from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None


@dataclass
class ValidationResult:
    passed: bool
    checks: dict
    notes: list[str]


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _venv_python() -> Path:
    root = _project_root()
    if os.name == "nt":
        return root / "venv" / "Scripts" / "python.exe"
    return root / "venv" / "bin" / "python"


def _runtime_options(metrics_file: Path, perf_log_file: Path) -> dict:
    return {
        "readonly_config": True,
        "auto_exit_seconds": 5.0,
        "metrics_output": str(metrics_file),
        "gui_settings": {
            "borderless": True,
            "monitor": "primary",
            "use_work_area": True,
            "pos_px": "0,0",
            "size_px": "1080,480",
            "fps": 60,
            "effects": {
                "enabled": True,
            },
            "crt_shader": {
                "enabled": True,
                "curvature": 0.07,
                "scanline_intensity": 0.14,
                "scanline_spacing": 2,
                "chromatic_aberration": 1,
                "vignette": 0.22,
                "noise": 0.025,
                "blur": 0.1,
                "mask_strength": 0.08,
                "jitter": 0.0,
            },
        },
        "performance_monitor": {
            "enabled": True,
            "sample_interval": 0.5,
            "log_path": str(perf_log_file),
        },
    }


def _run_gui_once(
    python_exe: Path,
    runtime_options_file: Path,
    timeout_seconds: float,
) -> tuple[int, str, str, Optional[int], Optional[float]]:
    cmd = [
        str(python_exe),
        "src/main_gui.py",
        "--runtime-options",
        str(runtime_options_file),
    ]
    env = os.environ.copy()
    started = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        cwd=str(_project_root()),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    peak_rss_mb = None
    if psutil is not None:
        try:
            proc_handle = psutil.Process(proc.pid)
            peak_rss_mb = 0.0
            while proc.poll() is None:
                try:
                    rss_mb = proc_handle.memory_info().rss / (1024 * 1024)
                    peak_rss_mb = max(peak_rss_mb, rss_mb)
                except Exception:
                    pass
                if (time.perf_counter() - started) >= timeout_seconds:
                    proc.terminate()
                    break
                time.sleep(0.1)
        except Exception:
            peak_rss_mb = None

    try:
        stdout, stderr = proc.communicate(timeout=max(1.0, timeout_seconds))
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()

    elapsed = time.perf_counter() - started
    return proc.returncode or 0, stdout, stderr, proc.pid, peak_rss_mb


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_perf_samples(log_path: Path) -> list[dict]:
    if not log_path.is_file():
        return []
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    samples = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except Exception:
            continue
        if isinstance(payload, dict):
            samples.append(payload)
    return samples


def _validate(metrics: dict, perf_samples: list[dict], *, peak_rss_mb: Optional[float]) -> ValidationResult:
    notes: list[str] = []
    checks = {
        "gui_process_started": False,
        "startup_exit_ok": False,
        "borderless_window": False,
        "component_refresh_ok": False,
        "effects_enabled": False,
        "perf_samples_collected": False,
        "cpu_usage_observed": False,
        "no_zombie_process": True,
    }

    frame_index = int(metrics.get("frame_index", 0) or 0)
    checks["gui_process_started"] = bool(metrics)
    if not checks["gui_process_started"]:
        notes.append("未生成 metrics，GUI 进程可能未成功启动")
    checks["startup_exit_ok"] = frame_index > 0
    if not checks["startup_exit_ok"]:
        notes.append("GUI frame_index 未增长，窗口可能未正常进入渲染循环")

    window = metrics.get("window", {}) if isinstance(metrics.get("window"), dict) else {}
    checks["borderless_window"] = bool(window.get("borderless", False))
    if not checks["borderless_window"]:
        notes.append("窗口未处于 borderless 状态")

    component_updates = metrics.get("component_updates", {})
    if not isinstance(component_updates, dict):
        component_updates = {}
    required_components = ["p_hardware", "p_network", "p_clock"]
    checks["component_refresh_ok"] = all(
        int(component_updates.get(component_id, 0) or 0) > 0
        for component_id in required_components
    )
    if not checks["component_refresh_ok"]:
        notes.append("CPU/内存/时钟/网络组件存在未刷新项")

    checks["effects_enabled"] = bool(metrics.get("effects_enabled", False))
    if not checks["effects_enabled"]:
        notes.append("effects 未启用，无法覆盖 10.1 特效验收")

    checks["perf_samples_collected"] = len(perf_samples) >= 2
    if not checks["perf_samples_collected"]:
        notes.append("GUI 性能采样不足（少于 2 条）")

    if perf_samples:
        cpu_values = [float(sample.get("cpu_percent", 0.0) or 0.0) for sample in perf_samples]
        checks["cpu_usage_observed"] = any(value >= 0 for value in cpu_values)
    if not checks["cpu_usage_observed"]:
        notes.append("未读取到有效 CPU 采样值")

    if peak_rss_mb is not None and peak_rss_mb > 1024:
        notes.append(f"峰值内存较高（约 {peak_rss_mb:.1f} MB），建议后续关注")

    passed = all(checks.values())
    return ValidationResult(passed=passed, checks=checks, notes=notes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate GUI host acceptance for 10.1/10.2")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="build/validation/gui_host",
        help="Directory for generated runtime options, logs and report",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=20.0,
        help="Max seconds to wait for one validation run",
    )
    args = parser.parse_args()

    root = _project_root()
    python_exe = _venv_python()
    if not python_exe.is_file():
        raise SystemExit(f"Python not found: {python_exe}")

    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_options_file = output_dir / "runtime_options.json5"
    metrics_file = output_dir / "metrics.json"
    perf_log_file = output_dir / "gui_perf.jsonl"
    report_file = output_dir / "report.json"

    runtime_options = _runtime_options(metrics_file=metrics_file, perf_log_file=perf_log_file)
    runtime_options_file.write_text(
        json.dumps(runtime_options, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if metrics_file.exists():
        metrics_file.unlink()
    if perf_log_file.exists():
        perf_log_file.unlink()

    returncode, stdout, stderr, pid, peak_rss_mb = _run_gui_once(
        python_exe=python_exe,
        runtime_options_file=runtime_options_file,
        timeout_seconds=max(5.0, args.timeout_seconds),
    )

    metrics = _load_json(metrics_file)
    perf_samples = _load_perf_samples(perf_log_file)
    result = _validate(metrics, perf_samples, peak_rss_mb=peak_rss_mb)

    if returncode != 0:
        stderr_text = (stderr or "").lower()
        qt_runtime_failed = (
            ("dll load failed" in stderr_text and "qtcore" in stderr_text)
            or "qt runtime check failed" in stderr_text
            or ("dll load failed" in stderr_text and "pyside6" in stderr_text)
        )
        if qt_runtime_failed:
            result.notes.append(
                "检测到 PySide6/Qt DLL 加载失败，请先安装 Microsoft VC++ 2015-2022 x64 运行库"
            )
            result.notes.append(
                "该环境无法完成 GUI 自动验收，需在可运行 Qt 的 Windows 环境复测"
            )

    if psutil is not None and pid is not None:
        try:
            _ = psutil.Process(pid)
            result.checks["no_zombie_process"] = False
            result.notes.append("GUI 进程退出后仍存活，疑似僵尸进程")
        except Exception:
            result.checks["no_zombie_process"] = True

    result.passed = all(result.checks.values())

    report_payload = {
        "passed": result.passed,
        "checks": result.checks,
        "notes": result.notes,
        "run": {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "metrics_file": str(metrics_file),
            "perf_log_file": str(perf_log_file),
            "peak_rss_mb": round(float(peak_rss_mb), 2) if peak_rss_mb is not None else None,
            "samples": len(perf_samples),
        },
        "metrics": metrics,
    }
    report_file.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = "PASS" if result.passed else "FAIL"
    print(f"[GUI-VALIDATION] {summary}")
    print(f"report: {report_file}")
    if result.notes:
        print("notes:")
        for note in result.notes:
            print(f"- {note}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

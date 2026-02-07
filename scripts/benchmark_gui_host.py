from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Scenario:
    name: str
    width: int
    height: int
    fps: int


SCENARIOS = [
    Scenario(name="1080x480", width=1080, height=480, fps=60),
    Scenario(name="1920x480", width=1920, height=480, fps=60),
]


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _venv_python() -> Path:
    root = _project_root()
    if os.name == "nt":
        return root / "venv" / "Scripts" / "python.exe"
    return root / "venv" / "bin" / "python"


def _runtime_payload(scenario: Scenario, metrics_file: Path, perf_log_file: Path, *, run_seconds: float) -> dict:
    return {
        "readonly_config": True,
        "auto_exit_seconds": run_seconds,
        "metrics_output": str(metrics_file),
        "gui_settings": {
            "borderless": True,
            "monitor": "primary",
            "use_work_area": True,
            "pos_px": "0,0",
            "size_px": f"{scenario.width},{scenario.height}",
            "fps": scenario.fps,
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


def _run_once(python_exe: Path, runtime_options_file: Path, *, timeout: float) -> tuple[int, str, str]:
    cmd = [
        str(python_exe),
        "src/main_gui.py",
        "--runtime-options",
        str(runtime_options_file),
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(_project_root()),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=max(10.0, timeout),
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _is_qt_runtime_error(returncode: int, stderr: str) -> bool:
    if returncode == 0:
        return False
    text = (stderr or "").lower()
    return (
        "qt runtime check failed" in text
        or ("dll load failed" in text and "qtcore" in text)
        or ("dll load failed" in text and "pyside6" in text)
    )


def _read_perf_samples(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    samples: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
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


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * 0.95))
    return ordered[max(0, min(idx, len(ordered) - 1))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark GUI host performance for 10.2")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="build/validation/gui_host_perf",
        help="Directory for benchmark artifacts",
    )
    parser.add_argument(
        "--run-seconds",
        type=float,
        default=8.0,
        help="Seconds per benchmark scenario",
    )
    args = parser.parse_args()

    root = _project_root()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    python_exe = _venv_python()
    if not python_exe.is_file():
        raise SystemExit(f"Python not found: {python_exe}")

    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "scenarios": [],
        "summary": {
            "pass": True,
            "targets": {
                "min_avg_fps": 20,
                "max_avg_cpu_percent": 85,
            },
        },
    }

    for scenario in SCENARIOS:
        scenario_dir = output_dir / scenario.name
        scenario_dir.mkdir(parents=True, exist_ok=True)
        runtime_options_file = scenario_dir / "runtime_options.json5"
        metrics_file = scenario_dir / "metrics.json"
        perf_log_file = scenario_dir / "gui_perf.jsonl"

        payload = _runtime_payload(
            scenario,
            metrics_file=metrics_file,
            perf_log_file=perf_log_file,
            run_seconds=max(4.0, float(args.run_seconds)),
        )
        runtime_options_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if perf_log_file.exists():
            perf_log_file.unlink()

        returncode, stdout, stderr = _run_once(
            python_exe,
            runtime_options_file,
            timeout=max(20.0, args.run_seconds + 10.0),
        )
        samples = _read_perf_samples(perf_log_file)
        fps_values = [float(item.get("fps", 0.0) or 0.0) for item in samples]
        cpu_values = [float(item.get("cpu_percent", 0.0) or 0.0) for item in samples]
        mem_values = [float(item.get("memory_mb", 0.0) or 0.0) for item in samples]
        frame_time_values = [float(item.get("frame_time_ms", 0.0) or 0.0) for item in samples]

        avg_fps = _avg(fps_values)
        avg_cpu = _avg(cpu_values)
        avg_mem = _avg(mem_values)
        p95_frame_time = _p95(frame_time_values)

        qt_runtime_error = _is_qt_runtime_error(returncode, stderr)
        scenario_pass = bool(returncode == 0 and samples and avg_fps >= 20 and avg_cpu <= 85)
        report["summary"]["pass"] = bool(report["summary"]["pass"] and scenario_pass)

        report["scenarios"].append(
            {
                "name": scenario.name,
                "resolution": f"{scenario.width}x{scenario.height}",
                "target_fps": scenario.fps,
                "returncode": returncode,
                "samples": len(samples),
                "avg_fps": round(avg_fps, 2),
                "avg_cpu_percent": round(avg_cpu, 2),
                "avg_memory_mb": round(avg_mem, 2),
                "p95_frame_time_ms": round(p95_frame_time, 3),
                "pass": scenario_pass,
                "qt_runtime_error": qt_runtime_error,
                "stdout": stdout,
                "stderr": stderr,
                "artifacts": {
                    "runtime_options": str(runtime_options_file),
                    "metrics": str(metrics_file),
                    "perf_log": str(perf_log_file),
                },
            }
        )

    report_file = output_dir / "benchmark_report.json"
    report_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if any(bool(item.get("qt_runtime_error", False)) for item in report["scenarios"]):
        report["summary"]["qt_runtime_available"] = False
        report["summary"]["pass"] = False
        report["summary"]["note"] = (
            "检测到 PySide6/Qt DLL 加载失败，当前环境无法完成 GUI 性能基准。"
        )
        report_file.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print("[GUI-BENCHMARK] PASS" if report["summary"]["pass"] else "[GUI-BENCHMARK] FAIL")
    print(f"report: {report_file}")
    for scenario in report["scenarios"]:
        print(
            f"- {scenario['name']}: "
            f"avg_fps={scenario['avg_fps']}, "
            f"avg_cpu={scenario['avg_cpu_percent']}%, "
            f"samples={scenario['samples']}, "
            f"pass={scenario['pass']}"
        )

    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

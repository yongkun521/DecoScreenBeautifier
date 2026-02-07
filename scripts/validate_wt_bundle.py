from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from utils import terminal_launcher


@dataclass
class SmokeResult:
    mode: str
    scenario: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_output_dir() -> Path:
    return PROJECT_ROOT / "build" / "validation" / "wt_bundle"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _resolve_terminal_defaults() -> dict[str, Any]:
    from config.manager import ConfigManager

    cfg = ConfigManager()
    cfg.load_settings()
    section = cfg.settings.get("terminal_integration")
    if isinstance(section, dict):
        return dict(section)
    return {}


def _bundled_wt_candidates(terminal_settings: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    configured = terminal_launcher._normalize_bundled_wt_path(
        terminal_settings.get("bundled_wt_path")
    )
    if configured is not None:
        candidates.append(str(configured.resolve()))
    root = terminal_launcher._application_root()
    for rel in terminal_launcher.BUNDLED_WT_RELATIVE_CANDIDATES:
        candidates.append(str((root / rel).resolve()))
    unique: list[str] = []
    seen: set[str] = set()
    for path_text in candidates:
        if path_text in seen:
            continue
        seen.add(path_text)
        unique.append(path_text)
    return unique


def _profile_check(terminal_settings: dict[str, Any], bundled_wt_exe: str | None) -> dict[str, Any]:
    profile_name = terminal_launcher._resolve_bundled_wt_profile_name(terminal_settings)
    result: dict[str, Any] = {
        "requested_profile": profile_name,
        "settings_path": "",
        "settings_exists": False,
        "profile_found": False,
        "retro_flag_present": False,
        "pixel_shader_flag_present": False,
    }

    if not bundled_wt_exe:
        return result

    settings_path = terminal_launcher._resolve_bundled_wt_settings_path(
        bundled_wt_exe,
        terminal_settings,
    )
    result["settings_path"] = str(settings_path)
    result["settings_exists"] = settings_path.is_file()
    if not settings_path.is_file():
        return result

    doc = _load_json(settings_path)
    profiles = doc.get("profiles") if isinstance(doc.get("profiles"), dict) else {}
    profile_list = profiles.get("list") if isinstance(profiles.get("list"), list) else []
    for item in profile_list:
        if not isinstance(item, dict):
            continue
        if str(item.get("name") or "").strip() != profile_name:
            continue
        result["profile_found"] = True
        result["retro_flag_present"] = (
            "experimental.retroTerminalEffect" in item
            or "retroTerminalEffect" in item
        )
        result["pixel_shader_flag_present"] = (
            "experimental.pixelShaderPath" in item
            or "pixelShaderPath" in item
        )
        break
    return result


def _smoke_command(mode: str, scenario: str) -> list[str]:
    cmd = ["wt", "--window", "new"]
    if mode == "fullscreen":
        cmd.append("--fullscreen")
    else:
        cmd.append("--focus")
    if scenario:
        cmd.extend(["--size", scenario])
    cmd.extend(["new-tab", "cmd", "/c", "exit"])
    return cmd


def _run_smoke(mode: str, scenario: str) -> SmokeResult:
    cmd = _smoke_command(mode, scenario)
    proc = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return SmokeResult(
        mode=mode,
        scenario=scenario,
        command=cmd,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def _write_smoke_text(output_dir: Path, smoke: SmokeResult) -> None:
    scenario_tag = smoke.scenario.replace(",", "x") if smoke.scenario else "default"
    target = output_dir / f"wt_bundle_smoke_{smoke.mode}_{scenario_tag}.txt"
    lines = [
        f"mode: {smoke.mode}",
        f"scenario: {smoke.scenario}",
        f"ok: {smoke.ok}",
        f"returncode: {smoke.returncode}",
        f"command: {' '.join(smoke.command)}",
        "--- stdout ---",
        smoke.stdout.rstrip(),
        "--- stderr ---",
        smoke.stderr.rstrip(),
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")


def _snapshot_portable_settings(
    output_dir: Path,
    terminal_settings: dict[str, Any],
    bundled_wt_exe: str | None,
) -> str:
    if not bundled_wt_exe:
        return ""
    settings_path = terminal_launcher._resolve_bundled_wt_settings_path(
        bundled_wt_exe,
        terminal_settings,
    )
    if not settings_path.is_file():
        return ""
    target = output_dir / "portable_settings_snapshot.json"
    content = settings_path.read_text(encoding="utf-8", errors="replace")
    target.write_text(content, encoding="utf-8")
    return str(target)


def _make_assessment(report: dict[str, Any]) -> dict[str, Any]:
    bundled_found = bool(report.get("bundled_wt", {}).get("available"))
    system_found = bool(report.get("system_wt", {}).get("available"))
    fallback_ok = bool(report.get("fallback", {}).get("to_system_when_bundled_missing"))
    profile_ok = bool(report.get("portable_profile", {}).get("profile_found"))

    recommendation = "维持"
    if bundled_found and profile_ok:
        recommendation = "继续"
    elif not bundled_found and system_found:
        recommendation = "维持"
    else:
        recommendation = "收缩"

    return {
        "recommendation": recommendation,
        "reasoning": {
            "bundled_wt_available": bundled_found,
            "system_wt_available": system_found,
            "fallback_path_ok": fallback_ok,
            "portable_profile_ready": profile_ok,
        },
    }


def _check_packaging_tiers() -> dict[str, Any]:
    script_exe = PROJECT_ROOT / "scripts" / "build_exe.ps1"
    script_portable = PROJECT_ROOT / "scripts" / "build_portable.ps1"
    text_exe = script_exe.read_text(encoding="utf-8", errors="replace")
    text_portable = script_portable.read_text(encoding="utf-8", errors="replace")
    return {
        "build_exe_has_include_switch": "IncludeBundledWT" in text_exe,
        "build_portable_has_include_switch": "IncludeBundledWT" in text_portable,
        "build_exe_default_standard": "if ($IncludeBundledWT)" in text_exe,
        "build_portable_default_standard": "if ($IncludeBundledWT)" in text_portable,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate bundled Windows Terminal route (M3/M4 acceptance)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(_default_output_dir()),
        help="Directory for generated validation artifacts",
    )
    parser.add_argument(
        "--with-smoke-run",
        action="store_true",
        help="Run wt smoke command for focus/fullscreen modes",
    )
    parser.add_argument(
        "--mode",
        action="append",
        choices=["focus", "fullscreen"],
        help="Smoke modes to run (default: both when --with-smoke-run)",
    )
    parser.add_argument(
        "--scenario-size",
        action="append",
        help="Smoke scenario size string passed to wt --size (default: 1080,480 and 1920,480)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    terminal_settings = _resolve_terminal_defaults()
    terminal_settings["enabled"] = True
    terminal_settings["backend"] = "windows_terminal"

    bundled_wt_exe = terminal_launcher._find_bundled_wt_executable(terminal_settings)
    system_wt_exe = terminal_launcher._find_system_wt_executable()
    selected_wt_exe, selected_is_bundled = terminal_launcher._select_wt_executable(
        terminal_settings
    )

    if bundled_wt_exe:
        terminal_launcher._ensure_wt_portable_mode(
            bundled_wt_exe,
            terminal_settings,
            use_bundled=True,
        )
        terminal_launcher._ensure_bundled_wt_profile(bundled_wt_exe, terminal_settings)

    profile_state = _profile_check(terminal_settings, bundled_wt_exe)
    snapshot_path = _snapshot_portable_settings(output_dir, terminal_settings, bundled_wt_exe)

    report: dict[str, Any] = {
        "generated_at_utc": _utc_now(),
        "project_root": str(PROJECT_ROOT),
        "packaging_tiers": _check_packaging_tiers(),
        "bundled_wt": {
            "available": bool(bundled_wt_exe),
            "path": bundled_wt_exe or "",
            "candidates": _bundled_wt_candidates(terminal_settings),
        },
        "system_wt": {
            "available": bool(system_wt_exe),
            "path": system_wt_exe or "",
            "on_path": bool(shutil.which("wt")),
        },
        "selection": {
            "selected_path": selected_wt_exe or "",
            "selected_is_bundled": bool(selected_is_bundled),
        },
        "fallback": {
            "to_system_when_bundled_missing": bool(system_wt_exe),
            "to_classic_when_all_missing": not bool(system_wt_exe),
        },
        "portable_profile": profile_state,
        "portable_settings_snapshot": snapshot_path,
        "validation_scenarios": [],
        "smoke_runs": [],
    }

    if args.with_smoke_run:
        modes = args.mode or ["focus", "fullscreen"]
        scenarios = args.scenario_size or ["1080,480", "1920,480"]
        report["validation_scenarios"] = scenarios
        smoke_items: list[dict[str, Any]] = []
        for mode in modes:
            for scenario in scenarios:
                smoke = _run_smoke(mode, scenario)
                _write_smoke_text(output_dir, smoke)
                smoke_items.append(
                    {
                        "mode": smoke.mode,
                        "scenario": smoke.scenario,
                        "ok": smoke.ok,
                        "returncode": smoke.returncode,
                        "command": smoke.command,
                    }
                )
        report["smoke_runs"] = smoke_items

    report["route_assessment"] = _make_assessment(report)

    report_path = output_dir / "wt_bundle_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"[WT-VALIDATE] Report: {report_path}")
    if report["smoke_runs"]:
        smoke_ok = all(item["ok"] for item in report["smoke_runs"])
        print(f"[WT-VALIDATE] Smoke runs ok: {smoke_ok}")

    assessment = report["route_assessment"]
    print(f"[WT-VALIDATE] Recommendation: {assessment['recommendation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

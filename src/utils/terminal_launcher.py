from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

DEFAULT_WT_TITLE = "DecoScreenBeautifier"
DEFAULT_WINDOW_TARGET = "new"


def _is_windows() -> bool:
    return os.name == "nt"


def _in_windows_terminal() -> bool:
    return bool(os.environ.get("WT_SESSION"))


def _find_wt_executable() -> Optional[str]:
    path = shutil.which("wt")
    if path:
        return path
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidate = Path(local_appdata) / "Microsoft" / "WindowsApps" / "wt.exe"
        if candidate.is_file():
            return str(candidate)
    return None


def _normalize_settings(settings: Any) -> dict:
    if isinstance(settings, dict):
        return settings
    return {}


def _build_app_command(argv: Iterable[str]) -> list[str]:
    argv_list = list(argv)
    if not argv_list:
        return [sys.executable]
    script_candidate = Path(argv_list[0])
    if script_candidate.suffix.lower() in {".py", ".pyw"}:
        script_path = str(script_candidate.resolve())
        return [sys.executable, script_path] + argv_list[1:]
    return [sys.executable] + argv_list[1:]


def _build_wt_command(
    wt_exe: str, terminal_settings: Mapping[str, Any], argv: Iterable[str]
) -> list[str]:
    settings = _normalize_settings(terminal_settings)
    args = [wt_exe]

    window_target = settings.get("window_target") or DEFAULT_WINDOW_TARGET
    if window_target:
        args += ["--window", str(window_target)]

    if settings.get("focus_mode"):
        args.append("--focus")
    if settings.get("fullscreen"):
        args.append("--fullscreen")
    if settings.get("maximized"):
        args.append("--maximized")

    position = settings.get("position")
    if position:
        args += ["--pos", str(position)]
    size = settings.get("size")
    if size:
        args += ["--size", str(size)]

    args.append("new-tab")

    profile = settings.get("profile")
    if profile:
        args += ["--profile", str(profile)]

    title = settings.get("title") or DEFAULT_WT_TITLE
    if title:
        args += ["--title", str(title)]

    starting_directory = settings.get("starting_directory")
    if starting_directory:
        args += ["--startingDirectory", str(starting_directory)]

    args += _build_app_command(argv)
    return args


def maybe_launch_in_windows_terminal(
    settings: Mapping[str, Any], argv: Iterable[str]
) -> bool:
    if not _is_windows():
        return False
    if _in_windows_terminal():
        return False
    if os.environ.get("DSB_DISABLE_WT"):
        return False

    terminal_settings = _normalize_settings(settings.get("terminal_integration"))
    if not terminal_settings or not terminal_settings.get("enabled"):
        return False
    if terminal_settings.get("backend", "windows_terminal") != "windows_terminal":
        return False

    wt_exe = _find_wt_executable()
    if not wt_exe:
        sys.stderr.write(
            "Windows Terminal not found; continuing in current console.\n"
        )
        return False

    args = _build_wt_command(wt_exe, terminal_settings, argv)
    try:
        subprocess.Popen(args)
    except OSError as exc:
        sys.stderr.write(f"Failed to launch Windows Terminal: {exc}\n")
        return False
    return True

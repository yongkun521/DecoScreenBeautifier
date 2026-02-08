from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

STARTUP_TRACE_LOG_NAME = "legacy_terminal_startup_trace.log"
ERROR_LOG_NAME = "legacy_terminal_error.log"


def _application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _trace_log_candidates() -> list[Path]:
    candidates: list[Path] = []
    candidates.append(_application_root() / STARTUP_TRACE_LOG_NAME)

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidates.append(
            Path(local_appdata)
            / "DecoTeam"
            / "DecoScreenBeautifier"
            / STARTUP_TRACE_LOG_NAME
        )

    normalized: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        normalized.append(Path(key))
    return normalized


def trace_startup(message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"[{timestamp}] {message}"

    for log_path in _trace_log_candidates():
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(line)
                f.write("\n")
            break
        except Exception:
            continue

    try:
        fallback = Path(tempfile.gettempdir()) / STARTUP_TRACE_LOG_NAME
        with fallback.open("a", encoding="utf-8") as f:
            f.write(line)
            f.write("\n")
    except Exception:
        pass

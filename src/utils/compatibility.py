from __future__ import annotations

import os
import platform
import sys
from typing import Any, Optional

if os.name == "nt":
    import ctypes
    from ctypes import wintypes


def _get_system_dpi() -> Optional[int]:
    if os.name != "nt":
        return None
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    try:
        get_dpi_for_system = user32.GetDpiForSystem
    except AttributeError:
        get_dpi_for_system = None
    if get_dpi_for_system:
        get_dpi_for_system.restype = wintypes.UINT
        dpi = int(get_dpi_for_system())
        if dpi > 0:
            return dpi
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    LOGPIXELSX = 88
    hdc = user32.GetDC(0)
    if not hdc:
        return None
    dpi = gdi32.GetDeviceCaps(hdc, LOGPIXELSX)
    user32.ReleaseDC(0, hdc)
    return int(dpi) if dpi else None


def _list_monitors() -> list[dict[str, Any]]:
    if os.name != "nt":
        return []
    try:
        from utils.deco_terminal import list_monitors
    except Exception:
        return []
    return list_monitors()


def collect_system_report() -> dict[str, Any]:
    dpi = _get_system_dpi()
    scale = None
    if dpi:
        scale = round(dpi / 96.0, 2)
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "os": {
            "name": os.name,
            "release": platform.release(),
            "version": platform.version(),
            "win32_ver": platform.win32_ver(),
        },
        "dpi": {
            "system_dpi": dpi,
            "scale": scale,
        },
        "monitors": _list_monitors(),
    }

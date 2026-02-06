from __future__ import annotations

import os
import sys
from typing import Any, Mapping, Optional, Tuple

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _user32 = ctypes.WinDLL("user32", use_last_error=True)

    _kernel32.GetConsoleWindow.restype = wintypes.HWND

    _user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    _user32.GetWindowLongW.restype = ctypes.c_long
    _user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
    _user32.SetWindowLongW.restype = ctypes.c_long
    _user32.SetWindowPos.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    _user32.SetWindowPos.restype = wintypes.BOOL

    GWL_STYLE = -16

    WS_CAPTION = 0x00C00000
    WS_THICKFRAME = 0x00040000
    WS_MINIMIZEBOX = 0x00020000
    WS_MAXIMIZEBOX = 0x00010000
    WS_SYSMENU = 0x00080000

    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020

    HWND_TOPMOST = wintypes.HWND(-1)
    HWND_NOTOPMOST = wintypes.HWND(-2)


def _normalize_settings(settings: Any) -> dict:
    if isinstance(settings, dict):
        return settings
    return {}


def _parse_pair(value: str) -> Optional[Tuple[int, int]]:
    if not value:
        return None
    if not isinstance(value, str):
        return None
    parts = [item.strip() for item in value.split(",")]
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def apply_deco_terminal_mode(terminal_settings: Mapping[str, Any]) -> bool:
    if os.name != "nt":
        return False
    if os.environ.get("WT_SESSION"):
        sys.stderr.write("Deco-terminal is not supported inside Windows Terminal.\n")
        return False

    settings = _normalize_settings(terminal_settings)
    if not settings:
        return False

    hwnd = _kernel32.GetConsoleWindow()
    if not hwnd:
        return False

    borderless = settings.get("deco_borderless", True)
    if borderless:
        style = _user32.GetWindowLongW(hwnd, GWL_STYLE)
        new_style = style & ~(
            WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU
        )
        if new_style != style:
            _user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)

    topmost = settings.get("deco_topmost")
    if topmost is not None:
        target = HWND_TOPMOST if topmost else HWND_NOTOPMOST
        _user32.SetWindowPos(
            hwnd,
            target,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED,
        )

    pos = _parse_pair(settings.get("deco_position", ""))
    size = _parse_pair(settings.get("deco_size", ""))
    if pos or size:
        x, y = pos if pos else (0, 0)
        width, height = size if size else (0, 0)
        flags = SWP_NOZORDER | SWP_FRAMECHANGED
        if not pos:
            flags |= SWP_NOMOVE
        if not size:
            flags |= SWP_NOSIZE
        _user32.SetWindowPos(hwnd, 0, x, y, width, height, flags)
    return True

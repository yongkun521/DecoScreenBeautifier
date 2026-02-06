from __future__ import annotations

import os
import sys
from dataclasses import dataclass
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
    _user32.GetForegroundWindow.argtypes = []
    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD
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
    _user32.EnumDisplayMonitors.argtypes = [
        wintypes.HDC,
        ctypes.POINTER(wintypes.RECT),
        ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.LPARAM,
        ),
        wintypes.LPARAM,
    ]
    _user32.EnumDisplayMonitors.restype = wintypes.BOOL
    _user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.c_void_p]
    _user32.GetMonitorInfoW.restype = wintypes.BOOL

    GWL_STYLE = -16
    GWL_EXSTYLE = -20

    WS_CAPTION = 0x00C00000
    WS_THICKFRAME = 0x00040000
    WS_MINIMIZEBOX = 0x00020000
    WS_MAXIMIZEBOX = 0x00010000
    WS_SYSMENU = 0x00080000
    WS_BORDER = 0x00800000
    WS_DLGFRAME = 0x00400000

    WS_EX_DLGMODALFRAME = 0x00000001
    WS_EX_WINDOWEDGE = 0x00000100
    WS_EX_CLIENTEDGE = 0x00000200
    WS_EX_STATICEDGE = 0x00020000

    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020

    HWND_TOPMOST = wintypes.HWND(-1)
    HWND_NOTOPMOST = wintypes.HWND(-2)

    MONITORINFOF_PRIMARY = 0x00000001

    class _MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", wintypes.RECT),
            ("rcWork", wintypes.RECT),
            ("dwFlags", wintypes.DWORD),
            ("szDevice", wintypes.WCHAR * 32),
        ]


@dataclass(frozen=True)
class _MonitorInfo:
    index: int
    handle: int
    left: int
    top: int
    right: int
    bottom: int
    work_left: int
    work_top: int
    work_right: int
    work_bottom: int
    is_primary: bool
    device: str

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def work_width(self) -> int:
        return self.work_right - self.work_left

    @property
    def work_height(self) -> int:
        return self.work_bottom - self.work_top


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


def _is_auto(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in {"auto", "screen", "monitor"}:
        return True
    return False


def _parse_monitor_index(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            try:
                return int(text)
            except ValueError:
                return None
    return None


def _list_monitors() -> list[_MonitorInfo]:
    if os.name != "nt":
        return []
    monitors: list[_MonitorInfo] = []

    def _callback(hmonitor, hdc, lprect, lparam) -> int:
        info = _MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(_MONITORINFOEXW)
        if not _user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            return 1
        monitors.append(
            _MonitorInfo(
                index=len(monitors),
                handle=int(hmonitor),
                left=info.rcMonitor.left,
                top=info.rcMonitor.top,
                right=info.rcMonitor.right,
                bottom=info.rcMonitor.bottom,
                work_left=info.rcWork.left,
                work_top=info.rcWork.top,
                work_right=info.rcWork.right,
                work_bottom=info.rcWork.bottom,
                is_primary=bool(info.dwFlags & MONITORINFOF_PRIMARY),
                device=info.szDevice,
            )
        )
        return 1

    callback = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(wintypes.RECT),
        wintypes.LPARAM,
    )(_callback)
    _user32.EnumDisplayMonitors(0, 0, callback, 0)
    return monitors


def list_monitors() -> list[dict[str, Any]]:
    """Expose monitor info for diagnostics/reporting."""
    monitors = _list_monitors()
    return [
        {
            "index": monitor.index,
            "device": monitor.device,
            "is_primary": monitor.is_primary,
            "bounds": [monitor.left, monitor.top, monitor.right, monitor.bottom],
            "work_area": [
                monitor.work_left,
                monitor.work_top,
                monitor.work_right,
                monitor.work_bottom,
            ],
            "size": [monitor.width, monitor.height],
            "work_size": [monitor.work_width, monitor.work_height],
        }
        for monitor in monitors
    ]


def _select_monitor(
    settings: Mapping[str, Any], monitors: list[_MonitorInfo]
) -> Optional[_MonitorInfo]:
    if not monitors:
        return None
    primary = next((m for m in monitors if m.is_primary), monitors[0])
    target = settings.get("deco_monitor")
    if target is None or target == "":
        target = "auto"
    if isinstance(target, str):
        target_value = target.strip().lower()
        if target_value in {"primary", "main"}:
            return primary
        if target_value in {"secondary", "second", "external"}:
            non_primary = [m for m in monitors if not m.is_primary]
            if non_primary:
                return max(non_primary, key=lambda m: m.width * m.height)
            return primary
        if target_value in {"auto"}:
            non_primary = [m for m in monitors if not m.is_primary]
            if non_primary:
                return max(non_primary, key=lambda m: m.width * m.height)
            return primary
        index = _parse_monitor_index(target_value)
        if index is not None and 0 <= index < len(monitors):
            return monitors[index]
    index = _parse_monitor_index(target)
    if index is not None and 0 <= index < len(monitors):
        return monitors[index]
    return primary


def _auto_monitor_rect(
    settings: Mapping[str, Any],
) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
    monitors = _list_monitors()
    monitor = _select_monitor(settings, monitors)
    if not monitor:
        return None
    use_work_area = bool(settings.get("deco_use_work_area"))
    if use_work_area:
        left, top, right, bottom = (
            monitor.work_left,
            monitor.work_top,
            monitor.work_right,
            monitor.work_bottom,
        )
    else:
        left, top, right, bottom = (
            monitor.left,
            monitor.top,
            monitor.right,
            monitor.bottom,
        )
    return (left, top), (right - left, bottom - top)


def _foreground_terminal_hwnd() -> Optional[int]:
    if os.name != "nt":
        return None
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return None
    try:
        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return None
        import psutil

        proc_name = psutil.Process(pid.value).name().lower()
    except Exception:
        return None
    if proc_name in {"windowsterminal.exe", "wt.exe"}:
        return int(hwnd)
    return None


def apply_deco_terminal_mode(terminal_settings: Mapping[str, Any]) -> bool:
    if os.name != "nt":
        return False

    settings = _normalize_settings(terminal_settings)
    if not settings:
        return False

    hwnd = _kernel32.GetConsoleWindow()
    if not hwnd:
        if os.environ.get("WT_SESSION"):
            hwnd = _foreground_terminal_hwnd()
        if not hwnd:
            sys.stderr.write("Deco-terminal is not supported inside Windows Terminal.\n")
            return False

    borderless = settings.get("deco_borderless", True)
    if borderless:
        style = _user32.GetWindowLongW(hwnd, GWL_STYLE)
        new_style = style & ~(
            WS_CAPTION
            | WS_THICKFRAME
            | WS_MINIMIZEBOX
            | WS_MAXIMIZEBOX
            | WS_SYSMENU
            | WS_BORDER
            | WS_DLGFRAME
        )
        if new_style != style:
            _user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)
        ex_style = _user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        new_ex_style = ex_style & ~(
            WS_EX_DLGMODALFRAME
            | WS_EX_WINDOWEDGE
            | WS_EX_CLIENTEDGE
            | WS_EX_STATICEDGE
        )
        if new_ex_style != ex_style:
            _user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_ex_style)

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

    raw_pos = settings.get("deco_position", "")
    raw_size = settings.get("deco_size", "")
    pos = None if _is_auto(raw_pos) else _parse_pair(raw_pos)
    size = None if _is_auto(raw_size) else _parse_pair(raw_size)
    auto_fit = settings.get("deco_auto_fit", True)
    if auto_fit and (pos is None or size is None):
        auto_rect = _auto_monitor_rect(settings)
        if auto_rect:
            auto_pos, auto_size = auto_rect
            if pos is None:
                pos = auto_pos
            if size is None:
                size = auto_size
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

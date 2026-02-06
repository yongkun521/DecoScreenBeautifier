from __future__ import annotations

from typing import Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QVBoxLayout, QWidget

from gui_host.input import action_from_key
from gui_host.surface import RenderSurface


class GuiMainWindow(QWidget):
    def __init__(self, settings: dict, action_handler=None) -> None:
        super().__init__()
        self._settings = settings or {}
        self._action_handler = action_handler
        self.surface = RenderSurface(self._settings, parent=self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.surface)
        self.setLayout(layout)

        self.setWindowTitle("DecoScreenBeautifier")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.apply_settings(self._settings)

    def apply_settings(self, settings: dict) -> None:
        self._settings = settings or {}
        flags = Qt.WindowType.Window
        if self._settings.get("borderless", True):
            flags |= Qt.WindowType.FramelessWindowHint
        if self._settings.get("always_on_top", False):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        screen = _select_screen(self._settings)
        if screen is not None:
            use_work_area = bool(self._settings.get("use_work_area", True))
            geometry = screen.availableGeometry() if use_work_area else screen.geometry()
            pos = _parse_pair(self._settings.get("pos_px"))
            size = _parse_pair(self._settings.get("size_px"))
            x = geometry.x() if pos is None else pos[0]
            y = geometry.y() if pos is None else pos[1]
            width = geometry.width() if size is None else size[0]
            height = geometry.height() if size is None else size[1]
            self.setGeometry(x, y, width, height)

        self.surface.update_settings(self._settings)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        action = action_from_key(event)
        if action:
            if self._action_handler:
                self._action_handler(action)
            event.accept()
            return
        super().keyPressEvent(event)


def _parse_pair(value: object) -> Optional[Tuple[int, int]]:
    if not value:
        return None
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        try:
            return int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.lower() in {"auto", ""}:
        return None
    parts = [item.strip() for item in text.split(",")]
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _select_screen(settings: dict):
    screens = QGuiApplication.screens()
    if not screens:
        return None
    primary = QGuiApplication.primaryScreen() or screens[0]
    target = settings.get("monitor", "auto")
    if target is None or target == "":
        target = "auto"
    if isinstance(target, str):
        key = target.strip().lower()
        if key in {"primary", "main"}:
            return primary
        if key in {"secondary", "second", "external", "auto"}:
            candidates = [screen for screen in screens if screen != primary]
            if candidates:
                return max(candidates, key=lambda s: s.size().width() * s.size().height())
            return primary
        if key.isdigit():
            try:
                idx = int(key)
                if 0 <= idx < len(screens):
                    return screens[idx]
            except ValueError:
                pass
    if isinstance(target, int):
        if 0 <= target < len(screens):
            return screens[target]
    return primary

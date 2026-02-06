import sys
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from config.manager import ConfigManager
from gui_host.scene import GuiScene
from gui_host.window import GuiMainWindow


class GuiHostApp:
    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("DecoScreenBeautifier")
        self.config_manager = ConfigManager()
        self.config_manager.load_settings()
        self.scene = GuiScene(self.config_manager)
        self.gui_settings = self.config_manager.settings.get("gui_host", {})
        if not isinstance(self.gui_settings, dict):
            self.gui_settings = {}

        self.window = GuiMainWindow(self.gui_settings, action_handler=self._handle_action)
        self.window.surface.update_settings(self.gui_settings, global_scale=self.scene.global_scale)
        self.window.show()

        self._frame_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        fps = _safe_int(self.gui_settings.get("fps"), 60)
        interval = max(1, int(1000 / max(1, fps)))
        self.timer.start(interval)

    def _tick(self) -> None:
        now = time.time()
        self.scene.update(now)
        self.window.surface.update_settings(self.gui_settings, global_scale=self.scene.global_scale)
        grid_w, grid_h = self.window.surface.grid_size()
        grid = self.scene.render(grid_w, grid_h, self._frame_index, now)
        self.window.surface.set_grid(grid)
        self._frame_index += 1

    def _handle_action(self, action: str) -> None:
        if action == "quit":
            self.app.quit()
            return
        if action in {"toggle_dark", "toggle_editor", "toggle_templates"}:
            # Placeholders for MVP
            return

    def run(self) -> int:
        return self.app.exec()


def _safe_int(value, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def run_gui() -> int:
    app = GuiHostApp()
    return app.run()

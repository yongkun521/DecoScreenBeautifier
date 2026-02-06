import sys
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog

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
        self._refresh_gui_settings()

        self.window = GuiMainWindow(
            self.gui_settings,
            action_handler=self._handle_action,
            geometry_handler=self._handle_geometry_update,
        )
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
        if action == "toggle_templates":
            self._open_templates_dialog()
            return
        if action == "toggle_settings":
            self._open_settings_dialog()
            return
        if action in {"toggle_dark", "toggle_editor"}:
            # Placeholders for MVP
            return

    def _open_templates_dialog(self) -> None:
        from gui_host.dialogs import TemplateDialog

        dialog = TemplateDialog(
            self.config_manager,
            current_id=str(self.config_manager.settings.get("template_id", "")),
            parent=self.window,
        )
        if dialog.exec() == QDialog.Accepted:
            template_id = dialog.selected_template_id()
            if template_id and self.scene.apply_template(template_id):
                self._refresh_gui_settings()
                self.window.surface.update_settings(
                    self.gui_settings, global_scale=self.scene.global_scale
                )

    def _open_settings_dialog(self) -> None:
        from gui_host.dialogs import SettingsDialog

        dialog = SettingsDialog(self.gui_settings, parent=self.window)
        if dialog.exec() != QDialog.Accepted:
            return
        payload = dialog.settings_payload()
        self._apply_gui_settings(payload)

    def _apply_gui_settings(self, payload: dict) -> None:
        self._refresh_gui_settings()
        monitor = payload.get("monitor") or "auto"
        old_monitor = str(self.gui_settings.get("monitor", "auto")).strip().lower()
        new_monitor = str(monitor).strip().lower()

        self.gui_settings["monitor"] = monitor
        self.gui_settings["use_work_area"] = bool(payload.get("use_work_area", True))
        self.gui_settings["always_on_top"] = bool(payload.get("always_on_top", False))
        if payload.get("font_face"):
            self.gui_settings["font_face"] = payload["font_face"]
        if payload.get("font_size"):
            self.gui_settings["font_size"] = int(payload["font_size"])

        effects = self.gui_settings.get("effects")
        if not isinstance(effects, dict):
            effects = {}
            self.gui_settings["effects"] = effects
        effects["enabled"] = bool(payload.get("effects_enabled", True))

        if new_monitor != old_monitor:
            self.gui_settings["pos_px"] = ""
            self.gui_settings["size_px"] = ""

        self.config_manager.settings["gui_host"] = self.gui_settings
        self.config_manager.save_settings()

        self.window.apply_settings(self.gui_settings)
        self.window.surface.update_settings(self.gui_settings, global_scale=self.scene.global_scale)
        self.window.show()
        self.scene.refresh_presets()

    def _handle_geometry_update(self, rect) -> None:
        if rect is None:
            return
        self._refresh_gui_settings()
        self.gui_settings["pos_px"] = f"{rect.x()},{rect.y()}"
        self.gui_settings["size_px"] = f"{rect.width()},{rect.height()}"
        self.config_manager.settings["gui_host"] = self.gui_settings
        self.config_manager.save_settings()

    def _refresh_gui_settings(self) -> None:
        gui_settings = self.config_manager.settings.get("gui_host", {})
        if not isinstance(gui_settings, dict):
            gui_settings = {}
            self.config_manager.settings["gui_host"] = gui_settings
        self.gui_settings = gui_settings

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

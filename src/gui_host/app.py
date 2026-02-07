import sys
import time
from pathlib import Path
from typing import Any, Mapping, Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog

from config.manager import ConfigManager
from gui_host.scene import GuiScene
from gui_host.window import GuiMainWindow
from utils.gui_perf_monitor import GuiPerformanceMonitor


class GuiHostApp:
    def __init__(self, runtime_options: Optional[dict] = None) -> None:
        self._runtime_options = runtime_options if isinstance(runtime_options, dict) else {}
        self._readonly_config = bool(self._runtime_options.get("readonly_config", False))
        self.performance_monitor: Optional[GuiPerformanceMonitor] = None
        self._auto_exit_timer: Optional[QTimer] = None
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("DecoScreenBeautifier")
        self.config_manager = ConfigManager()
        self.config_manager.load_settings()
        self._apply_runtime_overrides()
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

        self._start_performance_monitor()
        self.app.aboutToQuit.connect(self._shutdown)

        auto_exit_seconds = _safe_float(self._runtime_options.get("auto_exit_seconds"), 0.0)
        if auto_exit_seconds > 0:
            self._auto_exit_timer = QTimer(self.window)
            self._auto_exit_timer.setSingleShot(True)
            self._auto_exit_timer.timeout.connect(self.app.quit)
            self._auto_exit_timer.start(max(1, int(auto_exit_seconds * 1000)))

    def _tick(self) -> None:
        tick_started = time.perf_counter()
        now = time.time()
        self.scene.update(now)
        self.window.surface.update_settings(self.gui_settings, global_scale=self.scene.global_scale)
        grid_w, grid_h = self.window.surface.grid_size()
        grid = self.scene.render(grid_w, grid_h, self._frame_index, now)
        self.window.surface.set_frame_index(self._frame_index)
        self.window.surface.set_grid(grid)
        self._frame_index += 1
        tick_elapsed = time.perf_counter() - tick_started
        if self.performance_monitor is not None:
            sample = self.performance_monitor.record_frame(
                tick_elapsed,
                grid_width=grid_w,
                grid_height=grid_h,
            )
            if sample is not None:
                setattr(self, "performance_stats", sample)

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
        if action == "open_gui_editor":
            self._open_gui_editor_dialog()
            return
        if action == "toggle_editor":
            self._open_gui_editor_dialog()
            return
        if action == "toggle_dark":
            # Placeholder for MVP
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

    def _open_gui_editor_dialog(self) -> None:
        from gui_host.dialogs import GuiLayoutEditorDialog

        dialog = GuiLayoutEditorDialog(
            self.config_manager,
            template=self.scene.template,
            layout_data=self.scene.get_layout_data(),
            parent=self.window,
        )
        if dialog.exec() == QDialog.Accepted:
            self.scene.reload_layout()

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

        crt_shader = self.gui_settings.get("crt_shader")
        if not isinstance(crt_shader, dict):
            crt_shader = {}
            self.gui_settings["crt_shader"] = crt_shader
        crt_shader["enabled"] = bool(payload.get("crt_shader_enabled", False))

        if new_monitor != old_monitor:
            self.gui_settings["pos_px"] = ""
            self.gui_settings["size_px"] = ""

        self.config_manager.settings["gui_host"] = self.gui_settings
        self._save_settings_if_allowed()

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
        self._save_settings_if_allowed()

    def _refresh_gui_settings(self) -> None:
        gui_settings = self.config_manager.settings.get("gui_host", {})
        if not isinstance(gui_settings, dict):
            gui_settings = {}
            self.config_manager.settings["gui_host"] = gui_settings
        self.gui_settings = gui_settings

    def _apply_runtime_overrides(self) -> None:
        gui_overrides = self._runtime_options.get("gui_settings")
        if isinstance(gui_overrides, Mapping):
            gui_settings = self.config_manager.settings.get("gui_host")
            if not isinstance(gui_settings, dict):
                gui_settings = {}
                self.config_manager.settings["gui_host"] = gui_settings
            _merge_settings(gui_settings, gui_overrides)

        perf_overrides = self._runtime_options.get("performance_monitor")
        if isinstance(perf_overrides, Mapping):
            perf_settings = self.config_manager.settings.get("performance_monitor")
            if not isinstance(perf_settings, dict):
                perf_settings = {}
                self.config_manager.settings["performance_monitor"] = perf_settings
            _merge_settings(perf_settings, perf_overrides)

    def _start_performance_monitor(self) -> None:
        settings = self.config_manager.settings.get("performance_monitor", {})
        if not isinstance(settings, dict) or not settings.get("enabled"):
            return
        interval = settings.get("sample_interval", 1.0)
        log_path = settings.get("log_path")
        if log_path:
            log_path = self._resolve_perf_log_path(str(log_path))
        else:
            perf_dir = self.config_manager.data_dir / "perf"
            perf_dir.mkdir(parents=True, exist_ok=True)
            log_path = str(perf_dir / "gui_perf.jsonl")
        try:
            self.performance_monitor = GuiPerformanceMonitor(
                interval=interval,
                log_path=log_path,
            )
            self.performance_monitor.start()
        except Exception as exc:
            sys.stderr.write(f"Failed to start GUI performance monitor: {exc}\n")

    def _resolve_perf_log_path(self, log_path: str) -> str:
        path = Path(str(log_path)).expanduser()
        if not path.is_absolute():
            path = self.config_manager.data_dir / path
        return str(path.resolve())

    def _save_settings_if_allowed(self) -> None:
        if self._readonly_config:
            return
        self.config_manager.save_settings()

    def _shutdown(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
        if self._auto_exit_timer is not None and self._auto_exit_timer.isActive():
            self._auto_exit_timer.stop()
        if self.performance_monitor is not None:
            try:
                self.performance_monitor.stop()
            except Exception:
                pass
        self._write_metrics_output_if_requested()

    def snapshot_metrics(self) -> dict:
        return {
            "frame_index": int(self._frame_index),
            "grid": {
                "width": int(getattr(self.performance_monitor, "_latest_grid_width", 0))
                if self.performance_monitor is not None
                else 0,
                "height": int(getattr(self.performance_monitor, "_latest_grid_height", 0))
                if self.performance_monitor is not None
                else 0,
            },
            "component_updates": self.scene.component_update_counts(),
            "effects_enabled": bool(
                isinstance(self.gui_settings.get("effects"), dict)
                and self.gui_settings.get("effects", {}).get("enabled", False)
            ),
            "crt_shader_enabled": bool(
                isinstance(self.gui_settings.get("crt_shader"), dict)
                and self.gui_settings.get("crt_shader", {}).get("enabled", False)
            ),
            "window": {
                "x": int(self.window.x()),
                "y": int(self.window.y()),
                "width": int(self.window.width()),
                "height": int(self.window.height()),
                "borderless": bool(self.gui_settings.get("borderless", True)),
                "monitor": self.gui_settings.get("monitor", "auto"),
                "use_work_area": bool(self.gui_settings.get("use_work_area", True)),
            },
        }

    def _write_metrics_output_if_requested(self) -> None:
        metrics_output = self._runtime_options.get("metrics_output")
        if not metrics_output:
            return
        try:
            output_path = Path(str(metrics_output)).expanduser()
            if not output_path.is_absolute():
                output_path = (self.config_manager.data_dir / output_path).resolve()
            else:
                output_path = output_path.resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            payload = self.snapshot_metrics()
            payload["exit_timestamp"] = time.time()
            with output_path.open("w", encoding="utf-8") as handle:
                import json

                json.dump(payload, handle, ensure_ascii=False, indent=2)
        except Exception as exc:
            sys.stderr.write(f"Failed to write GUI metrics output: {exc}\n")

    def run(self) -> int:
        return self.app.exec()


def _safe_int(value, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _safe_float(value, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _merge_settings(target: dict, overrides: Mapping[str, Any]) -> None:
    for key, value in overrides.items():
        if isinstance(value, Mapping):
            existing = target.get(key)
            if not isinstance(existing, dict):
                existing = {}
                target[key] = existing
            _merge_settings(existing, value)
            continue
        target[key] = value


def run_gui(runtime_options: Optional[dict] = None) -> int:
    app = GuiHostApp(runtime_options=runtime_options)
    return app.run()

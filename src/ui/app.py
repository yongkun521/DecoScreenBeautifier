import sys
import os
import traceback
from pathlib import Path
from textual.app import App

# 导入主显示屏幕和编辑器屏幕
from ui.display import DisplayScreen
from ui.editor import EditorScreen
from ui.templates import TemplateScreen
from config.manager import ConfigManager
from core.presets import get_font_preset, get_style_preset

try:
    from utils.startup_trace import trace_startup as _trace_startup
except Exception:
    def _trace_startup(message: str) -> None:
        return None

class DecoScreenApp(App):
    """DecoScreenBeautifier 主应用程序"""

    # 加载外部 CSS 文件
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("e", "toggle_editor", "Open Editor"),
        ("t", "toggle_templates", "Open Templates"),
        ("b", "toggle_wt_border", "Toggle WT Border"),
        ("q", "quit", "Quit Application"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        self.display_screen = None
        self.visual_preset = get_font_preset(None)
        self.style_preset = get_style_preset(None)
        self.global_scale = 1.0
        self.performance_monitor = None

    def on_mount(self) -> None:
        """应用启动时挂载主屏幕"""
        _trace_startup("app.on_mount: enter")
        # 加载配置
        self.config_manager.load_settings()
        gui_host_settings = self.config_manager.settings.get("gui_host", {})
        terminal_settings = self.config_manager.settings.get("terminal_integration", {})
        _trace_startup(
            "app.on_mount: settings "
            f"template={self.config_manager.settings.get('template_id')} "
            f"gui_host.enabled={gui_host_settings.get('enabled') if isinstance(gui_host_settings, dict) else ''} "
            f"terminal.enabled={terminal_settings.get('enabled') if isinstance(terminal_settings, dict) else ''}"
        )
        self._refresh_visual_settings()
        self._start_performance_monitor()
        
        # 应用设置 (示例)
        # fps = self.config_manager.settings.get("fps_limit", 30)
        
        self.display_screen = DisplayScreen()
        self.push_screen(self.display_screen)
        _trace_startup("app.on_mount: display screen pushed")
        try:
            self.set_timer(2.0, self._trace_mount_health)
        except Exception:
            pass

    def _trace_mount_health(self) -> None:
        try:
            screen_name = type(self.screen).__name__
        except Exception:
            screen_name = "<unknown>"

        widget_count = -1
        display_screen_widget_count = -1
        screen_is_display = False
        app_screen_id = None
        display_screen_id = None
        try:
            app_screen_id = id(self.screen)
            widget_count = len(list(self.screen.query("*")))
        except Exception:
            pass
        try:
            if self.display_screen is not None:
                display_screen_id = id(self.display_screen)
                display_screen_widget_count = len(list(self.display_screen.query("*")))
                screen_is_display = self.screen is self.display_screen
        except Exception:
            pass

        _trace_startup(
            "app.mount_health: "
            f"active_screen={screen_name} "
            f"widget_count={widget_count} "
            f"display_widget_count={display_screen_widget_count} "
            f"screen_is_display={screen_is_display} "
            f"app_screen_id={app_screen_id} display_screen_id={display_screen_id}"
        )

    def _handle_exception(self, error: Exception) -> None:
        _trace_startup(
            f"app.handle_exception: {type(error).__name__}: {error}"
        )
        try:
            tb_text = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            for line in tb_text.splitlines():
                _trace_startup(f"app.traceback: {line}")
        except Exception:
            pass
        super()._handle_exception(error)

    def _start_performance_monitor(self) -> None:
        settings = self.config_manager.settings.get("performance_monitor", {})
        if not isinstance(settings, dict) or not settings.get("enabled"):
            return
        interval = settings.get("sample_interval", 1.0)
        log_path = settings.get("log_path")
        if log_path:
            log_path = self._resolve_perf_log_path(log_path)
        else:
            perf_dir = self.config_manager.data_dir / "perf"
            perf_dir.mkdir(parents=True, exist_ok=True)
            log_path = str(perf_dir / "perf.jsonl")
        try:
            from utils.perf_monitor import PerformanceMonitor
        except Exception as exc:
            sys.stderr.write(f"Performance monitor unavailable: {exc}\n")
            return
        try:
            self.performance_monitor = PerformanceMonitor(
                self, interval=interval, log_path=log_path
            )
            self.performance_monitor.start()
        except Exception as exc:
            sys.stderr.write(f"Failed to start performance monitor: {exc}\n")

    def _resolve_perf_log_path(self, log_path: str) -> str:
        path = Path(str(log_path)).expanduser()
        if not path.is_absolute():
            path = self.config_manager.data_dir / path
        return str(path.resolve())

    def on_shutdown(self) -> None:
        if self.performance_monitor:
            try:
                self.performance_monitor.stop()
            except Exception:
                pass

    def _refresh_visual_settings(self) -> None:
        self.visual_preset = get_font_preset(self.config_manager.settings.get("font_preset"))
        self.style_preset = get_style_preset(self.config_manager.settings.get("style_preset"))
        try:
            self.global_scale = float(self.config_manager.settings.get("global_scale", 1.0))
        except (TypeError, ValueError):
            self.global_scale = 1.0

    def action_toggle_dark(self) -> None:
        """切换暗黑模式 (Textual 内置支持)"""
        is_dark = self.has_class("-dark-mode") or self.theme == "textual-dark"
        self.theme = "textual-light" if is_dark else "textual-dark"

    def action_toggle_editor(self) -> None:
        """打开编辑器"""
        self.push_screen(EditorScreen())
        
    def action_toggle_templates(self) -> None:
        """打开模板库"""
        self.push_screen(TemplateScreen())

    def _terminal_settings(self) -> dict:
        settings = self.config_manager.settings.get("terminal_integration", {})
        if isinstance(settings, dict):
            return settings
        return {}

    def action_toggle_wt_border(self) -> None:
        terminal_settings = self._terminal_settings()
        backend = terminal_settings.get("backend", "windows_terminal")
        if backend != "windows_terminal":
            self.notify("Toggle border is only available in Windows Terminal mode.")
            return
        try:
            from utils.terminal_launcher import toggle_focus_mode_in_running_wt
        except Exception as exc:
            self.notify(f"Toggle border unavailable: {exc}")
            return

        ok, message = toggle_focus_mode_in_running_wt(terminal_settings)
        if ok:
            self.notify("Toggled border/focus mode. Drag now if needed.")
        else:
            self.notify(message)

    def apply_template(self, template_id: str) -> None:
        """应用模板并刷新当前显示"""
        template = self.config_manager.apply_template(template_id)
        self._refresh_visual_settings()
        if self.display_screen:
            self.display_screen.apply_template(template)

if __name__ == "__main__":
    app = DecoScreenApp()
    app.run()

import sys
import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

# 导入主显示屏幕和编辑器屏幕
from ui.display import DisplayScreen
from ui.editor import EditorScreen
from ui.templates import TemplateScreen
from config.manager import ConfigManager
from core.presets import get_font_preset, get_style_preset

class DecoScreenApp(App):
    """DecoScreenBeautifier 主应用程序"""

    # 加载外部 CSS 文件
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("e", "toggle_editor", "Open Editor"),
        ("t", "toggle_templates", "Open Templates"),
        ("q", "quit", "Quit Application"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        self.display_screen = None
        self.visual_preset = get_font_preset(None)
        self.style_preset = get_style_preset(None)
        self.global_scale = 1.0

    def on_mount(self) -> None:
        """应用启动时挂载主屏幕"""
        # 加载配置
        self.config_manager.load_settings()
        self._refresh_visual_settings()
        
        # 应用设置 (示例)
        # fps = self.config_manager.settings.get("fps_limit", 30)
        
        self.display_screen = DisplayScreen()
        self.push_screen(self.display_screen)

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

    def apply_template(self, template_id: str) -> None:
        """应用模板并刷新当前显示"""
        template = self.config_manager.apply_template(template_id)
        self._refresh_visual_settings()
        if self.display_screen:
            self.display_screen.apply_template(template)

if __name__ == "__main__":
    app = DecoScreenApp()
    app.run()

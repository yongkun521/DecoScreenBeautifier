import sys
import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

# 导入主显示屏幕和编辑器屏幕
from ui.display import DisplayScreen
from ui.editor import EditorScreen
from ui.templates import TemplateScreen
from config.manager import ConfigManager

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

    def on_mount(self) -> None:
        """应用启动时挂载主屏幕"""
        # 加载配置
        self.config_manager.load_settings()
        
        # 应用设置 (示例)
        # fps = self.config_manager.settings.get("fps_limit", 30)
        
        self.push_screen(DisplayScreen())

    def action_toggle_dark(self) -> None:
        """切换暗黑模式 (Textual 内置支持)"""
        self.dark = not self.dark

    def action_toggle_editor(self) -> None:
        """打开编辑器"""
        self.push_screen(EditorScreen())
        
    def action_toggle_templates(self) -> None:
        """打开模板库"""
        self.push_screen(TemplateScreen())

if __name__ == "__main__":
    app = DecoScreenApp()
    app.run()

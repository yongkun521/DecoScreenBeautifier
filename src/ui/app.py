from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

class DecoScreenApp(App):
    """DecoScreenBeautifier 主应用程序"""

    CSS = """
    Screen {
        background: #0D0208;
        color: #00FF41;
    }
    
    Static {
        content-align: center middle;
        text-style: bold;
        color: #FF00FF;
    }
    """

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """创建子组件"""
        yield Header()
        yield Static("DecoScreenBeautifier\nCyberpunk CLI Visualizer Initialized...")
        yield Footer()

    def action_toggle_dark(self) -> None:
        """切换暗黑模式"""
        self.dark = not self.dark

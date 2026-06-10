from rich.align import Align
from rich.console import Group
from rich.text import Text

from .base import BaseWidget


class HudDecorWidget(BaseWidget):
    """
    HUD 标尺/准星装饰组件。
    """

    DEFAULT_CSS = """
    HudDecorWidget {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(title="HUD DECOR", update_interval=0.5, **kwargs)
        self._phase = 0

    def update_content(self) -> None:
        width, height = self.get_content_size(default=(48, 7))
        width = max(16, width)
        height = max(5, height)
        mid_row = height // 2
        mid_col = width // 2
        line = self.get_style_color("line", self.get_style_color("secondary", "#00FFFF"))
        dim = self.get_style_color("line_dim", self.get_style_color("muted", "#335555"))
        accent = self.get_style_color("accent", "#FFD700")

        rows = []
        for row in range(height):
            text = Text()
            for col in range(width):
                char = " "
                style = dim
                if row in {0, height - 1} and col in {0, width - 1}:
                    char = "◆"
                    style = accent
                elif row in {0, height - 1} and col % 4 == self._phase % 4:
                    char = "═"
                    style = line
                elif col in {0, width - 1} and row % 2 == 0:
                    char = "║"
                    style = line
                elif row == mid_row and abs(col - mid_col) > 1:
                    char = "─" if col % 3 else "╴"
                    style = dim
                elif col == mid_col and abs(row - mid_row) > 1:
                    char = "│"
                    style = dim
                elif row == mid_row and col == mid_col:
                    char = "◇"
                    style = accent
                elif row == mid_row and abs(col - mid_col) == 1:
                    char = "─"
                    style = accent
                elif col == mid_col and abs(row - mid_row) == 1:
                    char = "│"
                    style = accent
                text.append(char, style=style)
            rows.append(text)

        self._phase = (self._phase + 1) % 4
        content = Group(*rows)
        if self.uses_light_chrome():
            self.update(self.compose_widget_content(content, footer="scan alignment"))
            return
        self.update(Align.center(content, vertical="middle"))

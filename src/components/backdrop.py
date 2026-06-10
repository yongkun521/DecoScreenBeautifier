import random

from rich.align import Align
from rich.console import Group
from rich.text import Text

from .base import BaseWidget


class BackdropPatternWidget(BaseWidget):
    """
    低对比点阵背景组件。
    """

    DEFAULT_CSS = """
    BackdropPatternWidget {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(title="BACKDROP MATRIX", update_interval=0.35, **kwargs)
        self._phase = 0

    def update_content(self) -> None:
        width, height = self.get_content_size(default=(48, 8))
        width = max(8, width)
        height = max(3, height)
        dim = self.get_style_color("line_dim", self.get_style_color("muted", "#335555"))
        accent = self.get_style_color("accent", "#FFD700")
        primary = self.get_style_color("primary", "#00FF41")

        lines = []
        for row in range(height):
            text = Text()
            for col in range(width):
                value = (row * 7 + col * 11 + self._phase) % 29
                if value == 0:
                    text.append("◆", style=accent)
                elif value in {3, 13}:
                    text.append("·", style=primary)
                elif random.random() < 0.018:
                    text.append("•", style=accent)
                else:
                    text.append("·", style=dim)
            lines.append(text)

        self._phase = (self._phase + 1) % 29
        content = Group(*lines)
        if self.uses_light_chrome():
            self.update(self.compose_widget_content(content, footer="low signal field"))
            return
        self.update(Align.center(content, vertical="middle"))

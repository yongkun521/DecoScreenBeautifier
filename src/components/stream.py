import random

from rich.align import Align
from rich.console import Group
from rich.text import Text

from .base import BaseWidget


class DataStreamWidget(BaseWidget):
    """
    信号流动装饰组件
    """

    DEFAULT_CSS = """
    DataStreamWidget {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(title="SIGNAL STREAM", update_interval=0.2, **kwargs)
        self._buffer = []
        self._last_size = (0, 0)

    def update_content(self) -> None:
        width = max(1, self.size.width - 2)
        height = max(1, self.size.height - 2)
        if width <= 0 or height <= 0:
            return
        if (width, height) != self._last_size or len(self._buffer) != height:
            self._buffer = [self._random_line(width) for _ in range(height)]
            self._last_size = (width, height)
        else:
            self._buffer.pop()
            self._buffer.insert(0, self._random_line(width))

        lines = [self._stylize_line(line) for line in self._buffer]
        self.update(Align.center(Group(*lines), vertical="middle"))

    def _random_line(self, width: int) -> str:
        preset = self.get_visual_preset()
        chars = preset.get("stream_chars") or preset.get("image_chars") or "01"
        return "".join(random.choice(chars) for _ in range(width))

    def _stylize_line(self, line: str) -> Text:
        primary = self.get_style_color("stream", "green")
        accent = self.get_style_color("stream_accent", "cyan")
        text = Text(line, style=primary)
        if line:
            accents = max(1, len(line) // 14)
            for _ in range(accents):
                idx = random.randrange(len(line))
                text.stylize(accent, idx, idx + 1)
        return text

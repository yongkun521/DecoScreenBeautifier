from datetime import datetime

from rich.align import Align
from rich.text import Text

from .base import GuiComponentBase


class ClockComponent(GuiComponentBase):
    def __init__(self, component_id: str = "p_clock", **kwargs) -> None:
        super().__init__(component_id, title="TIME SYNCHRONIZER", update_interval=1.0, **kwargs)

    def update_content(self) -> None:
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y / %m / %d")
        weekday_str = now.strftime("%A").upper()
        self.set_renderable(self._build_content(time_str, date_str, weekday_str))

    def _build_content(self, time_str, date_str, weekday_str):
        time_color = self.get_style_color("time", "magenta")
        date_color = self.get_style_color("date", "cyan")
        accent_color = self.get_style_color("accent", "yellow")

        time_text = Text(time_str, style=f"bold {time_color}")
        info_text = Text.assemble(
            (f"{date_str} ", date_color),
            (f"[{weekday_str}]", f"bold {accent_color}"),
        )
        glitched_title = self.glitch_text("SYSTEM TIME", probability=0.01)

        return Align.center(
            Text.assemble(glitched_title, "\n", time_text, "\n", info_text),
            vertical="middle",
        )

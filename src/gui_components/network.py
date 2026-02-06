import time
import psutil

from rich.align import Align
from rich.console import Group
from rich.table import Table
from rich.text import Text

from .base import GuiComponentBase


class NetworkComponent(GuiComponentBase):
    def __init__(self, component_id: str = "p_network", **kwargs) -> None:
        super().__init__(component_id, title="NETWORK UPLINK", update_interval=1.0, **kwargs)
        self.last_io = psutil.net_io_counters()
        self.last_time = time.time()
        self.up_speed = 0.0
        self.down_speed = 0.0

    def update_content(self) -> None:
        current_io = psutil.net_io_counters()
        current_time = time.time()
        elapsed = current_time - self.last_time
        if elapsed > 0:
            self.up_speed = (current_io.bytes_sent - self.last_io.bytes_sent) / elapsed
            self.down_speed = (current_io.bytes_recv - self.last_io.bytes_recv) / elapsed
        self.last_io = current_io
        self.last_time = current_time
        self.set_renderable(self._build_content())

    def _build_content(self):
        def format_speed(speed):
            if speed > 1024 * 1024:
                return f"{speed / (1024 * 1024):.2f} MB/s"
            return f"{speed / 1024:.2f} KB/s"

        down_color = self.get_style_color("net_down", "cyan")
        up_color = self.get_style_color("net_up", "magenta")
        label_color = self.get_style_color("accent", "white")

        table = Table.grid(padding=(0, 2))
        table.add_column(justify="right")
        table.add_column(justify="left")
        table.add_row(
            Text("DOWNLOAD:", style=f"bold {label_color}"),
            Text(format_speed(self.down_speed), style="bold white"),
        )
        table.add_row(
            Text("UPLOAD:", style=f"bold {label_color}"),
            Text(format_speed(self.up_speed), style="bold white"),
        )

        preset = self.get_visual_preset()
        arrow_down = preset.get("arrow_down", "▼")
        arrow_up = preset.get("arrow_up", "▲")
        arrows = arrow_down * min(5, int(self.down_speed / 102400) + 1) if self.down_speed > 0 else ""
        up_arrows = arrow_up * min(5, int(self.up_speed / 102400) + 1) if self.up_speed > 0 else ""

        arrows_line = Text.assemble(
            (f"RX {arrows}", down_color), "  ", (f"TX {up_arrows}", up_color)
        )
        return Align.center(Group(table, Text(""), arrows_line), vertical="middle")

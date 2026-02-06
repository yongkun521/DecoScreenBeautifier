import psutil
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .base import GuiComponentBase


class HardwareComponent(GuiComponentBase):
    def __init__(self, component_id: str = "p_hardware", **kwargs) -> None:
        super().__init__(component_id, title="SYSTEM ANALYZER", update_interval=1.0, **kwargs)
        self.cpu_history = []
        self.max_history = 20

    def update_content(self) -> None:
        cpu_percents = psutil.cpu_percent(percpu=True)
        if cpu_percents:
            avg_cpu = sum(cpu_percents) / len(cpu_percents)
        else:
            avg_cpu = 0.0
        self.cpu_history.append(avg_cpu)
        if len(self.cpu_history) > self.max_history:
            self.cpu_history.pop(0)

        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        self.set_renderable(self._build_content(cpu_percents, mem, swap))

    def _build_content(self, cpu_percents, mem, swap):
        cpu_ok = self.get_style_color("cpu_ok", "green")
        cpu_warn = self.get_style_color("cpu_warn", "yellow")
        cpu_crit = self.get_style_color("cpu_crit", "red")
        mem_color = self.get_style_color("mem", "cyan")
        swap_color = self.get_style_color("swap", "magenta")
        panel_cpu = self.get_style_color("panel_cpu", cpu_ok)
        panel_mem = self.get_style_color("panel_mem", "blue")

        cpu_grid = Table.grid(padding=(0, 1))
        cpu_grid.add_column(width=8)
        cpu_grid.add_column(width=15)

        for i, percent in enumerate(cpu_percents):
            if i >= 8:
                break
            bar_color = cpu_ok if percent < 70 else cpu_warn if percent < 90 else cpu_crit
            bar = self._make_cyber_bar(percent, width=12, color=bar_color)
            cpu_grid.add_row(f"CORE {i:02d}", bar)

        mem_bar = self._make_cyber_bar(mem.percent, width=25, color=mem_color)
        swap_bar = self._make_cyber_bar(swap.percent, width=25, color=swap_color)

        main_table = Table.grid(padding=1)
        main_table.add_column()
        main_table.add_column()
        main_table.add_row(
            Panel(cpu_grid, title="[CPU CORES]", border_style=panel_cpu),
            Panel(
                Text.assemble(
                    ("MEMORY USAGE\n", f"bold {mem_color}"),
                    mem_bar,
                    f" {mem.percent}%\n\n",
                    ("SWAP USAGE\n", f"bold {swap_color}"),
                    swap_bar,
                    f" {swap.percent}%",
                ),
                title="[MEMORY/SWAP]",
                border_style=panel_mem,
            ),
        )

        trend = self._make_trend_line(self.cpu_history)

        return Align.center(
            Group(
                main_table,
                Text(" "),
                Text.assemble(("CPU LOAD TREND: ", "bold white"), trend),
            ),
            vertical="middle",
        )

    def _make_cyber_bar(self, percentage, width=20, color="green"):
        preset = self.get_visual_preset()
        bar_full = preset.get("bar_full", "█")
        bar_empty = preset.get("bar_empty", "░")
        filled_width = int(width * (percentage / 100))
        bar = bar_full * filled_width + bar_empty * (width - filled_width)
        return Text(bar, style=color)

    def _make_trend_line(self, history):
        if not history:
            return Text("N/A")
        preset = self.get_visual_preset()
        chars = preset.get("sparkline", "▁▂▃▄▅▆▇█")
        if chars and chars[0] != " ":
            chars = " " + chars
        line = ""
        for val in history:
            idx = int((val / 100) * (len(chars) - 1))
            line += chars[idx]
        trend_color = self.get_style_color("accent", "yellow")
        return Text(line, style=f"bold {trend_color}")

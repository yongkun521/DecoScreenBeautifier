import os

import psutil
from rich.align import Align
from rich.console import Group
from rich.text import Text

from .base import BaseWidget


class StatusBadge(BaseWidget):
    """
    小型状态徽章组件
    """

    DEFAULT_CSS = """
    StatusBadge {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(title="STATUS", update_interval=1.0, **kwargs)

    def update_content(self) -> None:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        disk = self._disk_usage()
        status, color = self._status_level(cpu, mem, disk)

        label_color = self.get_style_color("muted", "grey70")
        cpu_bar = self._bar(cpu, width=10, color=self.get_style_color("cpu_ok", "green"))
        mem_bar = self._bar(mem, width=10, color=self.get_style_color("mem", "cyan"))
        disk_bar = self._bar(disk, width=10, color=self.get_style_color("warning", "yellow"))

        lines = [
            Text.assemble(("SYSTEM ", "bold"), (status, f"bold {color}")),
            Text.assemble(("CPU ", f"bold {label_color}"), cpu_bar, f" {cpu:.0f}%"),
            Text.assemble(("MEM ", f"bold {label_color}"), mem_bar, f" {mem:.0f}%"),
            Text.assemble(("DSK ", f"bold {label_color}"), disk_bar, f" {disk:.0f}%"),
        ]
        self.update(Align.center(Group(*lines), vertical="middle"))

    def _status_level(self, cpu: float, mem: float, disk: float) -> tuple[str, str]:
        crit = max(cpu, mem, disk)
        if crit >= 90:
            return ("CRITICAL", self.get_style_color("badge_crit", "red"))
        if crit >= 75:
            return ("WARN", self.get_style_color("badge_warn", "yellow"))
        return ("OK", self.get_style_color("badge_ok", "green"))

    def _bar(self, percent: float, width: int, color: str) -> Text:
        preset = self.get_visual_preset()
        bar_full = preset.get("bar_full", "█")
        bar_empty = preset.get("bar_empty", "░")
        filled = int(width * (percent / 100))
        bar = bar_full * filled + bar_empty * (width - filled)
        return Text(bar, style=color)

    def _disk_usage(self) -> float:
        root = "C:\\" if os.name == "nt" else os.path.abspath(os.sep)
        try:
            return psutil.disk_usage(root).percent
        except Exception:
            return 0.0

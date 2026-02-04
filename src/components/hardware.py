import psutil
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.columns import Columns
from rich.console import Group
from .base import BaseWidget

class HardwareMonitor(BaseWidget):
    """
    高级硬件监控组件
    显示多核 CPU、内存、Swap 以及简单的历史趋势
    """

    DEFAULT_CSS = """
    HardwareMonitor {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(title="SYSTEM ANALYZER", update_interval=1.0, **kwargs)
        self.cpu_history = []
        self.max_history = 20

    def update_content(self) -> None:
        """获取系统信息并更新显示"""
        cpu_percents = psutil.cpu_percent(percpu=True)
        avg_cpu = sum(cpu_percents) / len(cpu_percents)
        
        # 记录历史
        self.cpu_history.append(avg_cpu)
        if len(self.cpu_history) > self.max_history:
            self.cpu_history.pop(0)
            
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # 构建显示内容
        self.update(self._build_content(cpu_percents, mem, swap))

    def _build_content(self, cpu_percents, mem, swap):
        """渲染组件内容"""
        table = Table.grid(expand=True)
        table.add_column(justify="left")

        cpu_ok = self.get_style_color("cpu_ok", "green")
        cpu_warn = self.get_style_color("cpu_warn", "yellow")
        cpu_crit = self.get_style_color("cpu_crit", "red")
        mem_color = self.get_style_color("mem", "cyan")
        swap_color = self.get_style_color("swap", "magenta")
        panel_cpu = self.get_style_color("panel_cpu", cpu_ok)
        panel_mem = self.get_style_color("panel_mem", "blue")
        
        # 1. CPU 核心状态
        cpu_grid = Table.grid(padding=(0, 1))
        cpu_grid.add_column(width=8)  # Core name
        cpu_grid.add_column(width=15) # Bar
        
        for i, percent in enumerate(cpu_percents):
            if i >= 8: break # 最多显示 8 个核心，防止溢出
            bar_color = cpu_ok if percent < 70 else cpu_warn if percent < 90 else cpu_crit
            bar = self._make_cyber_bar(percent, width=12, color=bar_color)
            cpu_grid.add_row(f"CORE {i:02d}", bar)
            
        # 2. 内存与 Swap
        mem_bar = self._make_cyber_bar(mem.percent, width=25, color=mem_color)
        swap_bar = self._make_cyber_bar(swap.percent, width=25, color=swap_color)
        
        # 3. 整合布局
        main_table = Table.grid(padding=1)
        main_table.add_column()
        main_table.add_column()
        
        # 左侧核心列表
        main_table.add_row(
            Panel(cpu_grid, title="[CPU CORES]", border_style=panel_cpu),
            Panel(
                Text.assemble(
                    ("MEMORY USAGE\n", f"bold {mem_color}"),
                    mem_bar, f" {mem.percent}%\n\n",
                    ("SWAP USAGE\n", f"bold {swap_color}"),
                    swap_bar, f" {swap.percent}%"
                ),
                title="[MEMORY/SWAP]",
                border_style=panel_mem
            )
        )
        
        # 底部趋势图 (简单 ASCII)
        trend = self._make_trend_line(self.cpu_history)
        
        return Align.center(
            Group(
                main_table,
                Text(" "),  # Spacer
                Text.assemble(
                    ("CPU LOAD TREND: ", "bold white"),
                    trend
                )
            ),
            vertical="middle"
        )

    def _make_cyber_bar(self, percentage, width=20, color="green"):
        """创建一个具有赛博风格的块状进度条"""
        preset = self.get_visual_preset()
        bar_full = preset.get("bar_full", "█")
        bar_empty = preset.get("bar_empty", "░")
        filled_width = int(width * (percentage / 100))
        bar = bar_full * filled_width + bar_empty * (width - filled_width)
        return Text(bar, style=color)

    def _make_trend_line(self, history):
        """生成简单的趋势线"""
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

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
        
        # 1. CPU 核心状态
        cpu_grid = Table.grid(padding=(0, 1))
        cpu_grid.add_column(width=8)  # Core name
        cpu_grid.add_column(width=15) # Bar
        
        for i, percent in enumerate(cpu_percents):
            if i >= 8: break # 最多显示 8 个核心，防止溢出
            bar = self._make_cyber_bar(percent, width=12, color="green" if percent < 70 else "yellow" if percent < 90 else "red")
            cpu_grid.add_row(f"CORE {i:02d}", bar)
            
        # 2. 内存与 Swap
        mem_bar = self._make_cyber_bar(mem.percent, width=25, color="cyan")
        swap_bar = self._make_cyber_bar(swap.percent, width=25, color="magenta")
        
        # 3. 整合布局
        main_table = Table.grid(padding=1)
        main_table.add_column()
        main_table.add_column()
        
        # 左侧核心列表
        main_table.add_row(
            Panel(cpu_grid, title="[CPU CORES]", border_style="green"),
            Panel(
                Text.assemble(
                    ("MEMORY USAGE\n", "bold cyan"),
                    mem_bar, f" {mem.percent}%\n\n",
                    ("SWAP USAGE\n", "bold magenta"),
                    swap_bar, f" {swap.percent}%"
                ),
                title="[MEMORY/SWAP]",
                border_style="blue"
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
        filled_width = int(width * (percentage / 100))
        bar = "█" * filled_width + "░" * (width - filled_width)
        return Text(bar, style=color)

    def _make_trend_line(self, history):
        """生成简单的趋势线"""
        if not history:
            return Text("N/A")
        
        chars = " ▂▃▄▅▆▇█"
        line = ""
        for val in history:
            idx = int((val / 100) * (len(chars) - 1))
            line += chars[idx]
        return Text(line, style="bold yellow")

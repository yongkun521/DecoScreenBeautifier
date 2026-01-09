import psutil
from rich.text import Text
from rich.progress import BarColumn, Progress, TextColumn
from rich.panel import Panel
from rich.align import Align
from rich.layout import Layout
from .base import BaseWidget

class HardwareMonitor(BaseWidget):
    """
    硬件监控组件
    显示 CPU 和 内存 使用率
    """

    DEFAULT_CSS = """
    HardwareMonitor {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(title="SYSTEM STATUS", update_interval=2.0, **kwargs)
        self.cpu_percent = 0.0
        self.memory_percent = 0.0

    def update_content(self) -> None:
        """获取系统信息并更新显示"""
        self.cpu_percent = psutil.cpu_percent()
        self.memory_percent = psutil.virtual_memory().percent
        
        # 构建显示内容
        self.update(self._build_content())

    def _build_content(self):
        """渲染组件内容"""
        # CPU 进度条
        cpu_bar = self._make_bar(self.cpu_percent, "CPU", "red" if self.cpu_percent > 80 else "green")
        
        # 内存 进度条
        mem_bar = self._make_bar(self.memory_percent, "RAM", "yellow" if self.memory_percent > 80 else "blue")
        
        return Align.center(Text.assemble(cpu_bar, "\n\n", mem_bar), vertical="middle")

    def _make_bar(self, percentage, label, color):
        """创建一个简单的 ASCII 进度条"""
        width = 20
        filled = int(width * (percentage / 100))
        bar = f"[{'#' * filled}{'-' * (width - filled)}]"
        return Text(f"{label}: {bar} {percentage:.1f}%", style=f"bold {color}")

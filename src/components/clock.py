from datetime import datetime
from rich.text import Text
from rich.align import Align
from .base import BaseWidget

class ClockWidget(BaseWidget):
    """
    时钟组件
    显示当前日期和时间
    """

    DEFAULT_CSS = """
    ClockWidget {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(title="CHRONO", update_interval=1.0, **kwargs)

    def update_content(self) -> None:
        """获取当前时间并更新显示"""
        now = datetime.now()
        
        # 格式化时间
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")
        
        # 构建显示内容
        self.update(self._build_content(time_str, date_str))

    def _build_content(self, time_str, date_str):
        """渲染组件内容"""
        # 使用大字体显示时间 (这里暂时用普通文本，后续可集成 ASCII 艺术字体)
        time_text = Text(time_str, style="bold magenta", justify="center")
        # time_text.font_size = 3  # Textual 不直接支持 font_size，这只是占位，实际需要 ASCII 字体库
        
        # 日期显示
        date_text = Text(date_str, style="cyan", justify="center")
        
        return Align.center(Text.assemble(time_text, "\n", date_text), vertical="middle")

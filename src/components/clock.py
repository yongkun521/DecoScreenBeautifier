from datetime import datetime
from rich.text import Text
from rich.align import Align
from .base import BaseWidget

class ClockWidget(BaseWidget):
    """
    赛博朋克时钟组件
    显示当前日期、时间和星期，带有一些视觉特效
    """

    DEFAULT_CSS = """
    ClockWidget {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(title="TIME SYNCHRONIZER", update_interval=1.0, **kwargs)

    def update_content(self) -> None:
        """获取当前时间并更新显示"""
        now = datetime.now()
        
        # 格式化时间
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y / %m / %d")
        weekday_str = now.strftime("%A").upper()
        
        # 构建显示内容
        self.update(self._build_content(time_str, date_str, weekday_str))

    def _build_content(self, time_str, date_str, weekday_str):
        """渲染组件内容"""
        time_color = self.get_style_color("time", "magenta")
        date_color = self.get_style_color("date", "cyan")
        accent_color = self.get_style_color("accent", "yellow")

        # 时间主体
        time_text = Text(time_str, style=f"bold {time_color}")
        
        # 底部信息
        info_text = Text.assemble(
            (f"{date_str} ", date_color),
            (f"[{weekday_str}]", f"bold {accent_color}")
        )
        
        # 添加一些随机故障效果
        glitched_title = self.glitch_text("SYSTEM TIME", probability=0.01)

        return Align.center(
            Text.assemble(
                glitched_title, "\n",
                time_text, "\n",
                info_text
            ),
            vertical="middle"
        )

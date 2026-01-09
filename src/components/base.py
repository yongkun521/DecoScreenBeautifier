from textual.widgets import Static
from textual.reactive import reactive
from textual.message import Message

class BaseWidget(Static):
    """
    所有组件的基类
    提供统一的更新机制、样式接口和生命周期管理
    """

    DEFAULT_CSS = """
    BaseWidget {
        background: $surface;
        color: $text;
        border: heavy $primary;
        padding: 0 1;
    }
    """

    def __init__(self, title: str = "", update_interval: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.border_title = title
        self._update_interval = update_interval
        self._timer = None

    def on_mount(self) -> None:
        """组件挂载时启动定时更新"""
        if self._update_interval > 0:
            self._timer = self.set_interval(self._update_interval, self.update_content)
        self.update_content()  # 初始更新

    def update_content(self) -> None:
        """
        更新组件内容的抽象方法
        子类必须实现此方法以更新显示内容
        """
        pass

    def set_update_interval(self, interval: float) -> None:
        """动态调整更新频率"""
        self._update_interval = interval
        if self._timer:
            self._timer.stop()
        if interval > 0:
            self._timer = self.set_interval(interval, self.update_content)

    def on_click(self) -> None:
        """处理点击事件（为后续编辑功能预留）"""
        pass

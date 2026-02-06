from textual.widgets import Static
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
import random

class BaseWidget(Static):
    """
    所有组件的基类
    提供统一的更新机制、样式接口和生命周期管理
    """

    DEFAULT_CSS = """
    BaseWidget {
        background: transparent;
        color: #00FF41;
        border: heavy #00FF41;
        padding: 0 1;
        margin: 1;
    }
    """

    def __init__(self, title: str = "", update_interval: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self.border_title = f" [ {title} ] "
        self._update_interval = update_interval
        self._timer = None
        self._visual_preset = {}
        self._style_preset = {}

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

    def set_visual_preset(self, preset: dict) -> None:
        """设置渲染字符/样式预设"""
        self._visual_preset = preset or {}
        self.update_content()

    def set_style_preset(self, preset: dict) -> None:
        """设置样式 Token 预设"""
        self._style_preset = preset or {}
        self._apply_style_preset()
        self.update_content()

    def get_visual_preset(self) -> dict:
        """获取当前预设，如果未设置则尝试读取 App 全局预设"""
        if self._visual_preset:
            return self._visual_preset
        app = getattr(self, "app", None)
        if app and hasattr(app, "visual_preset"):
            return app.visual_preset
        return {}

    def get_style_preset(self) -> dict:
        """获取样式 Token 预设"""
        if self._style_preset:
            return self._style_preset
        app = getattr(self, "app", None)
        if app and hasattr(app, "style_preset"):
            return app.style_preset
        return {}

    def get_style_color(self, key: str, default: str) -> str:
        preset = self.get_style_preset()
        colors = preset.get("colors", {}) if isinstance(preset, dict) else {}
        return colors.get(key, default)

    def _apply_style_preset(self) -> None:
        preset = self.get_style_preset()
        title_style = preset.get("title_style")
        title_color = preset.get("title_color")
        if title_style:
            self.styles.border_title_style = title_style
        if title_color:
            self.styles.border_title_color = title_color

    def glitch_text(self, text: str, probability: float = 0.05) -> Text:
        """为文本添加随机故障效果"""
        glitch_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = Text()
        for char in text:
            if char != " " and random.random() < probability:
                result.append(random.choice(glitch_chars), style="blink bold magenta")
            else:
                result.append(char)
        return result

    def set_update_interval(self, interval: float) -> None:
        """动态调整更新频率"""
        self._update_interval = interval
        if self._timer:
            self._timer.stop()
        if interval > 0:
            self._timer = self.set_interval(interval, self.update_content)

    def export_render_grid(
        self,
        width: int,
        height: int,
        effects_config: object = None,
        frame_index: int = 0,
    ):
        """将当前组件内容转换为渲染网格数据"""
        from core.renderer import render_textual_widget

        grid = render_textual_widget(self, width, height)
        if effects_config:
            try:
                from core.retro_effects import apply_retro_effects
            except Exception:
                return grid
            return apply_retro_effects(grid, effects_config, frame_index=frame_index)
        return grid

    def on_click(self) -> None:
        """处理点击事件（为后续编辑功能预留）"""
        pass

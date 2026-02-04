from textual.screen import Screen
from textual.containers import Grid
from textual.widgets import Header, Footer, Static, Placeholder
from textual.app import ComposeResult

# 导入自定义组件
from components.base import BaseWidget
from components.hardware import HardwareMonitor
from components.clock import ClockWidget
from components.audio import AudioVisualizer
from components.image import ImageWidget
from components.network import NetworkMonitor
from components.status import StatusBadge
from components.stream import DataStreamWidget
from components.ticker import InfoTicker

class DisplayScreen(Screen):
    """主显示界面，用于展示各种 CLI 组件"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._active_template_classes = []

    def compose(self) -> ComposeResult:
        """构建主界面布局"""
        yield Header(show_clock=True)
        
        # 使用 Grid 布局容器
        with Grid(id="main_grid"):
            # 硬件监控组件
            yield HardwareMonitor(id="p_hardware")
            
            # 网络监控组件
            yield NetworkMonitor(id="p_network")
            
            # 时钟组件
            yield ClockWidget(id="p_clock")
            
            # 音频可视化组件
            yield AudioVisualizer(id="p_audio")
            
            # 图像组件
            yield ImageWidget(id="p_image", image_path="assets/logo.png")

            # 信息条组件
            yield InfoTicker(id="p_ticker")

            # 状态徽章组件
            yield StatusBadge(id="p_badge")

            # 信号流装饰组件
            yield DataStreamWidget(id="p_stream")
            
        yield Footer()

    def on_mount(self) -> None:
        """屏幕加载时的初始化操作"""
        self.title = "DecoScreen :: Main Display"
        if hasattr(self.app, "config_manager"):
            template = self.app.config_manager.get_active_template()
            self.apply_template(template)

    def apply_template(self, template) -> None:
        """应用模板样式与组件变体"""
        if not template:
            return
        layout_class = template.get("layout_class")
        theme_class = template.get("theme_class")
        new_classes = [c for c in (layout_class, theme_class) if c]

        if self._active_template_classes:
            self.remove_class(*self._active_template_classes)
        if new_classes:
            self.add_class(*new_classes)
        self._active_template_classes = new_classes

        self._apply_component_variants(template.get("component_variants", {}))
        self._apply_component_visibility(template.get("active_components"))
        self._apply_visual_preset()

    def _apply_component_variants(self, variants: dict) -> None:
        variant_classes = {
            "variant-dense",
            "variant-slim",
            "variant-compact",
            "variant-minimal",
            "variant-banner",
            "variant-glow",
            "variant-outline",
        }
        for widget in self.query(BaseWidget):
            widget.remove_class(*variant_classes)
        for widget_id, variant in variants.items():
            try:
                widget = self.query_one(f"#{widget_id}", BaseWidget)
            except Exception:
                widget = None
            if widget and variant:
                widget.add_class(variant)

    def _apply_visual_preset(self) -> None:
        for widget in self.query(BaseWidget):
            widget.set_visual_preset(getattr(self.app, "visual_preset", {}))
            widget.set_style_preset(getattr(self.app, "style_preset", {}))

    def _apply_component_visibility(self, active_components) -> None:
        if active_components is None:
            active = {"p_hardware", "p_network", "p_clock", "p_audio", "p_image"}
        else:
            active = set(active_components)
        for widget in self.query(BaseWidget):
            widget.display = widget.id in active

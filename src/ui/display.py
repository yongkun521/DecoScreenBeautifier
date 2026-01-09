from textual.screen import Screen
from textual.containers import Grid
from textual.widgets import Header, Footer, Static, Placeholder
from textual.app import ComposeResult

# 导入自定义组件
from components.hardware import HardwareMonitor
from components.clock import ClockWidget
from components.audio import AudioVisualizer
from components.image import ImageWidget

class DisplayScreen(Screen):
    """主显示界面，用于展示各种 CLI 组件"""

    def compose(self) -> ComposeResult:
        """构建主界面布局"""
        yield Header(show_clock=True)
        
        # 使用 Grid 布局容器
        with Grid(id="main_grid"):
            # 硬件监控组件
            yield HardwareMonitor(id="p_hardware")
            
            # 时钟组件
            yield ClockWidget(id="p_clock")
            
            # 音频可视化组件
            yield AudioVisualizer(id="p_audio")
            
            # 图像组件 (这里没有默认图片，会显示提示)
            # 用户可以通过后续的编辑器加载图片
            yield ImageWidget(id="p_image", image_path="assets/logo.png")
            
        yield Footer()

    def on_mount(self) -> None:
        """屏幕加载时的初始化操作"""
        self.title = "DecoScreen :: Main Display"

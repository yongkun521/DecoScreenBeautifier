from rich.align import Align
from rich.text import Text
from .base import BaseWidget
from processors.image import ImageProcessor
import os

class ImageWidget(BaseWidget):
    """
    图像组件
    显示转换后的 ASCII 图片
    """

    DEFAULT_CSS = """
    ImageWidget {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, image_path: str = None, **kwargs):
        super().__init__(title="VISUAL", update_interval=0, **kwargs) # 静态图片不需要定时更新
        self.image_path = image_path
        self.processor = ImageProcessor()
        self.ascii_art = None

    def on_mount(self) -> None:
        """组件挂载时加载图片"""
        super().on_mount()
        # 初始加载，之后在 update_content 中可能会重新计算（如果支持动态调整大小）
        # 但 Textual 的 Static 组件如果内容不变不需要频繁更新
        # 我们可以在 resize 事件中重新计算
        self.load_image()

    def update_content(self) -> None:
        """当预设变化时重新渲染"""
        self.load_image()

    def load_image(self):
        """加载并处理图片"""
        if not self.image_path or not os.path.exists(self.image_path):
            self.update(Align.center(Text("No Image Loaded", style="red"), vertical="middle"))
            return

        # 获取组件当前大小 (字符数)
        # 注意：在 on_mount 时 size 可能还未确定，可能需要稍后更新
        # 这里先给一个默认值，或者在 on_resize 中处理
        w, h = self.size.width, self.size.height
        if w == 0 or h == 0:
            w, h = 40, 20 # 默认值

        # 减去边框 padding
        w = max(1, w - 2)
        h = max(1, h - 2)

        scale = self._get_render_scale()
        render_w = max(1, int(w * scale))
        render_h = max(1, int(h * scale))
        preset = self.get_visual_preset()
        charset = preset.get("image_chars") if preset else None

        self.ascii_art = self.processor.process_image(
            self.image_path,
            width=render_w,
            height=render_h,
            charset=charset,
        )
        self.update(Align.center(self.ascii_art, vertical="middle"))

    def on_resize(self) -> None:
        """当组件大小改变时重新渲染图片"""
        self.load_image()

    def _get_render_scale(self) -> float:
        scale = getattr(self.app, "global_scale", 1.0)
        try:
            scale = float(scale)
        except (TypeError, ValueError):
            scale = 1.0
        return max(0.5, min(scale, 2.0))

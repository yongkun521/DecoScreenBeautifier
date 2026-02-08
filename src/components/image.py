import os

from rich.align import Align
from rich.text import Text

from .base import BaseWidget

try:
    from processors.image import ImageProcessor
except Exception:
    ImageProcessor = None


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
        super().__init__(title="VISUAL", update_interval=0, **kwargs)
        self.image_path = image_path
        self.processor = ImageProcessor() if ImageProcessor is not None else None
        self.ascii_art = None

    def on_mount(self) -> None:
        super().on_mount()
        self.load_image()

    def update_content(self) -> None:
        self.load_image()

    def load_image(self):
        if self.processor is None:
            error_color = self.get_style_color("danger", "red")
            self.update(
                Align.center(
                    Text("Image processor unavailable (cv2/Pillow missing)", style=error_color),
                    vertical="middle",
                )
            )
            return

        if not self.image_path or not os.path.exists(self.image_path):
            error_color = self.get_style_color("danger", "red")
            self.update(
                Align.center(Text("No Image Loaded", style=error_color), vertical="middle")
            )
            return

        w, h = self.size.width, self.size.height
        if w == 0 or h == 0:
            w, h = 40, 20

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
        self.load_image()

    def _get_render_scale(self) -> float:
        scale = getattr(self.app, "global_scale", 1.0)
        try:
            scale = float(scale)
        except (TypeError, ValueError):
            scale = 1.0
        return max(0.5, min(scale, 2.0))


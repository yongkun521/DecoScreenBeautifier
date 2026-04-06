import os
import sys
from pathlib import Path

from rich.align import Align
from rich.text import Text

from core.layout_config import (
    DEFAULT_IMAGE_DISPLAY_MODE,
    DEFAULT_IMAGE_RENDER_MODE,
    normalize_image_display_mode,
    normalize_image_render_mode,
)

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

    def __init__(
        self,
        image_path: str = None,
        image_display_mode: str = DEFAULT_IMAGE_DISPLAY_MODE,
        image_render_mode: str = DEFAULT_IMAGE_RENDER_MODE,
        **kwargs,
    ):
        super().__init__(title="VISUAL", update_interval=0, **kwargs)
        self.image_path = image_path
        self.image_display_mode = normalize_image_display_mode(image_display_mode)
        self.image_render_mode = normalize_image_render_mode(image_render_mode)
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

        resolved_path = self._resolve_image_path(self.image_path)
        if resolved_path is None or not resolved_path.exists():
            error_color = self.get_style_color("danger", "red")
            self.update(
                Align.center(Text("No Image Loaded", style=error_color), vertical="middle")
            )
            return

        inner_width, inner_height = self.get_content_size(default=(40, 20))
        render_w = inner_width
        render_h = inner_height * 2 if self.image_render_mode == "pixel" else inner_height
        preset = self.get_visual_preset()
        charset = preset.get("image_chars") if preset else None

        self.ascii_art = self.processor.process_image(
            str(resolved_path),
            width=render_w,
            height=render_h,
            charset=charset,
            display_mode=self.image_display_mode,
            render_mode=self.image_render_mode,
            sample_scale=self._get_render_scale(),
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

    def _resolve_image_path(self, image_path: str | None) -> Path | None:
        raw_path = str(image_path or "").strip()
        if not raw_path:
            return None

        candidate = Path(raw_path).expanduser()
        candidates = []
        if candidate.is_absolute():
            candidates.append(candidate)
        else:
            candidates.append(Path.cwd() / candidate)
            app = getattr(self, "app", None)
            config_manager = getattr(app, "config_manager", None)
            data_dir = getattr(config_manager, "data_dir", None)
            if data_dir:
                candidates.append(Path(data_dir) / candidate)
            if getattr(sys, "frozen", False):
                candidates.append(Path(sys.executable).resolve().parent / candidate)
            else:
                candidates.append(Path(__file__).resolve().parents[2] / candidate)

        seen = set()
        for path in candidates:
            try:
                resolved = path.resolve()
            except Exception:
                resolved = path
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            if resolved.exists():
                return resolved
        return candidates[0] if candidates else None

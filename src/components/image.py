import os
import sys
from pathlib import Path

from rich.align import Align
from rich.text import Text

from core.layout_config import (
    DEFAULT_IMAGE_DISPLAY_MODE,
    DEFAULT_IMAGE_EDGE_STRENGTH,
    DEFAULT_IMAGE_EFFECT_MODE,
    DEFAULT_IMAGE_EFFECT_THRESHOLD,
    DEFAULT_IMAGE_INVERT,
    DEFAULT_IMAGE_RENDER_MODE,
    normalize_image_edge_strength,
    normalize_image_effect_mode,
    normalize_image_effect_threshold,
    normalize_image_display_mode,
    normalize_image_invert,
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

    MAX_MEDIA_FRAMES = 120
    MIN_FRAME_SECONDS = 0.04
    MAX_FRAME_SECONDS = 2.0

    def __init__(
        self,
        image_path: str = None,
        image_display_mode: str = DEFAULT_IMAGE_DISPLAY_MODE,
        image_render_mode: str = DEFAULT_IMAGE_RENDER_MODE,
        image_effect_mode: str = DEFAULT_IMAGE_EFFECT_MODE,
        image_effect_threshold: float = DEFAULT_IMAGE_EFFECT_THRESHOLD,
        image_edge_strength: float = DEFAULT_IMAGE_EDGE_STRENGTH,
        image_invert: bool = DEFAULT_IMAGE_INVERT,
        **kwargs,
    ):
        super().__init__(title="VISUAL", update_interval=0, **kwargs)
        self.image_path = image_path
        self.image_display_mode = normalize_image_display_mode(image_display_mode)
        self.image_render_mode = normalize_image_render_mode(image_render_mode)
        self.image_effect_mode = normalize_image_effect_mode(image_effect_mode)
        self.image_effect_threshold = normalize_image_effect_threshold(image_effect_threshold)
        self.image_edge_strength = normalize_image_edge_strength(image_edge_strength)
        self.image_invert = normalize_image_invert(image_invert)
        self.processor = ImageProcessor() if ImageProcessor is not None else None
        self.ascii_art = None
        self._media_frames = []
        self._media_durations = []
        self._media_source_key = None
        self._frame_index = 0
        self._animation_timer = None
        self._rendered_frame_cache = {}

    def on_mount(self) -> None:
        super().on_mount()

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
            self._clear_media_state()
            error_color = self.get_style_color("danger", "red")
            self.update(
                Align.center(Text("No Image Loaded", style=error_color), vertical="middle")
            )
            return

        if not self._ensure_media_frames(resolved_path):
            return

        self._render_current_frame()
        self._sync_animation_timer()

    def _ensure_media_frames(self, resolved_path: Path) -> bool:
        source_key = self._media_source_key_for_path(resolved_path)
        if source_key == self._media_source_key and self._media_frames:
            return True

        try:
            frames, durations = self.processor.load_image_frames(
                str(resolved_path),
                max_frames=self.MAX_MEDIA_FRAMES,
            )
        except Exception as exc:
            error_color = self.get_style_color("danger", "red")
            self.update(
                Align.center(Text(f"Image Error: {exc}", style=error_color), vertical="middle")
            )
            self._stop_animation_timer()
            return False

        self._media_source_key = source_key
        self._media_frames = frames
        self._media_durations = durations
        self._frame_index = 0
        self._rendered_frame_cache.clear()
        return True

    def _clear_media_state(self) -> None:
        self._stop_animation_timer()
        self._media_source_key = None
        self._media_frames = []
        self._media_durations = []
        self._frame_index = 0
        self._rendered_frame_cache.clear()

    def _render_current_frame(self) -> None:
        if not self._media_frames:
            return

        inner_width, inner_height = self.get_content_size(default=(40, 20))
        render_w = inner_width
        render_h = inner_height * 2 if self.image_render_mode == "pixel" else inner_height
        preset = self.get_visual_preset()
        charset = preset.get("image_chars") if preset else None
        palette = self._get_effect_palette()
        render_scale = self._get_render_scale()
        threshold = self._get_effect_threshold()
        frame_index = min(self._frame_index, len(self._media_frames) - 1)
        cache_key = self._render_cache_key(
            frame_index=frame_index,
            width=render_w,
            height=render_h,
            charset=charset,
            palette=palette,
            threshold=threshold,
            sample_scale=render_scale,
        )
        cached = self._rendered_frame_cache.get(cache_key)
        if cached is not None:
            self.ascii_art = cached.copy()
        else:
            self.ascii_art = self.processor.process_array(
                self._media_frames[frame_index],
                width=render_w,
                height=render_h,
                charset=charset,
                display_mode=self.image_display_mode,
                render_mode=self.image_render_mode,
                effect_mode=self.image_effect_mode,
                palette=palette,
                threshold=threshold,
                edge_strength=self.image_edge_strength,
                invert=self.image_invert,
                sample_scale=render_scale,
            )
            self._rendered_frame_cache[cache_key] = self.ascii_art.copy()
            self._trim_rendered_frame_cache()

        if self.uses_light_chrome():
            footer_parts = [self.image_render_mode, self.image_display_mode]
            if self.image_effect_mode != "none":
                footer_parts.append(self.image_effect_mode)
            if len(self._media_frames) > 1:
                footer_parts.append(f"gif {frame_index + 1}/{len(self._media_frames)}")
            footer = " | ".join(footer_parts)
            self.update(self.compose_widget_content(self.ascii_art, footer=footer))
        else:
            self.update(Align.center(self.ascii_art, vertical="middle"))

    def on_resize(self) -> None:
        self.load_image()

    def on_unmount(self) -> None:
        self._stop_animation_timer()

    def _sync_animation_timer(self) -> None:
        if len(self._media_frames) <= 1:
            self._stop_animation_timer()
            return
        if self._animation_timer is not None:
            return
        self._schedule_next_frame()

    def _schedule_next_frame(self) -> None:
        if len(self._media_frames) <= 1 or not self.is_mounted:
            self._animation_timer = None
            return
        duration_ms = 100
        if self._media_durations:
            duration_ms = self._media_durations[self._frame_index % len(self._media_durations)]
        delay = max(self.MIN_FRAME_SECONDS, min(duration_ms / 1000.0, self.MAX_FRAME_SECONDS))
        self._animation_timer = self.set_timer(delay, self._advance_frame)

    def _advance_frame(self) -> None:
        self._animation_timer = None
        if len(self._media_frames) <= 1:
            return
        self._frame_index = (self._frame_index + 1) % len(self._media_frames)
        self._render_current_frame()
        self._schedule_next_frame()

    def _stop_animation_timer(self) -> None:
        if self._animation_timer is None:
            return
        try:
            self._animation_timer.stop()
        except Exception:
            pass
        self._animation_timer = None

    def _get_render_scale(self) -> float:
        scale = getattr(self.app, "global_scale", 1.0)
        try:
            scale = float(scale)
        except (TypeError, ValueError):
            scale = 1.0
        return max(0.5, min(scale, 2.0))

    def _get_effect_palette(self) -> dict[str, str]:
        colors = {}
        preset = self.get_style_preset()
        if isinstance(preset, dict):
            colors = preset.get("colors", {}) if isinstance(preset.get("colors"), dict) else {}
        return {
            "background": colors.get("background") or colors.get("surface") or "#000000",
            "primary": colors.get("primary") or "#00FF41",
            "accent": colors.get("accent") or colors.get("secondary") or "#FFD700",
        }

    def _get_effect_threshold(self) -> float | None:
        if self.image_effect_threshold <= 0:
            return None
        return self.image_effect_threshold

    def _media_source_key_for_path(self, path: Path) -> tuple:
        try:
            stat = path.stat()
            return (str(path.resolve()), stat.st_mtime_ns, stat.st_size)
        except OSError:
            return (str(path), None, None)

    def _render_cache_key(
        self,
        *,
        frame_index: int,
        width: int,
        height: int,
        charset: str | None,
        palette: dict[str, str],
        threshold: float | None,
        sample_scale: float,
    ) -> tuple:
        return (
            self._media_source_key,
            frame_index,
            int(width),
            int(height),
            charset or "",
            self.image_display_mode,
            self.image_render_mode,
            self.image_effect_mode,
            tuple(sorted(palette.items())),
            threshold,
            self.image_edge_strength,
            self.image_invert,
            sample_scale,
        )

    def _trim_rendered_frame_cache(self) -> None:
        max_items = max(1, min(len(self._media_frames), self.MAX_MEDIA_FRAMES))
        if len(self._rendered_frame_cache) <= max_items:
            return
        for key in list(self._rendered_frame_cache.keys())[: len(self._rendered_frame_cache) - max_items]:
            self._rendered_frame_cache.pop(key, None)

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

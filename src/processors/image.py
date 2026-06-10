from collections import OrderedDict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageSequence
from rich.text import Text

from core.layout_config import (
    DEFAULT_IMAGE_DISPLAY_MODE,
    DEFAULT_IMAGE_EFFECT_MODE,
    DEFAULT_IMAGE_RENDER_MODE,
    normalize_image_effect_mode,
    normalize_image_display_mode,
    normalize_image_render_mode,
)


class ImageProcessor:
    """
    图像处理器
    负责将位图转换为 ASCII/ANSI 字符画
    """

    # 字符集：从暗到亮
    ASCII_CHARS = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
    
    # 简化的字符集 (效果可能更清晰)
    SIMPLE_CHARS = "@%#*+=-:. "

    ASCII_CHAR_HEIGHT_RATIO = 0.5
    PIXEL_HEIGHT_RATIO = 1.0
    MAX_CACHE_ITEMS = 32
    MAX_IMAGE_FRAMES = 120

    def __init__(self):
        self._render_cache = OrderedDict()

    def process_image(
        self,
        image_path: str,
        width: int,
        height: int = None,
        color: bool = True,
        charset: str = None,
        display_mode: str = DEFAULT_IMAGE_DISPLAY_MODE,
        render_mode: str = DEFAULT_IMAGE_RENDER_MODE,
        effect_mode: str = DEFAULT_IMAGE_EFFECT_MODE,
        palette: object = None,
        threshold: float | None = None,
        edge_strength: float = 0.5,
        invert: bool = False,
        sample_scale: float = 1.0,
    ) -> Text:
        """
        处理图像并返回 Rich Text 对象
        
        :param image_path: 图片路径
        :param width: 目标宽度 (字符数)
        :param height: 目标高度 (字符数)，如果为 None 则按比例计算
        :param color: 是否使用 ANSI 颜色
        :param display_mode: 拉伸 / 填充 / 等比缩放
        :param render_mode: ascii / pixel
        :param effect_mode: none / silhouette / edge / duotone / dither / posterize
        :param sample_scale: 仅影响采样密度，不改变最终字符占位
        :return: Rich Text 对象
        """
        try:
            cache_key = self._make_file_cache_key(
                image_path=image_path,
                width=width,
                height=height,
                color=color,
                charset=charset,
                display_mode=display_mode,
                render_mode=render_mode,
                effect_mode=effect_mode,
                palette=palette,
                threshold=threshold,
                edge_strength=edge_strength,
                invert=invert,
                sample_scale=sample_scale,
            )
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached

            frames, _durations = self.load_image_frames(image_path, max_frames=1)
            img = frames[0]
            result = self.process_array(
                img,
                width=width,
                height=height,
                color=color,
                charset=charset,
                display_mode=display_mode,
                render_mode=render_mode,
                effect_mode=effect_mode,
                palette=palette,
                threshold=threshold,
                edge_strength=edge_strength,
                invert=invert,
                sample_scale=sample_scale,
            )
            self._cache_set(cache_key, result)
            return self._copy_text(result)
        except Exception as e:
            return Text(f"Image Error: {e}", style="red")

    def load_image_frames(
        self,
        image_path: str,
        *,
        max_frames: int | None = None,
    ) -> tuple[list[np.ndarray], list[int]]:
        """
        Load static or animated image frames as RGB arrays.

        GIF and other animated formats use the same downstream render pipeline
        as static images; this method only performs decoding and duration readout.
        """
        frame_limit = max(1, int(max_frames or self.MAX_IMAGE_FRAMES))
        frames: list[np.ndarray] = []
        durations: list[int] = []
        with Image.open(image_path) as pil_image:
            default_duration = int(pil_image.info.get("duration") or 100)
            for frame in ImageSequence.Iterator(pil_image):
                frames.append(np.array(frame.convert("RGB")))
                durations.append(max(20, int(frame.info.get("duration") or default_duration)))
                if len(frames) >= frame_limit:
                    break

        if not frames:
            raise ValueError("No image frames decoded")
        return frames, durations

    def process_array(
        self,
        img: np.ndarray,
        *,
        width: int,
        height: int | None = None,
        color: bool = True,
        charset: str | None = None,
        display_mode: str = DEFAULT_IMAGE_DISPLAY_MODE,
        render_mode: str = DEFAULT_IMAGE_RENDER_MODE,
        effect_mode: str = DEFAULT_IMAGE_EFFECT_MODE,
        palette: object = None,
        threshold: float | None = None,
        edge_strength: float = 0.5,
        invert: bool = False,
        sample_scale: float = 1.0,
    ) -> Text:
        render_mode = normalize_image_render_mode(render_mode)
        effect_mode = normalize_image_effect_mode(effect_mode)
        width = max(1, int(width))
        aspect_ratio = img.shape[0] / max(1, img.shape[1])
        height_ratio = self._height_ratio_for_mode(render_mode)
        if height is None:
            height = int(width * aspect_ratio * height_ratio)
        height = max(1, int(height))

        sample_scale = self._normalize_sample_scale(sample_scale)
        working_width = max(1, int(round(width * sample_scale)))
        working_height = max(1, int(round(height * sample_scale)))

        prepared_img = self._prepare_image(
            img,
            width=working_width,
            height=working_height,
            display_mode=display_mode,
            height_ratio=height_ratio,
        )
        if (working_width, working_height) != (width, height):
            prepared_img = self._resize_image(
                prepared_img,
                width,
                height,
                prefer_pixel_art=sample_scale < 1.0,
            )

        prepared_img = self._apply_effect(
            prepared_img,
            effect_mode=effect_mode,
            palette=palette,
            threshold=threshold,
            edge_strength=edge_strength,
            invert=invert,
        )

        if render_mode == "pixel":
            return self._to_pixel(prepared_img, color=color)
        return self._to_ascii(prepared_img, color=color, charset=charset)

    def _prepare_image(
        self,
        img: np.ndarray,
        *,
        width: int,
        height: int,
        display_mode: str,
        height_ratio: float,
    ) -> np.ndarray:
        mode = normalize_image_display_mode(display_mode)
        if mode == "stretch":
            return self._resize_image(img, width, height)
        if mode == "fill":
            cropped = self._crop_to_fill(
                img,
                width=width,
                height=height,
                height_ratio=height_ratio,
            )
            return self._resize_image(cropped, width, height)

        fit_width, fit_height = self._fit_size(
            img,
            width=width,
            height=height,
            height_ratio=height_ratio,
        )
        return self._resize_image(img, fit_width, fit_height)

    def _fit_size(
        self,
        img: np.ndarray,
        *,
        width: int,
        height: int,
        height_ratio: float,
    ) -> tuple[int, int]:
        source_height, source_width = img.shape[:2]
        source_char_ratio = (source_height / max(1, source_width)) * height_ratio
        target_char_ratio = height / max(1, width)

        if source_char_ratio > target_char_ratio:
            fit_height = height
            fit_width = max(1, min(width, int(round(height / max(source_char_ratio, 1e-6)))))
        else:
            fit_width = width
            fit_height = max(
                1,
                min(height, int(round(width * source_char_ratio))),
            )

        return fit_width, fit_height

    def _crop_to_fill(
        self,
        img: np.ndarray,
        *,
        width: int,
        height: int,
        height_ratio: float,
    ) -> np.ndarray:
        source_height, source_width = img.shape[:2]
        source_ratio = source_height / max(1, source_width)
        target_ratio = height / max(1, width * height_ratio)

        if source_ratio > target_ratio:
            crop_height = max(1, min(source_height, int(round(source_width * target_ratio))))
            top = max(0, (source_height - crop_height) // 2)
            return img[top : top + crop_height, :, :]

        crop_width = max(1, min(source_width, int(round(source_height / max(target_ratio, 1e-6)))))
        left = max(0, (source_width - crop_width) // 2)
        return img[:, left : left + crop_width, :]

    def _resize_image(
        self,
        img: np.ndarray,
        width: int,
        height: int,
        *,
        prefer_pixel_art: bool = False,
    ) -> np.ndarray:
        source_height, source_width = img.shape[:2]
        if prefer_pixel_art and (width > source_width or height > source_height):
            interpolation = cv2.INTER_NEAREST
        elif width >= source_width or height >= source_height:
            interpolation = cv2.INTER_LINEAR
        else:
            interpolation = cv2.INTER_AREA
        return cv2.resize(img, (max(1, width), max(1, height)), interpolation=interpolation)

    def _apply_effect(
        self,
        img: np.ndarray,
        *,
        effect_mode: str,
        palette: object,
        threshold: float | None,
        edge_strength: float,
        invert: bool,
    ) -> np.ndarray:
        if effect_mode == "none":
            return img

        colors = self._resolve_palette(palette)
        if effect_mode == "silhouette":
            return self._effect_silhouette(
                img,
                foreground=colors["accent"],
                background=colors["background"],
                threshold=threshold,
                invert=invert,
            )
        if effect_mode == "edge":
            return self._effect_edge(
                img,
                foreground=colors["accent"],
                background=colors["background"],
                edge_strength=edge_strength,
                invert=invert,
            )
        if effect_mode == "duotone":
            return self._effect_duotone(
                img,
                low=colors["background"],
                high=colors["accent"],
                invert=invert,
            )
        if effect_mode == "dither":
            return self._effect_dither(
                img,
                low=colors["background"],
                high=colors["accent"],
                invert=invert,
            )
        if effect_mode == "posterize":
            return self._effect_posterize(img)
        return img

    def _effect_silhouette(
        self,
        img: np.ndarray,
        *,
        foreground: tuple[int, int, int],
        background: tuple[int, int, int],
        threshold: float | None,
        invert: bool,
    ) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        threshold_value = self._normalize_threshold(threshold, gray)
        mask = gray <= threshold_value
        if threshold is None:
            dark_count = int(mask.sum())
            light_count = int(mask.size - dark_count)
            mask = mask if dark_count <= light_count else ~mask
        if invert:
            mask = ~mask

        mask_u8 = mask.astype(np.uint8) * 255
        kernel = np.ones((3, 3), np.uint8)
        mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)
        mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)
        return self._compose_two_color(mask_u8 > 0, foreground=foreground, background=background)

    def _effect_edge(
        self,
        img: np.ndarray,
        *,
        foreground: tuple[int, int, int],
        background: tuple[int, int, int],
        edge_strength: float,
        invert: bool,
    ) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        strength = self._normalize_unit(edge_strength, 0.5)
        low = int(24 + (1.0 - strength) * 72)
        high = int(low * (2.2 + strength))
        edges = cv2.Canny(gray, low, high)
        if invert:
            edges = 255 - edges
        return self._compose_two_color(edges > 0, foreground=foreground, background=background)

    def _effect_duotone(
        self,
        img: np.ndarray,
        *,
        low: tuple[int, int, int],
        high: tuple[int, int, int],
        invert: bool,
    ) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
        if invert:
            gray = 1.0 - gray
        low_arr = np.array(low, dtype=np.float32)
        high_arr = np.array(high, dtype=np.float32)
        mixed = low_arr + (high_arr - low_arr) * gray[:, :, None]
        return np.clip(mixed, 0, 255).astype(np.uint8)

    def _effect_dither(
        self,
        img: np.ndarray,
        *,
        low: tuple[int, int, int],
        high: tuple[int, int, int],
        invert: bool,
    ) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
        if invert:
            gray = 1.0 - gray
        bayer = (
            np.array(
                [
                    [0, 8, 2, 10],
                    [12, 4, 14, 6],
                    [3, 11, 1, 9],
                    [15, 7, 13, 5],
                ],
                dtype=np.float32,
            )
            + 0.5
        ) / 16.0
        threshold_map = np.tile(
            bayer,
            (
                int(np.ceil(gray.shape[0] / 4)),
                int(np.ceil(gray.shape[1] / 4)),
            ),
        )[: gray.shape[0], : gray.shape[1]]
        return self._compose_two_color(gray >= threshold_map, foreground=high, background=low)

    def _effect_posterize(self, img: np.ndarray) -> np.ndarray:
        levels = 4
        scaled = np.floor(img.astype(np.float32) / 256.0 * levels)
        scaled = np.clip(scaled, 0, levels - 1)
        return np.clip((scaled / (levels - 1)) * 255.0, 0, 255).astype(np.uint8)

    def _compose_two_color(
        self,
        mask: np.ndarray,
        *,
        foreground: tuple[int, int, int],
        background: tuple[int, int, int],
    ) -> np.ndarray:
        result = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
        result[:, :] = np.array(background, dtype=np.uint8)
        result[mask] = np.array(foreground, dtype=np.uint8)
        return result

    def _normalize_threshold(self, threshold: float | None, gray: np.ndarray) -> int:
        if threshold is None:
            value, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return int(value)
        try:
            value = float(threshold)
        except (TypeError, ValueError):
            value = 128.0
        if 0.0 <= value <= 1.0:
            value *= 255.0
        return int(max(0, min(255, value)))

    def _normalize_unit(self, value: float, fallback: float) -> float:
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            normalized = fallback
        return max(0.0, min(1.0, normalized))

    def _resolve_palette(self, palette: object) -> dict[str, tuple[int, int, int]]:
        default = {
            "background": (0, 0, 0),
            "primary": (0, 255, 65),
            "accent": (255, 215, 0),
        }
        if isinstance(palette, dict):
            return {
                "background": self._parse_color(
                    palette.get("background") or palette.get("low") or palette.get("surface"),
                    default["background"],
                ),
                "primary": self._parse_color(
                    palette.get("primary") or palette.get("foreground"),
                    default["primary"],
                ),
                "accent": self._parse_color(
                    palette.get("accent") or palette.get("high") or palette.get("foreground"),
                    default["accent"],
                ),
            }
        if isinstance(palette, (list, tuple)) and len(palette) >= 2:
            return {
                "background": self._parse_color(palette[0], default["background"]),
                "primary": self._parse_color(palette[1], default["primary"]),
                "accent": self._parse_color(palette[-1], default["accent"]),
            }
        return default

    def _parse_color(
        self,
        value: object,
        fallback: tuple[int, int, int],
    ) -> tuple[int, int, int]:
        if isinstance(value, (list, tuple)) and len(value) >= 3:
            try:
                return tuple(max(0, min(255, int(channel))) for channel in value[:3])
            except (TypeError, ValueError):
                return fallback
        text = str(value or "").strip()
        if not text:
            return fallback
        if text.startswith("#"):
            text = text[1:]
        if len(text) == 3:
            text = "".join(char * 2 for char in text)
        if len(text) == 6:
            try:
                return (
                    int(text[0:2], 16),
                    int(text[2:4], 16),
                    int(text[4:6], 16),
                )
            except ValueError:
                return fallback
        return fallback

    def _to_ascii(self, img: np.ndarray, color: bool = True, charset: str = None) -> Text:
        """将图像数组转换为 ASCII 文本"""
        height, width, _ = img.shape
        result = Text()
        gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        chars = charset if charset else self.SIMPLE_CHARS
        char_len = len(chars)

        for y in range(height):
            for x in range(width):
                r, g, b = img[y, x]
                brightness = gray_img[y, x]
                char_index = int((brightness / 255) * (char_len - 1))
                char = chars[char_index]
                if color:
                    result.append(char, style=f"rgb({r},{g},{b})")
                else:
                    result.append(char)
            if y < height - 1:
                result.append("\n")

        return result

    def _to_pixel(self, img: np.ndarray, *, color: bool = True) -> Text:
        height, width, _ = img.shape
        if height % 2:
            img = np.concatenate([img, img[-1:, :, :]], axis=0)
            height += 1

        result = Text()
        for y in range(0, height, 2):
            for x in range(width):
                top_r, top_g, top_b = img[y, x]
                bottom_r, bottom_g, bottom_b = img[y + 1, x]
                if color:
                    result.append(
                        "▀",
                        style=(
                            f"rgb({top_r},{top_g},{top_b}) "
                            f"on rgb({bottom_r},{bottom_g},{bottom_b})"
                        ),
                    )
                else:
                    result.append("▀")
            if y < height - 2:
                result.append("\n")
        return result

    def _height_ratio_for_mode(self, render_mode: str) -> float:
        if render_mode == "pixel":
            return self.PIXEL_HEIGHT_RATIO
        return self.ASCII_CHAR_HEIGHT_RATIO

    def _normalize_sample_scale(self, sample_scale: float) -> float:
        try:
            value = float(sample_scale)
        except (TypeError, ValueError):
            value = 1.0
        return max(0.5, min(value, 2.0))

    def _make_file_cache_key(
        self,
        *,
        image_path: str,
        width: int,
        height: int | None,
        color: bool,
        charset: str | None,
        display_mode: str,
        render_mode: str,
        effect_mode: str,
        palette: object,
        threshold: float | None,
        edge_strength: float,
        invert: bool,
        sample_scale: float,
    ) -> tuple:
        path = Path(str(image_path)).expanduser()
        try:
            stat = path.stat()
            file_identity = (str(path.resolve()), stat.st_mtime_ns, stat.st_size)
        except OSError:
            file_identity = (str(path), None, None)
        return (
            file_identity,
            int(width),
            None if height is None else int(height),
            bool(color),
            charset or "",
            normalize_image_display_mode(display_mode),
            normalize_image_render_mode(render_mode),
            normalize_image_effect_mode(effect_mode),
            self._freeze_for_cache(palette),
            None if threshold is None else float(threshold),
            float(edge_strength),
            bool(invert),
            self._normalize_sample_scale(sample_scale),
        )

    def _cache_get(self, key: tuple) -> Text | None:
        cached = self._render_cache.get(key)
        if cached is None:
            return None
        self._render_cache.move_to_end(key)
        return self._copy_text(cached)

    def _cache_set(self, key: tuple, value: Text) -> None:
        self._render_cache[key] = self._copy_text(value)
        self._render_cache.move_to_end(key)
        while len(self._render_cache) > self.MAX_CACHE_ITEMS:
            self._render_cache.popitem(last=False)

    def _copy_text(self, text: Text) -> Text:
        try:
            return text.copy()
        except Exception:
            return Text(text.plain, style=text.style)

    def _freeze_for_cache(self, value: object) -> object:
        if isinstance(value, dict):
            return tuple(
                (str(key), self._freeze_for_cache(item))
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            )
        if isinstance(value, (list, tuple)):
            return tuple(self._freeze_for_cache(item) for item in value)
        return value

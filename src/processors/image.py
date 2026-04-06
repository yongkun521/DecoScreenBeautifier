import cv2
import numpy as np
from PIL import Image
from rich.text import Text

from core.layout_config import (
    DEFAULT_IMAGE_DISPLAY_MODE,
    DEFAULT_IMAGE_RENDER_MODE,
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

    def process_image(
        self,
        image_path: str,
        width: int,
        height: int = None,
        color: bool = True,
        charset: str = None,
        display_mode: str = DEFAULT_IMAGE_DISPLAY_MODE,
        render_mode: str = DEFAULT_IMAGE_RENDER_MODE,
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
        :param sample_scale: 仅影响采样密度，不改变最终字符占位
        :return: Rich Text 对象
        """
        try:
            pil_image = Image.open(image_path)
            pil_image = pil_image.convert("RGB")
            img = np.array(pil_image)
            return self.process_array(
                img,
                width=width,
                height=height,
                color=color,
                charset=charset,
                display_mode=display_mode,
                render_mode=render_mode,
                sample_scale=sample_scale,
            )
        except Exception as e:
            return Text(f"Image Error: {e}", style="red")

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
        sample_scale: float = 1.0,
    ) -> Text:
        render_mode = normalize_image_render_mode(render_mode)
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

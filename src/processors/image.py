import cv2
import numpy as np
from PIL import Image
from rich.text import Text

from core.layout_config import DEFAULT_IMAGE_DISPLAY_MODE, normalize_image_display_mode


class ImageProcessor:
    """
    图像处理器
    负责将位图转换为 ASCII/ANSI 字符画
    """

    # 字符集：从暗到亮
    ASCII_CHARS = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
    
    # 简化的字符集 (效果可能更清晰)
    SIMPLE_CHARS = "@%#*+=-:. "

    CHAR_HEIGHT_RATIO = 0.5

    def process_image(
        self,
        image_path: str,
        width: int,
        height: int = None,
        color: bool = True,
        charset: str = None,
        display_mode: str = DEFAULT_IMAGE_DISPLAY_MODE,
    ) -> Text:
        """
        处理图像并返回 Rich Text 对象
        
        :param image_path: 图片路径
        :param width: 目标宽度 (字符数)
        :param height: 目标高度 (字符数)，如果为 None 则按比例计算
        :param color: 是否使用 ANSI 颜色
        :param display_mode: 拉伸 / 填充 / 等比缩放
        :return: Rich Text 对象
        """
        try:
            # 使用 PIL 读取图像 (支持更多格式)
            pil_image = Image.open(image_path)
            # 转换为 RGB
            pil_image = pil_image.convert("RGB")
            # 转换为 numpy 数组以便 OpenCV 处理
            img = np.array(pil_image)
            # OpenCV 默认为 BGR，PIL 为 RGB，如果后续用 cv2 处理颜色需注意，这里直接用 RGB
            
            width = max(1, int(width))

            # 计算目标高度 (字符的高宽比通常是 2:1，所以高度要乘 0.5)
            aspect_ratio = img.shape[0] / img.shape[1]
            if height is None:
                height = int(width * aspect_ratio * self.CHAR_HEIGHT_RATIO)
            height = max(1, int(height))

            resized_img = self._prepare_image(
                img,
                width=width,
                height=height,
                display_mode=display_mode,
            )
            
            return self._to_ascii(resized_img, color, charset)
            
        except Exception as e:
            return Text(f"Image Error: {e}", style="red")

    def _prepare_image(
        self,
        img: np.ndarray,
        *,
        width: int,
        height: int,
        display_mode: str,
    ) -> np.ndarray:
        mode = normalize_image_display_mode(display_mode)
        if mode == "stretch":
            return self._resize_image(img, width, height)
        if mode == "fill":
            cropped = self._crop_to_fill(img, width=width, height=height)
            return self._resize_image(cropped, width, height)

        fit_width, fit_height = self._fit_size(img, width=width, height=height)
        return self._resize_image(img, fit_width, fit_height)

    def _fit_size(self, img: np.ndarray, *, width: int, height: int) -> tuple[int, int]:
        source_height, source_width = img.shape[:2]
        source_char_ratio = (source_height / max(1, source_width)) * self.CHAR_HEIGHT_RATIO
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

    def _crop_to_fill(self, img: np.ndarray, *, width: int, height: int) -> np.ndarray:
        source_height, source_width = img.shape[:2]
        source_ratio = source_height / max(1, source_width)
        target_ratio = height / max(1, width * self.CHAR_HEIGHT_RATIO)

        if source_ratio > target_ratio:
            crop_height = max(1, min(source_height, int(round(source_width * target_ratio))))
            top = max(0, (source_height - crop_height) // 2)
            return img[top : top + crop_height, :, :]

        crop_width = max(1, min(source_width, int(round(source_height / max(target_ratio, 1e-6)))))
        left = max(0, (source_width - crop_width) // 2)
        return img[:, left : left + crop_width, :]

    def _resize_image(self, img: np.ndarray, width: int, height: int) -> np.ndarray:
        source_height, source_width = img.shape[:2]
        if width >= source_width or height >= source_height:
            interpolation = cv2.INTER_LINEAR
        else:
            interpolation = cv2.INTER_AREA
        return cv2.resize(img, (max(1, width), max(1, height)), interpolation=interpolation)

    def _to_ascii(self, img: np.ndarray, color: bool = True, charset: str = None) -> Text:
        """将图像数组转换为 ASCII 文本"""
        height, width, _ = img.shape
        result = Text()
        
        # 转换为灰度图用于选择字符
        gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # 字符集长度
        chars = charset if charset else self.SIMPLE_CHARS
        char_len = len(chars)
        
        for y in range(height):
            for x in range(width):
                # 获取像素颜色
                r, g, b = img[y, x]
                # 获取亮度
                brightness = gray_img[y, x]
                # 映射到字符
                char_index = int((brightness / 255) * (char_len - 1))
                char = chars[char_index]
                
                # 添加到 Text 对象
                if color:
                    result.append(char, style=f"rgb({r},{g},{b})")
                else:
                    result.append(char)
            result.append("\n")
            
        return result

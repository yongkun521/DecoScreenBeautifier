import cv2
import numpy as np
from PIL import Image
from rich.text import Text

class ImageProcessor:
    """
    图像处理器
    负责将位图转换为 ASCII/ANSI 字符画
    """

    # 字符集：从暗到亮
    ASCII_CHARS = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
    
    # 简化的字符集 (效果可能更清晰)
    SIMPLE_CHARS = "@%#*+=-:. "

    def __init__(self):
        pass

    def process_image(self, image_path: str, width: int, height: int = None, color: bool = True) -> Text:
        """
        处理图像并返回 Rich Text 对象
        
        :param image_path: 图片路径
        :param width: 目标宽度 (字符数)
        :param height: 目标高度 (字符数)，如果为 None 则按比例计算
        :param color: 是否使用 ANSI 颜色
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
            
            # 计算目标高度 (字符的高宽比通常是 2:1，所以高度要乘 0.5)
            aspect_ratio = img.shape[0] / img.shape[1]
            if height is None:
                height = int(width * aspect_ratio * 0.5)
            
            # 调整大小
            resized_img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
            
            return self._to_ascii(resized_img, color)
            
        except Exception as e:
            return Text(f"Image Error: {e}", style="red")

    def _to_ascii(self, img: np.ndarray, color: bool = True) -> Text:
        """将图像数组转换为 ASCII 文本"""
        height, width, _ = img.shape
        result = Text()
        
        # 转换为灰度图用于选择字符
        gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # 字符集长度
        char_len = len(self.SIMPLE_CHARS)
        
        for y in range(height):
            for x in range(width):
                # 获取像素颜色
                r, g, b = img[y, x]
                # 获取亮度
                brightness = gray_img[y, x]
                # 映射到字符
                char_index = int((brightness / 255) * (char_len - 1))
                char = self.SIMPLE_CHARS[char_index]
                
                # 添加到 Text 对象
                if color:
                    result.append(char, style=f"rgb({r},{g},{b})")
                else:
                    result.append(char)
            result.append("\n")
            
        return result

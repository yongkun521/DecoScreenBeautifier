import random
from rich.text import Text

class GlitchEffect:
    """
    故障艺术特效处理器
    """

    @staticmethod
    def apply_glitch(text_obj: Text, intensity: float = 0.1) -> Text:
        """
        对 Rich Text 对象应用故障效果
        :param text_obj: 原始 Text 对象
        :param intensity: 故障强度 (0.0 - 1.0)
        :return: 处理后的 Text 对象 (副本)
        """
        result = text_obj.copy()
        plain_text = result.plain
        length = len(plain_text)
        
        # 随机字符替换
        num_glitches = int(length * intensity * 0.1)
        for _ in range(num_glitches):
            idx = random.randint(0, length - 1)
            if plain_text[idx] != "\n":
                # 随机替换为特殊字符
                glitch_char = random.choice("!@#$%^&*()_+-=[]{}|;':,./<>?")
                # 由于 Rich Text 的不可变性，这里操作比较复杂，简化为只修改样式或重建
                # 这里为了性能，我们暂不直接修改字符，而是修改颜色/样式
                
                # 随机颜色偏移
                style_idx = random.randint(0, len(result.spans) - 1) if result.spans else -1
                if style_idx >= 0:
                    span = result.spans[style_idx]
                    # 这里需要更复杂的 span 操作，暂时略过
                    pass

        return result

    @staticmethod
    def apply_scanline(text_str: str, line_index: int) -> str:
        """
        应用扫描线效果 (简单的亮度变化或字符替换)
        """
        # 实际在 TUI 中很难做像素级扫描线，通常用高亮行模拟
        return text_str

    @staticmethod
    def random_noise(width: int, height: int, density: float = 0.1) -> str:
        """生成噪点背景字符"""
        chars = " .`,"
        lines = []
        for _ in range(height):
            line = ""
            for _ in range(width):
                if random.random() < density:
                    line += random.choice(chars)
                else:
                    line += " "
            lines.append(line)
        return "\n".join(lines)

import numpy as np
import pyaudio
import random
from rich.text import Text
from rich.align import Align
from rich.table import Table
from .base import BaseWidget

class AudioVisualizer(BaseWidget):
    """
    高级音频可视化组件
    显示对称的、带渐变色的音频频谱
    """

    DEFAULT_CSS = """
    AudioVisualizer {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        # 提高采样频率以获得更丝滑的体验
        super().__init__(title="NEURAL AUDIO LINK", update_interval=0.03, **kwargs)
        
        self.chunk = 1024
        self.rate = 44100
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.use_mock = False
        self.prev_data = np.zeros(16)  # 用于平滑处理
        
        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
        except Exception:
            self.use_mock = True

    def update_content(self) -> None:
        """读取音频数据并更新显示"""
        data_int = None
        
        if not self.use_mock and self.stream:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                data_int = np.frombuffer(data, dtype=np.int16)
            except Exception:
                self.use_mock = True
        
        if self.use_mock:
            # 模拟数据：生成更自然的波动
            data_int = np.random.randint(-16384, 16383, self.chunk)

        if data_int is not None and len(data_int) > 0:
            # 执行 FFT
            fft_data = np.abs(np.fft.fft(data_int)[:16])
            # 归一化并应用对数缩放，使视觉效果更明显
            max_val = np.max(fft_data) if np.max(fft_data) > 0 else 1
            normalized_data = (fft_data / max_val) * 10
            
            # 平滑处理：结合上一帧数据
            smooth_data = 0.6 * normalized_data + 0.4 * self.prev_data
            self.prev_data = smooth_data
            
            self.update(self._render_enhanced_spectrum(smooth_data))

    def _render_enhanced_spectrum(self, data):
        """渲染增强版频谱图（对称且带颜色）"""
        # 我们使用 16 个频段，将其镜像为 32 个
        mirrored_data = np.concatenate([np.flip(data), data])
        
        preset = self.get_visual_preset()
        chars = preset.get("spectrum", [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"])
        low_color = self.get_style_color("audio_low", "cyan")
        mid_color = self.get_style_color("audio_mid", "blue")
        high_color = self.get_style_color("audio_high", "magenta")
        
        result = Text()
        for i, val in enumerate(mirrored_data):
            height = int(val)
            height = max(0, min(height, len(chars) - 1))
            
            # 根据频率（位置）应用渐变色
            # 两边青色，中间紫色
            dist_from_center = abs(i - 15.5) / 16.0
            if dist_from_center < 0.3:
                color = high_color
            elif dist_from_center < 0.6:
                color = mid_color
            else:
                color = low_color
                
            # 添加闪烁效果
            style = f"bold {color}"
            if height > 7 and random.random() < 0.2:
                style += " blink"
                
            result.append(chars[height] * 2 + " ", style=style)
            
        return Align.center(
            Text.assemble(
                result, "\n",
                self.glitch_text(">>> AUDIO SIGNAL SYNCHRONIZED <<<", probability=0.02)
            ),
            vertical="middle"
        )

    def on_unmount(self) -> None:
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

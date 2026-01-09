import numpy as np
import pyaudio
import random
from rich.text import Text
from rich.align import Align
from rich.bar import Bar
from .base import BaseWidget

class AudioVisualizer(BaseWidget):
    """
    音频可视化组件
    显示音频频谱
    """

    DEFAULT_CSS = """
    AudioVisualizer {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        # 音频更新频率需要较高，例如 20fps -> 0.05s
        super().__init__(title="AUDIO VISUALIZER", update_interval=0.05, **kwargs)
        
        self.chunk = 1024  # 每次读取的音频帧数
        self.rate = 44100  # 采样率
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.use_mock = False
        
        try:
            # 尝试打开默认输入流
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
        except Exception as e:
            # 如果失败（例如没有麦克风），则使用模拟模式
            self.use_mock = True
            self.log(f"Audio device init failed, using mock mode: {e}")

    def update_content(self) -> None:
        """读取音频数据并更新显示"""
        data_int = None
        
        if not self.use_mock and self.stream:
            try:
                # 读取音频数据
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                data_int = np.frombuffer(data, dtype=np.int16)
            except Exception:
                self.use_mock = True
        
        if self.use_mock:
            # 模拟数据：生成随机频谱
            data_int = np.random.randint(-32768, 32767, self.chunk)

        # 计算 FFT
        # 取前 32 个频率分量进行显示
        if data_int is not None and len(data_int) > 0:
            fft_data = np.abs(np.fft.fft(data_int)[:32])
            # 归一化
            max_val = np.max(fft_data) if np.max(fft_data) > 0 else 1
            normalized_data = (fft_data / max_val) * 8  # 假设高度为 8 字符
            
            self.update(self._render_spectrum(normalized_data))

    def _render_spectrum(self, data):
        """渲染频谱图"""
        bars = []
        chars = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        
        # 将数据转换为柱状图字符
        # 这里为了演示，简单地将数值映射到字符高度
        spectrum_str = ""
        for val in data:
            height = int(val)
            height = max(0, min(height, len(chars) - 1))
            spectrum_str += chars[height]
            
        # 让频谱图看起来更宽一些
        full_spectrum = ""
        for char in spectrum_str:
            full_spectrum += char * 2 + " "
            
        return Align.center(Text(full_spectrum, style="bold cyan"), vertical="middle")

    def on_unmount(self) -> None:
        """组件卸载时清理资源"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

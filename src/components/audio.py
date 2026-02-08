import random
import os
import sys
import threading

import numpy as np
from rich.align import Align
from rich.text import Text

from .base import BaseWidget

try:
    from utils.startup_trace import trace_startup as _trace_startup
except Exception:
    def _trace_startup(message: str) -> None:
        return None

try:
    import pyaudio
except Exception:
    pyaudio = None


class AudioVisualizer(BaseWidget):
    """高级音频可视化组件。"""

    DEFAULT_CSS = """
    AudioVisualizer {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(title="NEURAL AUDIO LINK", update_interval=0.03, **kwargs)

        self.chunk = 1024
        self.rate = 44100
        self.stream = None
        self.p = None
        self.use_mock = False
        self.prev_data = np.zeros(16)
        self._init_lock = threading.Lock()
        self._init_thread = None
        self._audio_init_done = False
        self._audio_init_started = False

        if pyaudio is None:
            self.use_mock = True
            self._audio_init_done = True
            return

        enable_audio_capture = os.environ.get("DSB_ENABLE_AUDIO_CAPTURE", "")
        if getattr(sys, "frozen", False) and enable_audio_capture.lower() not in {
            "1",
            "true",
            "yes",
        }:
            self.use_mock = True
            self._audio_init_done = True
            _trace_startup("audio: frozen mode defaults to mock capture")

    def on_mount(self) -> None:
        self._start_audio_init_thread()
        super().on_mount()

    def _start_audio_init_thread(self) -> None:
        if self.use_mock or self._audio_init_started or self._audio_init_done:
            return

        self._audio_init_started = True

        def _worker() -> None:
            with self._init_lock:
                try:
                    self.p = pyaudio.PyAudio()
                    self.stream = self.p.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk,
                    )
                    _trace_startup("audio: stream initialized")
                except Exception as exc:
                    self.use_mock = True
                    _trace_startup(
                        f"audio: stream init failed, fallback mock ({type(exc).__name__}: {exc})"
                    )
                finally:
                    self._audio_init_done = True

        self._init_thread = threading.Thread(target=_worker, daemon=True)
        self._init_thread.start()

    def update_content(self) -> None:
        data_int = None

        if not self.use_mock and self.stream:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                data_int = np.frombuffer(data, dtype=np.int16)
            except Exception:
                self.use_mock = True

        if self.use_mock:
            data_int = np.random.randint(-16384, 16383, self.chunk)
        elif not self._audio_init_done:
            text = Text("Audio capture initializing...", style="yellow")
            self.update(Align.center(text, vertical="middle"))
            return

        if data_int is not None and len(data_int) > 0:
            fft_data = np.abs(np.fft.fft(data_int)[:16])
            max_val = np.max(fft_data) if np.max(fft_data) > 0 else 1
            normalized_data = (fft_data / max_val) * 10

            smooth_data = 0.6 * normalized_data + 0.4 * self.prev_data
            self.prev_data = smooth_data

            self.update(self._render_enhanced_spectrum(smooth_data))

    def _render_enhanced_spectrum(self, data):
        mirrored_data = np.concatenate([np.flip(data), data])

        preset = self.get_visual_preset()
        chars = preset.get("spectrum", [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇"])
        low_color = self.get_style_color("audio_low", "cyan")
        mid_color = self.get_style_color("audio_mid", "blue")
        high_color = self.get_style_color("audio_high", "magenta")

        result = Text()
        for i, val in enumerate(mirrored_data):
            height = int(val)
            height = max(0, min(height, len(chars) - 1))

            dist_from_center = abs(i - 15.5) / 16.0
            if dist_from_center < 0.3:
                color = high_color
            elif dist_from_center < 0.6:
                color = mid_color
            else:
                color = low_color

            style = f"bold {color}"
            if height > 7 and random.random() < 0.2:
                style += " blink"

            result.append(chars[height] * 2 + " ", style=style)

        return Align.center(
            Text.assemble(
                result,
                "\n",
                self.glitch_text(">>> AUDIO SIGNAL SYNCHRONIZED <<<", probability=0.02),
            ),
            vertical="middle",
        )

    def on_unmount(self) -> None:
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p is not None:
            self.p.terminate()

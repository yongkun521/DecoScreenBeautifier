from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil


@dataclass(frozen=True)
class GuiPerfSample:
    timestamp: float
    elapsed: float
    fps: float
    cpu_percent: float
    memory_mb: float
    frame_time_ms: float
    grid_width: int
    grid_height: int


class GuiPerformanceMonitor:
    def __init__(self, interval: float = 1.0, log_path: Optional[str] = None):
        self.interval = max(0.2, float(interval))
        self.log_path = Path(log_path) if log_path else None
        self._process = psutil.Process()
        self._last_sample = time.perf_counter()
        self._frames_since_sample = 0
        self._frame_time_sum = 0.0
        self._latest_grid_width = 0
        self._latest_grid_height = 0
        self._running = False

    def start(self) -> None:
        self._process.cpu_percent(None)
        self._last_sample = time.perf_counter()
        self._frames_since_sample = 0
        self._frame_time_sum = 0.0
        self._running = True

    def stop(self) -> None:
        self._running = False

    def record_frame(self, frame_elapsed: float, *, grid_width: int, grid_height: int) -> Optional[GuiPerfSample]:
        if not self._running:
            return None
        self._frames_since_sample += 1
        self._frame_time_sum += max(0.0, float(frame_elapsed))
        self._latest_grid_width = max(0, int(grid_width))
        self._latest_grid_height = max(0, int(grid_height))

        now = time.perf_counter()
        elapsed = now - self._last_sample
        if elapsed < self.interval:
            return None

        fps = self._frames_since_sample / elapsed if elapsed > 0 else 0.0
        frame_time_ms = (
            (self._frame_time_sum / self._frames_since_sample) * 1000
            if self._frames_since_sample > 0
            else 0.0
        )
        cpu = self._process.cpu_percent(None)
        mem = self._process.memory_info().rss / (1024 * 1024)
        sample = GuiPerfSample(
            timestamp=time.time(),
            elapsed=elapsed,
            fps=round(fps, 2),
            cpu_percent=round(cpu, 2),
            memory_mb=round(mem, 2),
            frame_time_ms=round(frame_time_ms, 3),
            grid_width=self._latest_grid_width,
            grid_height=self._latest_grid_height,
        )
        self._write_sample(sample)

        self._last_sample = now
        self._frames_since_sample = 0
        self._frame_time_sum = 0.0
        return sample

    def _write_sample(self, sample: GuiPerfSample) -> None:
        if not self.log_path:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(sample.__dict__, ensure_ascii=False) + "\n")

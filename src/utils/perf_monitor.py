from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil


@dataclass(frozen=True)
class PerfSample:
    timestamp: float
    elapsed: float
    fps: float
    cpu_percent: float
    memory_mb: float


class PerformanceMonitor:
    def __init__(self, app, interval: float = 1.0, log_path: Optional[str] = None):
        self.app = app
        self.interval = max(0.2, float(interval))
        self.log_path = Path(log_path) if log_path else None
        self._process = psutil.Process()
        self._timer = None
        self._frame_counter = 0
        self._last_frame_counter = 0
        self._last_sample = time.perf_counter()
        self._original_refresh = None

    def start(self) -> None:
        self._hook_refresh()
        self._process.cpu_percent(None)
        self._timer = self.app.set_interval(self.interval, self._sample)

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self._restore_refresh()

    def _hook_refresh(self) -> None:
        if getattr(self.app, "_perf_refresh_hooked", False):
            return
        original = self.app.refresh

        def wrapped(*args, **kwargs):
            self._frame_counter += 1
            return original(*args, **kwargs)

        self.app.refresh = wrapped
        self._original_refresh = original
        self.app._perf_refresh_hooked = True

    def _restore_refresh(self) -> None:
        if self._original_refresh:
            self.app.refresh = self._original_refresh
            self._original_refresh = None
            self.app._perf_refresh_hooked = False

    def _sample(self) -> None:
        now = time.perf_counter()
        elapsed = now - self._last_sample
        frames = self._frame_counter - self._last_frame_counter
        fps = frames / elapsed if elapsed > 0 else 0.0
        cpu = self._process.cpu_percent(None)
        mem = self._process.memory_info().rss / (1024 * 1024)
        sample = PerfSample(
            timestamp=time.time(),
            elapsed=elapsed,
            fps=round(fps, 2),
            cpu_percent=round(cpu, 2),
            memory_mb=round(mem, 2),
        )
        self._last_sample = now
        self._last_frame_counter = self._frame_counter
        setattr(self.app, "performance_stats", sample)
        self._write_sample(sample)

    def _write_sample(self, sample: PerfSample) -> None:
        if not self.log_path:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(sample.__dict__, ensure_ascii=False) + "\n")

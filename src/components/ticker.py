import os
import socket
import time

import psutil
from rich.align import Align
from rich.text import Text

from .base import BaseWidget


class InfoTicker(BaseWidget):
    """
    滚动信息条组件
    展示系统关键指标与主机信息
    """

    DEFAULT_CSS = """
    InfoTicker {
        height: 100%;
        width: 100%;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(title="DATA TICKER", update_interval=0.2, **kwargs)
        self._offset = 0
        self._last_refresh = 0.0
        self._cached_message = ""

    def update_content(self) -> None:
        now = time.time()
        if now - self._last_refresh > 1.2 or not self._cached_message:
            self._cached_message = self._build_message()
            self._last_refresh = now
        width = max(10, self.size.width - 2)
        line = self._scroll_text(self._cached_message, width)
        color = self.get_style_color("ticker", "bright_cyan")
        ticker_text = Text(line, style=color)
        if self.uses_light_chrome():
            self.update(self.compose_widget_content(ticker_text, footer="sys feed"))
        else:
            self.update(Align.center(ticker_text, vertical="middle"))
        self._offset += 1

    def _scroll_text(self, message: str, width: int) -> str:
        if not message:
            return " " * width
        pad = "   "
        scroll = f"{message}{pad}"
        if width >= len(scroll):
            return scroll.ljust(width)
        offset = self._offset % len(scroll)
        return (scroll + scroll)[offset : offset + width]

    def _build_message(self) -> str:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        disk = self._disk_usage()
        uptime = self._format_uptime(time.time() - psutil.boot_time())
        host = socket.gethostname()
        ip = self._safe_ip()
        parts = [
            f"UP {uptime}",
            f"CPU {cpu:.0f}%",
            f"MEM {mem:.0f}%",
            f"DSK {disk:.0f}%",
            f"HOST {host}",
        ]
        if ip:
            parts.append(f"IP {ip}")
        return " • ".join(parts)

    def _disk_usage(self) -> float:
        root = "C:\\" if os.name == "nt" else os.path.abspath(os.sep)
        try:
            return psutil.disk_usage(root).percent
        except Exception:
            return 0.0

    def _safe_ip(self) -> str:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            return ""
        if ip.startswith("127."):
            return ""
        return ip

    def _format_uptime(self, seconds: float) -> str:
        total = max(0, int(seconds))
        days, rem = divmod(total, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        if days:
            return f"{days}d {hours}h"
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

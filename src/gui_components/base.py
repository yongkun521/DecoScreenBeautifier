from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol
import random

from rich.text import Text

from core.renderer import ColorRGB, RenderGrid, TextStyle, render_rich_to_grid


@dataclass(frozen=True)
class RenderContext:
    frame_index: int
    now_ts: float
    global_scale: float
    style_preset: dict
    visual_preset: dict


class GuiComponent(Protocol):
    id: str

    def update(self, now_ts: float) -> None:
        ...

    def render(self, width: int, height: int, ctx: RenderContext) -> RenderGrid:
        ...


class GuiComponentBase:
    def __init__(
        self,
        component_id: str,
        *,
        title: str = "",
        update_interval: float = 1.0,
    ) -> None:
        self.id = component_id
        self.title = title
        self.update_interval = update_interval
        self._last_update: float = 0.0
        self._renderable = Text("")
        self._visual_preset: dict = {}
        self._style_preset: dict = {}

    def set_visual_preset(self, preset: dict) -> None:
        self._visual_preset = preset or {}

    def set_style_preset(self, preset: dict) -> None:
        self._style_preset = preset or {}

    def get_visual_preset(self) -> dict:
        return self._visual_preset or {}

    def get_style_preset(self) -> dict:
        return self._style_preset or {}

    def get_style_color(self, key: str, default: str) -> str:
        preset = self.get_style_preset()
        colors = preset.get("colors", {}) if isinstance(preset, dict) else {}
        return colors.get(key, default)

    def update(self, now_ts: float) -> None:
        if self.update_interval <= 0:
            self.update_content()
            self._last_update = now_ts
            return
        if self._last_update <= 0 or now_ts - self._last_update >= self.update_interval:
            self.update_content()
            self._last_update = now_ts

    def update_content(self) -> None:
        raise NotImplementedError

    def set_renderable(self, renderable: object) -> None:
        self._renderable = renderable

    def render(self, width: int, height: int, ctx: RenderContext) -> RenderGrid:
        base_style = self._base_style(ctx)
        return render_rich_to_grid(
            self._renderable,
            width,
            height,
            base_style=base_style,
        )

    def _base_style(self, ctx: RenderContext) -> Optional[TextStyle]:
        fg_hex = self.get_style_color("primary", "#00FF41")
        fg = ColorRGB.from_hex(fg_hex) if isinstance(fg_hex, str) else None
        return TextStyle(fg=fg)

    def glitch_text(self, text: str, probability: float = 0.05) -> Text:
        glitch_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = Text()
        for char in text:
            if char != " " and random.random() < probability:
                result.append(random.choice(glitch_chars), style="blink bold magenta")
            else:
                result.append(char)
        return result

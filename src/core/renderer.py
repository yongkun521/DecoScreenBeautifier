from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from rich.console import Console
from rich.segment import Segment
from rich.style import Style


@dataclass(frozen=True)
class ColorRGB:
    r: int
    g: int
    b: int
    a: int = 255

    @classmethod
    def from_hex(cls, value: str) -> Optional["ColorRGB"]:
        text = value.strip().lstrip("#")
        if len(text) != 6:
            return None
        try:
            return cls(
                int(text[0:2], 16),
                int(text[2:4], 16),
                int(text[4:6], 16),
            )
        except ValueError:
            return None


def _rich_color_to_rgb(color: Optional[Any]) -> Optional[ColorRGB]:
    if color is None:
        return None
    triplet = None
    getter = getattr(color, "get_truecolor", None)
    if callable(getter):
        try:
            triplet = getter()
        except Exception:
            triplet = None
    if triplet is None:
        triplet = getattr(color, "triplet", None)
    if triplet is not None:
        return ColorRGB(triplet.red, triplet.green, triplet.blue)
    hex_value = getattr(color, "hex", None)
    if isinstance(hex_value, str):
        return ColorRGB.from_hex(hex_value)
    return None


@dataclass(frozen=True)
class TextStyle:
    fg: Optional[ColorRGB] = None
    bg: Optional[ColorRGB] = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    blink: bool = False
    reverse: bool = False
    dim: bool = False
    strike: bool = False
    font: Optional[str] = None

    @classmethod
    def from_rich(cls, style: Optional[Style], *, font: Optional[str] = None) -> "TextStyle":
        if style is None:
            return cls(font=font)
        return cls(
            fg=_rich_color_to_rgb(style.color),
            bg=_rich_color_to_rgb(style.bgcolor),
            bold=bool(style.bold),
            italic=bool(style.italic),
            underline=bool(style.underline),
            blink=bool(style.blink),
            reverse=bool(style.reverse),
            dim=bool(style.dim),
            strike=bool(style.strike),
            font=font,
        )

    def with_base(self, base: Optional["TextStyle"]) -> "TextStyle":
        if base is None:
            return self
        return TextStyle(
            fg=self.fg or base.fg,
            bg=self.bg or base.bg,
            bold=self.bold or base.bold,
            italic=self.italic or base.italic,
            underline=self.underline or base.underline,
            blink=self.blink or base.blink,
            reverse=self.reverse or base.reverse,
            dim=self.dim or base.dim,
            strike=self.strike or base.strike,
            font=self.font or base.font,
        )


@dataclass(frozen=True)
class RenderCell:
    char: str = " "
    style: TextStyle = field(default_factory=TextStyle)


@dataclass
class RenderGrid:
    width: int
    height: int
    cells: list[list[RenderCell]] = field(default_factory=list)

    @classmethod
    def empty(cls, width: int, height: int, style: Optional[TextStyle] = None) -> "RenderGrid":
        base_style = style or TextStyle()
        cells = [
            [RenderCell(" ", base_style) for _ in range(width)] for _ in range(height)
        ]
        return cls(width=width, height=height, cells=cells)

    @classmethod
    def from_segments(
        cls,
        segments: Iterable[Segment],
        width: int,
        height: int,
        *,
        base_style: Optional[TextStyle] = None,
        font: Optional[str] = None,
    ) -> "RenderGrid":
        grid = cls.empty(width, height, base_style)
        if width <= 0 or height <= 0:
            return grid
        x = 0
        y = 0
        for segment in segments:
            text = segment.text
            if not text:
                continue
            style = TextStyle.from_rich(segment.style, font=font).with_base(base_style)
            for char in text:
                if char == "\n":
                    x = 0
                    y += 1
                    if y >= height:
                        return grid
                    continue
                if char == "\r":
                    continue
                if x >= width:
                    x = 0
                    y += 1
                    if y >= height:
                        return grid
                if 0 <= x < width and 0 <= y < height:
                    grid.cells[y][x] = RenderCell(char, style)
                x += 1
                if y >= height:
                    return grid
        return grid

    def set_cell(self, x: int, y: int, cell: RenderCell) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.cells[y][x] = cell

    def to_plain_text(self) -> str:
        return "\n".join("".join(cell.char for cell in row) for row in self.cells)


def render_rich_to_grid(
    renderable: Any,
    width: int,
    height: int,
    *,
    base_style: Optional[TextStyle] = None,
    font: Optional[str] = None,
    console: Optional[Console] = None,
) -> RenderGrid:
    if renderable is None:
        return RenderGrid.empty(width, height, base_style)
    active_console = console or Console(
        width=width,
        height=height,
        color_system="truecolor",
        force_terminal=True,
        record=False,
        soft_wrap=False,
    )
    options = active_console.options
    if hasattr(options, "update"):
        options = options.update(width=width, height=height)
    segments = list(active_console.render(renderable, options))
    return RenderGrid.from_segments(
        segments,
        width,
        height,
        base_style=base_style,
        font=font,
    )


def render_textual_widget(
    widget: Any,
    width: int,
    height: int,
    *,
    base_style: Optional[TextStyle] = None,
    font: Optional[str] = None,
    console: Optional[Console] = None,
) -> RenderGrid:
    if widget is None:
        return RenderGrid.empty(width, height, base_style)
    renderable = widget
    render_method = getattr(widget, "render", None)
    if callable(render_method):
        try:
            renderable = render_method()
        except Exception:
            renderable = getattr(widget, "renderable", widget)
    return render_rich_to_grid(
        renderable,
        width,
        height,
        base_style=base_style,
        font=font,
        console=console,
    )

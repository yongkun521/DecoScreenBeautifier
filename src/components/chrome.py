from __future__ import annotations

from rich.console import Group
from rich.text import Text


LIGHT_VARIANTS = {
    "variant-rail",
    "variant-corner",
    "variant-ribbon",
    "variant-hero",
}


def build_light_chrome(
    body,
    *,
    title: str,
    width: int,
    variant: str,
    line_color: str,
    line_dim_color: str,
    accent_color: str,
    muted_color: str,
    label_bg: str,
    footer: str | Text | None = None,
) -> Group:
    items = [_build_header(title, width=max(8, width), variant=variant, line_color=line_color, line_dim_color=line_dim_color, accent_color=accent_color, label_bg=label_bg)]
    items.append(body)
    footer_line = _build_footer(
        footer,
        width=max(8, width),
        variant=variant,
        line_dim_color=line_dim_color,
        muted_color=muted_color,
    )
    if footer_line is not None:
        items.append(footer_line)
    return Group(*items)


def _build_header(
    title: str,
    *,
    width: int,
    variant: str,
    line_color: str,
    line_dim_color: str,
    accent_color: str,
    label_bg: str,
) -> Text:
    chip = Text()
    chip.append(" ", style=f"on {label_bg}")
    chip.append(title.upper(), style=f"bold {accent_color} on {label_bg}")
    chip.append(" ", style=f"on {label_bg}")
    chip_width = len(chip.plain)

    if variant == "variant-hero":
        return chip

    if variant == "variant-ribbon":
        left = Text("▌", style=line_color)
        right_fill = max(0, width - 1 - chip_width)
        return Text.assemble(left, chip, ("▐" + "═" * max(0, right_fill - 1), line_color))

    if variant == "variant-corner":
        prefix = Text("┌─", style=line_color)
        fill = max(0, width - len(prefix.plain) - chip_width)
        return Text.assemble(prefix, chip, ("·" * fill, line_dim_color))

    prefix = Text("╶", style=line_dim_color)
    fill = max(0, width - len(prefix.plain) - chip_width)
    return Text.assemble(prefix, chip, ("─" * fill, line_color))


def _build_footer(
    footer: str | Text | None,
    *,
    width: int,
    variant: str,
    line_dim_color: str,
    muted_color: str,
) -> Text | None:
    if footer is None:
        if variant == "variant-hero":
            return None
        glyph = "·" if variant == "variant-corner" else "─"
        return Text(glyph * width, style=line_dim_color)

    footer_text = footer if isinstance(footer, Text) else Text(str(footer), style=muted_color)
    raw = footer_text.plain
    max_footer = max(0, width - 3)
    if max_footer > 0 and len(raw) > max_footer:
        footer_text = Text(raw[: max_footer - 1] + "…", style=footer_text.style or muted_color)

    if variant == "variant-ribbon":
        return Text.assemble(("▚ ", line_dim_color), footer_text)
    if variant == "variant-corner":
        return Text.assemble(("└ ", line_dim_color), footer_text)
    return Text.assemble(("╶ ", line_dim_color), footer_text)

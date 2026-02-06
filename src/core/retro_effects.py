from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Union

from core.renderer import ColorRGB, RenderCell, RenderGrid, TextStyle


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return default


def _clamp_int(value: Any, default: int, minimum: int, maximum: Optional[int] = None) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if maximum is not None:
        number = min(number, maximum)
    return max(minimum, number)


def _clamp_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    number = min(number, maximum)
    return max(minimum, number)


def _parse_color(value: Any) -> Optional[ColorRGB]:
    if isinstance(value, ColorRGB):
        return value
    if isinstance(value, str) and value.strip():
        return ColorRGB.from_hex(value)
    return None


def _scale_color(color: Optional[ColorRGB], factor: float) -> Optional[ColorRGB]:
    if color is None:
        return None
    factor = max(0.0, factor)
    return ColorRGB(
        r=max(0, min(255, int(color.r * factor))),
        g=max(0, min(255, int(color.g * factor))),
        b=max(0, min(255, int(color.b * factor))),
        a=color.a,
    )


def _blend_color(
    base: Optional[ColorRGB],
    overlay: Optional[ColorRGB],
    alpha: float,
) -> Optional[ColorRGB]:
    if overlay is None:
        return base
    if base is None:
        return overlay
    alpha = _clamp_float(alpha, 0.0, 0.0, 1.0)
    inv = 1.0 - alpha
    return ColorRGB(
        r=max(0, min(255, int(base.r * inv + overlay.r * alpha))),
        g=max(0, min(255, int(base.g * inv + overlay.g * alpha))),
        b=max(0, min(255, int(base.b * inv + overlay.b * alpha))),
        a=base.a,
    )


def _update_style(
    style: TextStyle,
    *,
    fg: Optional[ColorRGB] = None,
    bg: Optional[ColorRGB] = None,
    bold: Optional[bool] = None,
    dim: Optional[bool] = None,
) -> TextStyle:
    return TextStyle(
        fg=fg if fg is not None else style.fg,
        bg=bg if bg is not None else style.bg,
        bold=style.bold if bold is None else bold,
        italic=style.italic,
        underline=style.underline,
        blink=style.blink,
        reverse=style.reverse,
        dim=style.dim if dim is None else dim,
        strike=style.strike,
        font=style.font,
    )


def _copy_grid(grid: RenderGrid) -> RenderGrid:
    return RenderGrid(
        width=grid.width,
        height=grid.height,
        cells=[row.copy() for row in grid.cells],
    )


@dataclass(frozen=True)
class ScanlineSettings:
    enabled: bool = True
    spacing: int = 2
    intensity: float = 0.15
    speed: int = 1
    mode: str = "darken"


@dataclass(frozen=True)
class GlowSettings:
    enabled: bool = True
    intensity: float = 0.35
    radius: int = 1
    halo_alpha: float = 0.35


@dataclass(frozen=True)
class NoiseSettings:
    enabled: bool = True
    density: float = 0.02
    chars: str = " .`,"
    color: Optional[ColorRGB] = None
    on_text: bool = False


@dataclass(frozen=True)
class WarpSettings:
    enabled: bool = True
    strength: int = 1
    probability: float = 0.12


@dataclass(frozen=True)
class RetroEffectConfig:
    enabled: bool = True
    scanlines: ScanlineSettings = ScanlineSettings()
    glow: GlowSettings = GlowSettings()
    noise: NoiseSettings = NoiseSettings()
    warp: WarpSettings = WarpSettings()
    seed: Optional[int] = None

    @classmethod
    def from_settings(cls, settings: Optional[Mapping[str, Any]]) -> "RetroEffectConfig":
        if not isinstance(settings, Mapping):
            return cls()
        enabled = _as_bool(settings.get("enabled", True), True)
        seed = settings.get("seed")
        if not isinstance(seed, int):
            seed = None

        scan_settings = settings.get("scanlines") or settings.get("scanline") or {}
        if not isinstance(scan_settings, Mapping):
            scan_settings = {}
        scanlines = ScanlineSettings(
            enabled=_as_bool(scan_settings.get("enabled", True), True),
            spacing=_clamp_int(scan_settings.get("spacing"), 2, 1, 64),
            intensity=_clamp_float(scan_settings.get("intensity"), 0.15, 0.0, 1.0),
            speed=_clamp_int(scan_settings.get("speed"), 1, 0, 10),
            mode=str(scan_settings.get("mode", "darken")).strip().lower() or "darken",
        )

        glow_settings = settings.get("glow") or {}
        if not isinstance(glow_settings, Mapping):
            glow_settings = {}
        glow = GlowSettings(
            enabled=_as_bool(glow_settings.get("enabled", True), True),
            intensity=_clamp_float(glow_settings.get("intensity"), 0.35, 0.0, 2.0),
            radius=_clamp_int(glow_settings.get("radius"), 1, 0, 4),
            halo_alpha=_clamp_float(glow_settings.get("halo_alpha"), 0.35, 0.0, 1.0),
        )

        noise_settings = settings.get("noise") or {}
        if not isinstance(noise_settings, Mapping):
            noise_settings = {}
        noise = NoiseSettings(
            enabled=_as_bool(noise_settings.get("enabled", True), True),
            density=_clamp_float(noise_settings.get("density"), 0.02, 0.0, 1.0),
            chars=str(noise_settings.get("chars", " .`,")) or " .`,",
            color=_parse_color(noise_settings.get("color")),
            on_text=_as_bool(noise_settings.get("on_text", False), False),
        )

        warp_settings = settings.get("warp") or {}
        if not isinstance(warp_settings, Mapping):
            warp_settings = {}
        warp = WarpSettings(
            enabled=_as_bool(warp_settings.get("enabled", True), True),
            strength=_clamp_int(warp_settings.get("strength"), 1, 0, 5),
            probability=_clamp_float(warp_settings.get("probability"), 0.12, 0.0, 1.0),
        )

        return cls(
            enabled=enabled,
            scanlines=scanlines,
            glow=glow,
            noise=noise,
            warp=warp,
            seed=seed,
        )


def apply_scanlines(
    grid: RenderGrid, settings: ScanlineSettings, frame_index: int = 0
) -> RenderGrid:
    if not settings.enabled or grid.height <= 0 or grid.width <= 0:
        return grid
    spacing = max(1, settings.spacing)
    phase = 0
    if spacing > 0 and settings.speed:
        phase = (frame_index * settings.speed) % spacing
    factor = 1.0 - settings.intensity
    if settings.mode == "brighten":
        factor = 1.0 + settings.intensity
    result = _copy_grid(grid)
    for y, row in enumerate(grid.cells):
        if (y + phase) % spacing != 0:
            continue
        for x, cell in enumerate(row):
            new_style = _update_style(
                cell.style,
                fg=_scale_color(cell.style.fg, factor),
                bg=_scale_color(cell.style.bg, factor),
                bold=cell.style.bold or factor > 1.0,
                dim=cell.style.dim or factor < 1.0,
            )
            if new_style != cell.style:
                result.cells[y][x] = RenderCell(cell.char, new_style)
    return result


def apply_glow(grid: RenderGrid, settings: GlowSettings) -> RenderGrid:
    if not settings.enabled or grid.height <= 0 or grid.width <= 0:
        return grid
    radius = max(0, settings.radius)
    if radius == 0:
        return grid
    result = _copy_grid(grid)
    halo_map: dict[tuple[int, int], tuple[ColorRGB, float]] = {}

    def _add_halo(x: int, y: int, color: ColorRGB, alpha: float) -> None:
        key = (x, y)
        if key in halo_map:
            existing_color, existing_alpha = halo_map[key]
            combined_alpha = min(1.0, existing_alpha + alpha)
            blended = _blend_color(existing_color, color, alpha / combined_alpha)
            halo_map[key] = (blended or color, combined_alpha)
        else:
            halo_map[key] = (color, alpha)

    for y, row in enumerate(grid.cells):
        for x, cell in enumerate(row):
            if cell.char == " ":
                continue
            fg = cell.style.fg
            if fg is None:
                continue
            bright = _scale_color(fg, 1.0 + settings.intensity)
            if bright is not None:
                result.cells[y][x] = RenderCell(
                    cell.char, _update_style(cell.style, fg=bright, bold=True)
                )
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    dist = abs(dx) + abs(dy)
                    if dist > radius:
                        continue
                    nx = x + dx
                    ny = y + dy
                    if nx < 0 or ny < 0 or nx >= grid.width or ny >= grid.height:
                        continue
                    if grid.cells[ny][nx].char != " ":
                        continue
                    falloff = 1.0 - (dist / (radius + 1))
                    alpha = settings.halo_alpha * falloff
                    if alpha <= 0:
                        continue
                    _add_halo(nx, ny, fg, alpha)

    for (x, y), (color, alpha) in halo_map.items():
        cell = result.cells[y][x]
        blended_bg = _blend_color(cell.style.bg, color, alpha)
        result.cells[y][x] = RenderCell(
            cell.char,
            _update_style(cell.style, bg=blended_bg, dim=True),
        )
    return result


def apply_noise(
    grid: RenderGrid, settings: NoiseSettings, rng: random.Random
) -> RenderGrid:
    if not settings.enabled or grid.height <= 0 or grid.width <= 0:
        return grid
    if settings.density <= 0:
        return grid
    result = _copy_grid(grid)
    noise_chars = settings.chars or " .`,"
    color = settings.color
    for y, row in enumerate(grid.cells):
        for x, cell in enumerate(row):
            if not settings.on_text and cell.char != " ":
                continue
            if rng.random() >= settings.density:
                continue
            noise_char = rng.choice(noise_chars)
            fg = cell.style.fg
            if color is not None:
                fg = _blend_color(cell.style.fg, color, 0.6)
            new_style = _update_style(cell.style, fg=fg, dim=True)
            result.cells[y][x] = RenderCell(noise_char, new_style)
    return result


def apply_warp(
    grid: RenderGrid, settings: WarpSettings, rng: random.Random
) -> RenderGrid:
    if not settings.enabled or grid.height <= 0 or grid.width <= 0:
        return grid
    if settings.strength <= 0 or settings.probability <= 0:
        return grid
    width = grid.width
    new_cells: list[list[RenderCell]] = []
    for row in grid.cells:
        base_style = row[0].style if row else TextStyle()
        offset = 0
        if rng.random() < settings.probability:
            offset = rng.randint(-settings.strength, settings.strength)
            if offset == 0 and settings.strength > 0:
                offset = settings.strength if rng.random() < 0.5 else -settings.strength
        if offset == 0:
            new_cells.append(row.copy())
            continue
        new_row = [RenderCell(" ", base_style) for _ in range(width)]
        for x, cell in enumerate(row):
            nx = x + offset
            if 0 <= nx < width:
                new_row[nx] = cell
        new_cells.append(new_row)
    return RenderGrid(width=grid.width, height=grid.height, cells=new_cells)


def apply_retro_effects(
    grid: RenderGrid,
    settings: Optional[Union[Mapping[str, Any], RetroEffectConfig]],
    *,
    frame_index: int = 0,
) -> RenderGrid:
    config = settings
    if isinstance(settings, Mapping) or settings is None:
        config = RetroEffectConfig.from_settings(settings)
    if not isinstance(config, RetroEffectConfig) or not config.enabled:
        return grid
    rng = random.Random()
    if config.seed is not None:
        rng.seed(config.seed + frame_index)
    working = grid
    if config.warp.enabled:
        working = apply_warp(working, config.warp, rng)
    if config.scanlines.enabled:
        working = apply_scanlines(working, config.scanlines, frame_index=frame_index)
    if config.glow.enabled:
        working = apply_glow(working, config.glow)
    if config.noise.enabled:
        working = apply_noise(working, config.noise, rng)
    return working

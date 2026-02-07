from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Union

try:
    import numpy as np
except Exception:  # pragma: no cover - optional fallback path
    np = None

from PySide6.QtGui import QColor, QImage, QPainter


@dataclass(frozen=True)
class CRTShaderConfig:
    enabled: bool = False
    curvature: float = 0.07
    scanline_intensity: float = 0.14
    scanline_spacing: int = 2
    chromatic_aberration: int = 1
    vignette: float = 0.22
    noise: float = 0.025
    blur: float = 0.1
    mask_strength: float = 0.08
    jitter: float = 0.0

    @classmethod
    def from_settings(cls, settings: Optional[Mapping[str, Any]]) -> "CRTShaderConfig":
        if not isinstance(settings, Mapping):
            return cls()
        return cls(
            enabled=_as_bool(settings.get("enabled"), False),
            curvature=_clamp_float(settings.get("curvature"), 0.07, 0.0, 0.3),
            scanline_intensity=_clamp_float(
                settings.get("scanline_intensity"), 0.14, 0.0, 1.0
            ),
            scanline_spacing=_clamp_int(settings.get("scanline_spacing"), 2, 1, 12),
            chromatic_aberration=_clamp_int(
                settings.get("chromatic_aberration"), 1, 0, 6
            ),
            vignette=_clamp_float(settings.get("vignette"), 0.22, 0.0, 0.8),
            noise=_clamp_float(settings.get("noise"), 0.025, 0.0, 0.25),
            blur=_clamp_float(settings.get("blur"), 0.1, 0.0, 1.0),
            mask_strength=_clamp_float(settings.get("mask_strength"), 0.08, 0.0, 0.35),
            jitter=_clamp_float(settings.get("jitter"), 0.0, 0.0, 2.0),
        )


def apply_crt_shader(
    image: QImage,
    settings: Optional[Union[Mapping[str, Any], CRTShaderConfig]],
    *,
    frame_index: int = 0,
) -> QImage:
    if image.isNull():
        return image
    config = settings
    if settings is None or isinstance(settings, Mapping):
        config = CRTShaderConfig.from_settings(settings)
    if not isinstance(config, CRTShaderConfig) or not config.enabled:
        return image
    if np is None:
        return _fallback_overlay(image, config, frame_index=frame_index)

    working = image.convertToFormat(QImage.Format.Format_ARGB32)
    arr = _image_to_bgra_array(working).astype(np.float32, copy=False)
    if arr.size == 0:
        return working

    h, w = arr.shape[0], arr.shape[1]
    rgb = arr[:, :, :3]

    if config.jitter > 0:
        jx = int(round(np.sin(frame_index * 0.62) * config.jitter))
        jy = int(round(np.cos(frame_index * 0.41) * config.jitter * 0.5))
        if jx or jy:
            rgb[:] = _shift_rgb(rgb, jx, jy)

    if config.curvature > 0:
        rgb[:] = _curvature_warp(rgb, config.curvature)

    if config.chromatic_aberration > 0:
        _apply_chromatic_aberration(rgb, config.chromatic_aberration)

    if config.blur > 0:
        _apply_soft_blur(rgb, config.blur)

    if config.scanline_intensity > 0:
        _apply_scanlines(
            rgb,
            intensity=config.scanline_intensity,
            spacing=config.scanline_spacing,
            frame_index=frame_index,
        )

    if config.mask_strength > 0:
        _apply_slot_mask(rgb, config.mask_strength)

    if config.vignette > 0:
        _apply_vignette(rgb, config.vignette)

    if config.noise > 0:
        _apply_noise(rgb, config.noise, frame_index=frame_index)

    np.clip(arr[:, :, :3], 0, 255, out=arr[:, :, :3])
    result_u8 = arr.astype(np.uint8)
    return _array_to_image(result_u8, w=w, h=h)


def _image_to_bgra_array(image: QImage):
    width = image.width()
    height = image.height()
    if width <= 0 or height <= 0:
        return np.zeros((0, 0, 4), dtype=np.uint8)
    ptr = image.bits()
    ptr.setsize(image.sizeInBytes())
    arr = np.frombuffer(ptr, dtype=np.uint8)
    bytes_per_line = image.bytesPerLine()
    arr = arr.reshape((height, bytes_per_line))
    arr = arr[:, : width * 4]
    return arr.reshape((height, width, 4))


def _array_to_image(arr, *, w: int, h: int) -> QImage:
    output = QImage(w, h, QImage.Format.Format_ARGB32)
    ptr = output.bits()
    ptr.setsize(output.sizeInBytes())
    out_arr = np.frombuffer(ptr, dtype=np.uint8).reshape((h, output.bytesPerLine()))
    out_arr[:, : w * 4] = arr.reshape((h, w * 4))
    if output.bytesPerLine() > w * 4:
        out_arr[:, w * 4 :] = 0
    return output


def _shift_rgb(rgb, dx: int, dy: int):
    shifted = np.roll(rgb, shift=(dy, dx), axis=(0, 1))
    if dy > 0:
        shifted[:dy, :, :] = shifted[dy : dy + 1, :, :]
    elif dy < 0:
        shifted[dy:, :, :] = shifted[dy - 1 : dy, :, :]
    if dx > 0:
        shifted[:, :dx, :] = shifted[:, dx : dx + 1, :]
    elif dx < 0:
        shifted[:, dx:, :] = shifted[:, dx - 1 : dx, :]
    return shifted


def _curvature_warp(rgb, curvature: float):
    h, w = rgb.shape[0], rgb.shape[1]
    if h <= 1 or w <= 1:
        return rgb
    yy, xx = np.indices((h, w), dtype=np.float32)
    nx = (xx / (w - 1)) * 2.0 - 1.0
    ny = (yy / (h - 1)) * 2.0 - 1.0
    strength = curvature * 0.65
    src_x = nx * (1.0 + strength * (ny * ny))
    src_y = ny * (1.0 + strength * (nx * nx))
    outside = (np.abs(src_x) > 1.0) | (np.abs(src_y) > 1.0)
    sx = np.clip(((src_x + 1.0) * 0.5 * (w - 1)).astype(np.int32), 0, w - 1)
    sy = np.clip(((src_y + 1.0) * 0.5 * (h - 1)).astype(np.int32), 0, h - 1)
    warped = rgb[sy, sx].copy()
    warped[outside] *= 0.2
    return warped


def _apply_chromatic_aberration(rgb, offset: int) -> None:
    if offset <= 0:
        return
    original = rgb.copy()
    if offset < rgb.shape[1]:
        rgb[:, :-offset, 2] = original[:, offset:, 2]
        rgb[:, -offset:, 2] = original[:, -1:, 2]
        rgb[:, offset:, 0] = original[:, :-offset, 0]
        rgb[:, :offset, 0] = original[:, :1, 0]


def _apply_soft_blur(rgb, blur: float) -> None:
    if blur <= 0:
        return
    alpha = min(1.0, blur)
    original = rgb.copy()
    up = np.roll(original, -1, axis=0)
    down = np.roll(original, 1, axis=0)
    left = np.roll(original, -1, axis=1)
    right = np.roll(original, 1, axis=1)
    neighbor = (up + down + left + right) * 0.25
    rgb[:] = (original * (1.0 - alpha)) + (neighbor * alpha)


def _apply_scanlines(rgb, *, intensity: float, spacing: int, frame_index: int) -> None:
    rows = np.arange(rgb.shape[0], dtype=np.int32)
    phase = frame_index % max(1, spacing)
    mask = ((rows + phase) % max(1, spacing)) == 0
    rgb[mask, :, :] *= max(0.0, 1.0 - intensity)


def _apply_slot_mask(rgb, strength: float) -> None:
    cols = np.arange(rgb.shape[1], dtype=np.int32)
    tri = cols % 3
    dark = max(0.0, 1.0 - strength)
    rgb[:] *= dark
    boost = 1.0 + strength * 0.85
    rgb[:, tri == 0, 2] *= boost
    rgb[:, tri == 1, 1] *= boost
    rgb[:, tri == 2, 0] *= boost


def _apply_vignette(rgb, vignette: float) -> None:
    h, w = rgb.shape[0], rgb.shape[1]
    yy, xx = np.indices((h, w), dtype=np.float32)
    nx = (xx / max(1, w - 1)) * 2.0 - 1.0
    ny = (yy / max(1, h - 1)) * 2.0 - 1.0
    radius = np.sqrt(nx * nx + ny * ny)
    falloff = 1.0 - np.clip((radius - 0.2) * vignette * 1.6, 0.0, 0.85)
    rgb[:] *= falloff[:, :, None]


def _apply_noise(rgb, noise_strength: float, *, frame_index: int) -> None:
    seed = 0xC0DE + frame_index * 131
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, noise_strength * 255.0, size=rgb.shape)
    rgb[:] += noise


def _fallback_overlay(image: QImage, config: CRTShaderConfig, *, frame_index: int) -> QImage:
    result = image.copy()
    painter = QPainter(result)
    painter.setOpacity(min(0.35, max(0.0, config.scanline_intensity)))
    spacing = max(1, config.scanline_spacing)
    y_offset = frame_index % spacing
    scanline_color = QColor(0, 0, 0, 70)
    for y in range(y_offset, result.height(), spacing):
        painter.fillRect(0, y, result.width(), 1, scanline_color)
    if config.vignette > 0:
        alpha = int(160 * min(1.0, config.vignette))
        shade = QColor(0, 0, 0, alpha)
        painter.fillRect(0, 0, result.width(), int(result.height() * 0.08), shade)
        painter.fillRect(
            0,
            int(result.height() * 0.92),
            result.width(),
            result.height(),
            shade,
        )
    painter.end()
    return result


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return value != 0
    return default


def _clamp_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))


def _clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))

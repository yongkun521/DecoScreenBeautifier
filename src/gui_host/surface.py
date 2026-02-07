from __future__ import annotations

from typing import Optional, Tuple

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QImage, QPainter
from PySide6.QtWidgets import QWidget

from core.renderer import RenderGrid, TextStyle
from gui_host.postprocess import CRTShaderConfig, apply_crt_shader


class RenderSurface(QWidget):
    def __init__(self, settings: dict, *, parent=None) -> None:
        super().__init__(parent)
        self._grid: Optional[RenderGrid] = None
        self._font_face = "Cascadia Mono"
        self._font_size = 14
        self._cell_aspect = 1.0
        self._global_scale = 1.0
        self._frame_index = 0
        self._background = QColor(0, 0, 0)
        self._crt_shader_config = CRTShaderConfig()
        self._font_normal: Optional[QFont] = None
        self._font_bold: Optional[QFont] = None
        self._metrics: Optional[QFontMetrics] = None
        self._cell_w = 1
        self._cell_h = 1
        self._baseline = 1
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAutoFillBackground(False)
        self.update_settings(settings)

    def update_settings(self, settings: dict, *, global_scale: Optional[float] = None) -> None:
        if isinstance(settings, dict):
            self._font_face = str(settings.get("font_face") or self._font_face)
            self._font_size = _safe_int(settings.get("font_size"), self._font_size)
            self._cell_aspect = _safe_float(settings.get("cell_aspect"), self._cell_aspect)
            self._crt_shader_config = CRTShaderConfig.from_settings(
                settings.get("crt_shader")
            )
        if global_scale is not None:
            self._global_scale = _safe_float(global_scale, self._global_scale)
        self._rebuild_metrics()
        self.update()

    def set_grid(self, grid: Optional[RenderGrid]) -> None:
        self._grid = grid
        self.update()

    def set_frame_index(self, frame_index: int) -> None:
        self._frame_index = _safe_int(frame_index, 0)

    def grid_size(self) -> Tuple[int, int]:
        self._rebuild_metrics()
        width = max(1, self.width() // max(1, self._cell_w))
        height = max(1, self.height() // max(1, self._cell_h))
        return width, height

    def paintEvent(self, event) -> None:  # noqa: N802
        target_image = QImage(self.size(), QImage.Format.Format_ARGB32)
        target_image.fill(self._background)
        painter = QPainter(target_image)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(target_image.rect(), self._background)

        grid = self._grid
        if grid is not None and grid.width > 0 and grid.height > 0:
            self._rebuild_metrics()
            if self._font_normal and self._metrics:
                total_w = grid.width * self._cell_w
                total_h = grid.height * self._cell_h
                offset_x = max(0, (self.width() - total_w) // 2)
                offset_y = max(0, (self.height() - total_h) // 2)

                for y, row in enumerate(grid.cells):
                    if not row:
                        continue
                    y_top = offset_y + y * self._cell_h
                    baseline = y_top + self._baseline
                    for start, text, style in _iter_segments(row):
                        if not text:
                            continue
                        fg, bg = _resolve_colors(style, self._background)
                        if bg is not None:
                            painter.fillRect(
                                QRect(
                                    offset_x + start * self._cell_w,
                                    y_top,
                                    len(text) * self._cell_w,
                                    self._cell_h,
                                ),
                                bg,
                            )
                        if text.strip() == "" and bg is None:
                            continue
                        painter.setFont(self._font_bold if style.bold else self._font_normal)
                        painter.setPen(fg)
                        painter.drawText(offset_x + start * self._cell_w, baseline, text)

        painter.end()

        shader_enabled = bool(getattr(self._crt_shader_config, "enabled", False))
        if shader_enabled:
            frame_index = _safe_int(getattr(self, "_frame_index", 0), 0)
            target_image = apply_crt_shader(
                target_image,
                self._crt_shader_config,
                frame_index=frame_index,
            )

        final_painter = QPainter(self)
        final_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        final_painter.drawImage(0, 0, target_image)
        final_painter.end()

    def _rebuild_metrics(self) -> None:
        if self._font_normal is None:
            self._font_normal = QFont(self._font_face, self._font_size)
            self._font_normal.setStyleHint(QFont.StyleHint.Monospace)
            self._font_normal.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        else:
            self._font_normal.setFamily(self._font_face)
            self._font_normal.setPointSize(self._font_size)
        self._font_bold = QFont(self._font_normal)
        self._font_bold.setBold(True)
        self._metrics = QFontMetrics(self._font_normal)
        scale = max(0.1, self._global_scale)
        self._cell_w = max(1, int(self._metrics.horizontalAdvance("M") * self._cell_aspect * scale))
        self._cell_h = max(1, int(self._metrics.height() * scale))
        self._baseline = max(1, int(self._metrics.ascent() * scale))


def _iter_segments(row):
    if not row:
        return
    start = 0
    current_style = row[0].style
    buffer = [row[0].char]
    for idx in range(1, len(row)):
        cell = row[idx]
        if cell.style == current_style:
            buffer.append(cell.char)
            continue
        yield start, "".join(buffer), current_style
        start = idx
        current_style = cell.style
        buffer = [cell.char]
    yield start, "".join(buffer), current_style


def _resolve_colors(style: TextStyle, fallback_bg: QColor) -> tuple[QColor, Optional[QColor]]:
    fg = _to_qcolor(style.fg) or QColor(0, 255, 65)
    bg = _to_qcolor(style.bg)
    if style.reverse:
        fg, bg = bg or fallback_bg, fg
    if style.dim:
        fg = _dim_color(fg)
        if bg is not None:
            bg = _dim_color(bg)
    return fg, bg


def _to_qcolor(color) -> Optional[QColor]:
    if color is None:
        return None
    return QColor(color.r, color.g, color.b, getattr(color, "a", 255))


def _dim_color(color: QColor, factor: float = 0.6) -> QColor:
    return QColor(
        max(0, int(color.red() * factor)),
        max(0, int(color.green() * factor)),
        max(0, int(color.blue() * factor)),
        color.alpha(),
    )


def _safe_int(value, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _safe_float(value, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback

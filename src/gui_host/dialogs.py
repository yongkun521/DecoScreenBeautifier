from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from core.presets import DEFAULT_TEMPLATE_ID


class TemplateDialog(QDialog):
    def __init__(self, config_manager, current_id: Optional[str] = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Templates")
        self._templates = config_manager.list_templates()
        self._template_lookup: Dict[str, dict] = {
            str(template.get("id")): template for template in self._templates
        }
        self._current_id = current_id

        self._list = QListWidget()
        self._description = QLabel("Select a template to view details.")
        self._description.setWordWrap(True)
        self._description.setMinimumWidth(280)

        self._populate_list()
        self._list.currentItemChanged.connect(self._on_selection_changed)
        self._list.itemDoubleClicked.connect(self._accept_if_valid)

        list_layout = QVBoxLayout()
        list_layout.addWidget(QLabel("Templates"))
        list_layout.addWidget(self._list)

        detail_layout = QVBoxLayout()
        detail_layout.addWidget(QLabel("Details"))
        detail_layout.addWidget(self._description)
        detail_layout.addStretch(1)

        content_layout = QHBoxLayout()
        content_layout.addLayout(list_layout, 2)
        content_layout.addLayout(detail_layout, 3)

        buttons = QDialogButtonBox()
        apply_button = QPushButton("Apply")
        close_button = QPushButton("Close")
        buttons.addButton(apply_button, QDialogButtonBox.AcceptRole)
        buttons.addButton(close_button, QDialogButtonBox.RejectRole)
        apply_button.clicked.connect(self._accept_if_valid)
        close_button.clicked.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(content_layout)
        main_layout.addWidget(buttons)
        self.setLayout(main_layout)
        self.resize(640, 360)

    def selected_template_id(self) -> Optional[str]:
        item = self._list.currentItem()
        if not item:
            return None
        template_id = item.data(Qt.ItemDataRole.UserRole)
        return str(template_id) if template_id else None

    def _populate_list(self) -> None:
        self._list.clear()
        if not self._templates:
            self._description.setText("No templates available.")
            return
        current_index = 0
        for idx, template in enumerate(self._templates):
            template_id = str(template.get("id", ""))
            name = str(template.get("name") or template_id or "Unnamed")
            item = QListWidgetItem(f"{name} ({template_id})")
            item.setData(Qt.ItemDataRole.UserRole, template_id)
            self._list.addItem(item)
            if self._current_id and template_id == self._current_id:
                current_index = idx
        if self._list.count() > 0:
            self._list.setCurrentRow(current_index)

    def _on_selection_changed(self, current: QListWidgetItem, _previous: QListWidgetItem) -> None:
        if not current:
            return
        template_id = current.data(Qt.ItemDataRole.UserRole)
        template = self._template_lookup.get(str(template_id), {})
        self._description.setText(_format_template_description(template))

    def _accept_if_valid(self) -> None:
        if self.selected_template_id():
            self.accept()


class SettingsDialog(QDialog):
    def __init__(self, gui_settings: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._initial_settings = gui_settings or {}

        self.screen_combo = QComboBox()
        self._populate_screens()

        self.use_work_area_check = QCheckBox("Use work area")
        self.use_work_area_check.setChecked(bool(self._initial_settings.get("use_work_area", True)))

        self.always_on_top_check = QCheckBox("Always on top")
        self.always_on_top_check.setChecked(bool(self._initial_settings.get("always_on_top", False)))

        effects_settings = self._initial_settings.get("effects")
        effects_enabled = True
        if isinstance(effects_settings, dict):
            effects_enabled = bool(effects_settings.get("enabled", True))
        self.effects_check = QCheckBox("Enable effects")
        self.effects_check.setChecked(effects_enabled)

        crt_settings = self._initial_settings.get("crt_shader")
        crt_enabled = False
        if isinstance(crt_settings, dict):
            crt_enabled = bool(crt_settings.get("enabled", False))
        self.crt_shader_check = QCheckBox("Enable CRT shader")
        self.crt_shader_check.setChecked(crt_enabled)

        self.font_combo = QFontComboBox()
        self.font_combo.setFontFilters(QFontComboBox.FontFilter.MonospacedFonts)
        font_face = str(self._initial_settings.get("font_face") or "Cascadia Mono")
        self.font_combo.setCurrentFont(QFont(font_face))

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 48)
        self.font_size_spin.setValue(int(self._initial_settings.get("font_size", 14)))

        form = QFormLayout()
        form.addRow("Screen", self.screen_combo)
        form.addRow("Font", self.font_combo)
        form.addRow("Font size", self.font_size_spin)
        form.addRow("", self.use_work_area_check)
        form.addRow("", self.always_on_top_check)
        form.addRow("", self.effects_check)
        form.addRow("", self.crt_shader_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.resize(460, 280)

    def settings_payload(self) -> dict:
        return {
            "monitor": self.screen_combo.currentData(),
            "use_work_area": self.use_work_area_check.isChecked(),
            "always_on_top": self.always_on_top_check.isChecked(),
            "font_face": self.font_combo.currentFont().family(),
            "font_size": self.font_size_spin.value(),
            "effects_enabled": self.effects_check.isChecked(),
            "crt_shader_enabled": self.crt_shader_check.isChecked(),
        }

    def _populate_screens(self) -> None:
        choices = _screen_choices()
        current_monitor = self._initial_settings.get("monitor", "auto")
        self.screen_combo.clear()
        current_index = 0
        for idx, (label, value) in enumerate(choices):
            self.screen_combo.addItem(label, value)
            if _same_monitor(value, current_monitor):
                current_index = idx
        self.screen_combo.setCurrentIndex(current_index)


def _screen_choices() -> List[tuple[str, str]]:
    choices: List[tuple[str, str]] = [
        ("Auto (secondary preferred)", "auto"),
        ("Primary", "primary"),
        ("Secondary", "secondary"),
    ]
    screens = QGuiApplication.screens()
    primary = QGuiApplication.primaryScreen()
    for index, screen in enumerate(screens):
        geo = screen.geometry()
        name = screen.name() or f"Screen {index}"
        label = f"{index}: {name} {geo.width()}x{geo.height()}"
        if screen == primary:
            label += " (Primary)"
        choices.append((label, str(index)))
    return choices


def _same_monitor(value: Optional[str], current) -> bool:
    if value is None:
        return False
    if current is None:
        return False
    if isinstance(current, int):
        current = str(current)
    return str(value).strip().lower() == str(current).strip().lower()


def _format_template_description(template: dict) -> str:
    description = str(template.get("description") or "").strip()
    profile = str(template.get("screen_profile") or "").strip()
    resolution = str(template.get("recommended_resolution") or "").strip()
    tags = template.get("tags")
    if not isinstance(tags, list):
        tags = []
    lines = []
    if description:
        lines.append(description)
    if resolution:
        lines.append(f"Recommended: {resolution}")
    if profile:
        lines.append(f"Profile: {profile}")
    if tags:
        lines.append(f"Tags: {', '.join(str(tag) for tag in tags)}")
    if not lines:
        return "No details available."
    return "\n".join(lines)


class GuiLayoutEditorDialog(QDialog):
    def __init__(self, config_manager, template: dict, layout_data: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("GUI Layout Editor")
        self._config_manager = config_manager
        self._template = template or {}
        self._layout_name = str(self._template.get("id") or "default")
        self._layout_data = deepcopy(layout_data) if isinstance(layout_data, dict) else {}
        self._grid_cols = 1
        self._grid_rows = 1
        self._cell_size = 32
        self._selected_component_id: Optional[str] = None

        self._canvas = _LayoutCanvasWidget(self)
        self._component_list = QListWidget()
        self._component_list.currentItemChanged.connect(self._on_component_selected)

        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Components"))
        right_layout.addWidget(self._component_list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        save_button = buttons.button(QDialogButtonBox.Save)
        if save_button:
            save_button.setText("Save")
        restore_button = buttons.button(QDialogButtonBox.RestoreDefaults)
        if restore_button:
            restore_button.setText("Auto Arrange")
        buttons.accepted.connect(self._save_layout)
        buttons.rejected.connect(self.reject)
        if restore_button:
            restore_button.clicked.connect(self._auto_arrange)

        root_layout = QHBoxLayout()
        root_layout.addWidget(self._canvas, 3)
        root_layout.addLayout(right_layout, 2)

        container = QVBoxLayout()
        container.addLayout(root_layout)
        container.addWidget(buttons)
        self.setLayout(container)
        self.resize(860, 560)

        self._sanitize_layout()
        self._refresh_component_list()

    def _sanitize_layout(self) -> None:
        grid_size = self._layout_data.get("grid_size", {})
        if not isinstance(grid_size, dict):
            grid_size = {}
            self._layout_data["grid_size"] = grid_size
        self._grid_cols = max(1, _safe_int(grid_size.get("cols"), 6))
        self._grid_rows = max(1, _safe_int(grid_size.get("rows"), 4))
        grid_size["cols"] = self._grid_cols
        grid_size["rows"] = self._grid_rows

        components = self._layout_data.get("components")
        if not isinstance(components, list):
            components = []
            self._layout_data["components"] = components

        clean_components = []
        for component in components:
            if not isinstance(component, dict):
                continue
            component_id = str(component.get("id") or "").strip()
            type_name = str(component.get("type") or "").strip()
            if not component_id or not type_name:
                continue
            pos = component.get("pos")
            if not isinstance(pos, list):
                pos = [0, 0, 1, 1]
            while len(pos) < 4:
                pos.append(1)
            col = max(0, min(self._grid_cols - 1, _safe_int(pos[0], 0)))
            row = max(0, min(self._grid_rows - 1, _safe_int(pos[1], 0)))
            col_span = max(1, min(self._grid_cols - col, _safe_int(pos[2], 1)))
            row_span = max(1, min(self._grid_rows - row, _safe_int(pos[3], 1)))
            component["pos"] = [col, row, col_span, row_span]
            clean_components.append(component)
        self._layout_data["components"] = clean_components
        if clean_components and self._selected_component_id is None:
            self._selected_component_id = str(clean_components[0].get("id"))

    def _refresh_component_list(self) -> None:
        self._component_list.clear()
        current_index = 0
        for index, component in enumerate(self._components()):
            component_id = str(component.get("id"))
            pos = component.get("pos", [0, 0, 1, 1])
            label = f"{component_id} [{pos[0]},{pos[1]} {pos[2]}x{pos[3]}]"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, component_id)
            self._component_list.addItem(item)
            if component_id == self._selected_component_id:
                current_index = index
        if self._component_list.count() > 0:
            self._component_list.setCurrentRow(current_index)
        self._canvas.update()

    def _on_component_selected(self, current: QListWidgetItem, _previous: QListWidgetItem) -> None:
        if not current:
            self._selected_component_id = None
        else:
            self._selected_component_id = str(current.data(Qt.ItemDataRole.UserRole) or "")
        self._canvas.update()

    def _save_layout(self) -> None:
        self._layout_data["template_id"] = self._template.get("id", DEFAULT_TEMPLATE_ID)
        self._layout_data.setdefault("layout_class", self._template.get("layout_class"))
        self._layout_data.setdefault("name", f"Layout {self._layout_name}")
        self._layout_data["grid_size"] = {"cols": self._grid_cols, "rows": self._grid_rows}
        self._config_manager.save_layout(self._layout_name, self._layout_data)
        self.accept()

    def _auto_arrange(self) -> None:
        components = self._components()
        occupied = set()
        for component in components:
            pos = component.get("pos", [0, 0, 1, 1])
            col_span = max(1, _safe_int(pos[2], 1))
            row_span = max(1, _safe_int(pos[3], 1))
            placed = False
            for row in range(self._grid_rows):
                for col in range(self._grid_cols):
                    if col + col_span > self._grid_cols or row + row_span > self._grid_rows:
                        continue
                    cells = _cells_for_pos(col, row, col_span, row_span)
                    if occupied.isdisjoint(cells):
                        component["pos"] = [col, row, col_span, row_span]
                        occupied |= cells
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                component["pos"] = [0, 0, col_span, row_span]
        self._refresh_component_list()

    def _components(self) -> List[dict]:
        components = self._layout_data.get("components")
        if isinstance(components, list):
            return components
        return []

    def _selected_component(self) -> Optional[dict]:
        if not self._selected_component_id:
            return None
        for component in self._components():
            if str(component.get("id")) == self._selected_component_id:
                return component
        return None

    def _can_place(self, moving_id: str, col: int, row: int, col_span: int, row_span: int) -> bool:
        if col < 0 or row < 0:
            return False
        if col + col_span > self._grid_cols or row + row_span > self._grid_rows:
            return False
        occupied = set()
        for component in self._components():
            component_id = str(component.get("id") or "")
            if component_id == moving_id:
                continue
            pos = component.get("pos", [0, 0, 1, 1])
            occupied |= _cells_for_pos(
                _safe_int(pos[0], 0),
                _safe_int(pos[1], 0),
                max(1, _safe_int(pos[2], 1)),
                max(1, _safe_int(pos[3], 1)),
            )
        target_cells = _cells_for_pos(col, row, col_span, row_span)
        return occupied.isdisjoint(target_cells)

    def _handle_drag(self, delta_col: int, delta_row: int) -> None:
        component = self._selected_component()
        if component is None:
            return
        pos = component.get("pos", [0, 0, 1, 1])
        col = _safe_int(pos[0], 0)
        row = _safe_int(pos[1], 0)
        col_span = max(1, _safe_int(pos[2], 1))
        row_span = max(1, _safe_int(pos[3], 1))
        new_col = col + delta_col
        new_row = row + delta_row
        if not self._can_place(str(component.get("id")), new_col, new_row, col_span, row_span):
            return
        component["pos"] = [new_col, new_row, col_span, row_span]
        self._refresh_component_list()

    def _handle_resize(self, delta_col_span: int, delta_row_span: int) -> None:
        component = self._selected_component()
        if component is None:
            return
        pos = component.get("pos", [0, 0, 1, 1])
        col = _safe_int(pos[0], 0)
        row = _safe_int(pos[1], 0)
        col_span = max(1, _safe_int(pos[2], 1) + delta_col_span)
        row_span = max(1, _safe_int(pos[3], 1) + delta_row_span)
        col_span = min(col_span, self._grid_cols - col)
        row_span = min(row_span, self._grid_rows - row)
        if not self._can_place(str(component.get("id")), col, row, col_span, row_span):
            return
        component["pos"] = [col, row, col_span, row_span]
        self._refresh_component_list()


class _LayoutCanvasWidget(QLabel):
    def __init__(self, editor: GuiLayoutEditorDialog) -> None:
        super().__init__()
        self._editor = editor
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(420, 360)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._dragging = False
        self._drag_anchor = None

    def paintEvent(self, event) -> None:  # noqa: N802
        from PySide6.QtGui import QColor, QPainter, QPen

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#070b12"))

        cols = self._editor._grid_cols
        rows = self._editor._grid_rows
        if cols <= 0 or rows <= 0:
            painter.end()
            return

        cell = max(
            12,
            min(self.width() // max(1, cols), self.height() // max(1, rows)),
        )
        self._editor._cell_size = cell
        canvas_w = cols * cell
        canvas_h = rows * cell
        origin_x = max(0, (self.width() - canvas_w) // 2)
        origin_y = max(0, (self.height() - canvas_h) // 2)

        grid_pen = QPen(QColor("#1a3245"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for col in range(cols + 1):
            x = origin_x + col * cell
            painter.drawLine(x, origin_y, x, origin_y + canvas_h)
        for row in range(rows + 1):
            y = origin_y + row * cell
            painter.drawLine(origin_x, y, origin_x + canvas_w, y)

        for component in self._editor._components():
            component_id = str(component.get("id") or "")
            pos = component.get("pos", [0, 0, 1, 1])
            col = _safe_int(pos[0], 0)
            row = _safe_int(pos[1], 0)
            col_span = max(1, _safe_int(pos[2], 1))
            row_span = max(1, _safe_int(pos[3], 1))
            x = origin_x + col * cell
            y = origin_y + row * cell
            w = col_span * cell
            h = row_span * cell
            selected = component_id == self._editor._selected_component_id
            fill = QColor("#00b894") if selected else QColor("#1f8bff")
            fill.setAlpha(95 if selected else 70)
            painter.fillRect(x + 1, y + 1, max(1, w - 2), max(1, h - 2), fill)

            border = QPen(QColor("#00ffd5") if selected else QColor("#8ad7ff"))
            border.setWidth(2 if selected else 1)
            painter.setPen(border)
            painter.drawRect(x + 1, y + 1, max(1, w - 2), max(1, h - 2))

            painter.setPen(QColor("#d7f7ff"))
            painter.drawText(x + 6, y + 18, component_id)

        painter.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        self.setFocus()
        hit = self._pick_component(event.position().x(), event.position().y())
        if hit is not None:
            self._editor._selected_component_id = hit
            self._editor._refresh_component_list()
            self._dragging = True
            self._drag_anchor = event.position()
        else:
            self._dragging = False
            self._drag_anchor = None
        self.update()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if not self._dragging or self._drag_anchor is None:
            return super().mouseMoveEvent(event)
        cell = max(1, self._editor._cell_size)
        delta = event.position() - self._drag_anchor
        dx = int(delta.x() // cell)
        dy = int(delta.y() // cell)
        if dx == 0 and dy == 0:
            return
        self._editor._handle_drag(dx, dy)
        self._drag_anchor = event.position()
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._dragging = False
        self._drag_anchor = None
        return super().mouseReleaseEvent(event)

    def wheelEvent(self, event) -> None:  # noqa: N802
        component = self._editor._selected_component()
        if component is None:
            return super().wheelEvent(event)
        delta = event.angleDelta().y()
        if delta == 0:
            return
        direction = 1 if delta > 0 else -1
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self._editor._handle_resize(direction, 0)
        else:
            self._editor._handle_resize(0, direction)
        self.update()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        if key == Qt.Key.Key_Left:
            self._editor._handle_drag(-1, 0)
        elif key == Qt.Key.Key_Right:
            self._editor._handle_drag(1, 0)
        elif key == Qt.Key.Key_Up:
            self._editor._handle_drag(0, -1)
        elif key == Qt.Key.Key_Down:
            self._editor._handle_drag(0, 1)
        elif key in {Qt.Key.Key_BracketLeft, Qt.Key.Key_Minus}:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._editor._handle_resize(0, -1)
            else:
                self._editor._handle_resize(-1, 0)
        elif key in {Qt.Key.Key_BracketRight, Qt.Key.Key_Equal, Qt.Key.Key_Plus}:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._editor._handle_resize(0, 1)
            else:
                self._editor._handle_resize(1, 0)
        else:
            return super().keyPressEvent(event)
        self.update()

    def _pick_component(self, x: float, y: float) -> Optional[str]:
        cols = self._editor._grid_cols
        rows = self._editor._grid_rows
        cell = max(1, self._editor._cell_size)
        canvas_w = cols * cell
        canvas_h = rows * cell
        origin_x = max(0, (self.width() - canvas_w) // 2)
        origin_y = max(0, (self.height() - canvas_h) // 2)
        gx = int((x - origin_x) // cell)
        gy = int((y - origin_y) // cell)
        if gx < 0 or gy < 0 or gx >= cols or gy >= rows:
            return None
        for component in reversed(self._editor._components()):
            component_id = str(component.get("id") or "")
            pos = component.get("pos", [0, 0, 1, 1])
            col = _safe_int(pos[0], 0)
            row = _safe_int(pos[1], 0)
            col_span = max(1, _safe_int(pos[2], 1))
            row_span = max(1, _safe_int(pos[3], 1))
            if col <= gx < col + col_span and row <= gy < row + row_span:
                return component_id
        return None


def _cells_for_pos(col: int, row: int, col_span: int, row_span: int) -> set:
    return {(c, r) for c in range(col, col + col_span) for r in range(row, row + row_span)}


def _safe_int(value: object, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback

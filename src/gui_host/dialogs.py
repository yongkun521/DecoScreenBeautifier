from __future__ import annotations

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

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.resize(420, 240)

    def settings_payload(self) -> dict:
        return {
            "monitor": self.screen_combo.currentData(),
            "use_work_area": self.use_work_area_check.isChecked(),
            "always_on_top": self.always_on_top_check.isChecked(),
            "font_face": self.font_combo.currentFont().family(),
            "font_size": self.font_size_spin.value(),
            "effects_enabled": self.effects_check.isChecked(),
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

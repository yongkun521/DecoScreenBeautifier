from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static

from config.manager import ConfigManager
from core.layout_config import (
    BASE_COMPONENTS,
    add_manual_empty_row,
    build_default_layout,
    cells_for_pos,
    default_span_for_component,
    grid_size_for_layout_class,
    layout_usage,
    remove_manual_empty_row,
    sanitize_layout_data,
)
from core.presets import DEFAULT_TEMPLATE_ID


@dataclass(frozen=True)
class ComponentTool:
    key: str
    label: str
    type_name: str
    base_id: str
    variant: Optional[str] = None
    default_span: Optional[Tuple[int, int]] = None


COMPONENT_TOOLS: List[ComponentTool] = [
    ComponentTool("hardware_dense", "Hardware Monitor - Dense", "HardwareMonitor", "p_hardware", "variant-dense"),
    ComponentTool("hardware_slim", "Hardware Monitor - Slim", "HardwareMonitor", "p_hardware", "variant-slim"),
    ComponentTool("network_ribbon", "Network Monitor - Ribbon", "NetworkMonitor", "p_network", "variant-banner"),
    ComponentTool("network_min", "Network Monitor - Minimal", "NetworkMonitor", "p_network", "variant-minimal"),
    ComponentTool("clock_min", "Clock - Minimal", "ClockWidget", "p_clock", "variant-minimal"),
    ComponentTool("clock_glitch", "Clock - Glitch", "ClockWidget", "p_clock", "variant-dense"),
    ComponentTool("audio_spectrum", "Audio Visualizer - Spectrum", "AudioVisualizer", "p_audio", "variant-banner"),
    ComponentTool("audio_bars", "Audio Visualizer - Bars", "AudioVisualizer", "p_audio", "variant-compact"),
    ComponentTool("image_poster", "Image - Poster", "ImageWidget", "p_image", "variant-compact"),
    ComponentTool("image_matrix", "Image - Matrix", "ImageWidget", "p_image", "variant-slim"),
    ComponentTool("ticker", "Info Ticker", "InfoTicker", "p_ticker", "variant-banner", default_span=(4, 1)),
    ComponentTool("badge", "Status Badge", "StatusBadge", "p_badge", "variant-compact", default_span=(2, 1)),
    ComponentTool("stream", "Signal Stream", "DataStreamWidget", "p_stream", "variant-glow", default_span=(4, 2)),
]

TOKEN_SET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


class EditorScreen(Screen):
    """Layout editor screen."""

    BINDINGS = [
        Binding("escape", "back_to_main", "Back to Display"),
        Binding("s", "save_layout", "Save Layout"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager: Optional[ConfigManager] = None
        self.layout_data: Dict[str, object] = {}
        self.layout_name: str = ""
        self.template: Dict[str, object] = {}
        self.selected_component_id: Optional[str] = None
        self.selected_tool_key: Optional[str] = None
        self._active_theme_class: Optional[str] = None
        self._tool_lookup: Dict[str, ComponentTool] = {tool.key: tool for tool in COMPONENT_TOOLS}

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="editor_layout"):
            with Vertical(id="toolbox"):
                yield Label("Components", id="toolbox_title")
                tool_items = [
                    ListItem(Label(tool.label), id=f"tool_{tool.key}") for tool in COMPONENT_TOOLS
                ]
                yield ListView(*tool_items, id="toolbox_list")
                yield Button("Add Component", variant="primary", id="btn_add")

            with Vertical(id="editor_canvas"):
                yield Label("Layout Preview", id="canvas_title")
                yield Static("", id="canvas_grid")
                yield Label("Components", id="canvas_components_title")
                yield ListView(id="component_list")
                yield Button("Delete Selected", variant="error", id="btn_remove_selected")

            with Vertical(id="properties"):
                yield Label("Properties", id="prop_title")
                yield Static("No component selected.", id="prop_selected")
                yield Label("Grid", classes="prop_section")
                yield Label("", id="prop_grid")
                yield Label("", id="prop_usage")
                with Horizontal(id="grid_row_actions"):
                    yield Button("Add Row", variant="primary", id="btn_add_row")
                    yield Button("Remove Row", variant="warning", id="btn_remove_row")
                yield Label("Position (0-based)", classes="prop_section")
                yield Label("Column", classes="prop_label")
                yield Input(placeholder="Column", id="prop_col")
                yield Label("Row", classes="prop_label")
                yield Input(placeholder="Row", id="prop_row")
                yield Label("Column Span", classes="prop_label")
                yield Input(placeholder="Column Span", id="prop_col_span")
                yield Label("Row Span", classes="prop_label")
                yield Input(placeholder="Row Span", id="prop_row_span")
                yield Label("Image Path (ImageWidget only)", classes="prop_section")
                yield Input(placeholder="Leave blank to use built-in logo", id="prop_image_path")
                yield Button("Apply Changes", variant="primary", id="btn_apply")
                yield Button("Remove Component", variant="error", id="btn_remove")
                yield Button("Save Layout", variant="primary", id="btn_save")
                yield Label("Global Settings", classes="prop_section")
                yield Label("", id="prop_font")
                yield Label("", id="prop_scale")

        yield Footer()

    async def on_mount(self) -> None:
        self._load_layout()
        await self._refresh_editor_state()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id == "toolbox_list":
            self._set_selected_tool(event.item)
        elif event.list_view.id == "component_list":
            self._set_selected_component_from_item(event.item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "toolbox_list":
            self._set_selected_tool(event.item)
        elif event.list_view.id == "component_list":
            self._set_selected_component_from_item(event.item)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn_add":
            await self._handle_add_component()
        elif button_id == "btn_add_row":
            await self._handle_add_row()
        elif button_id == "btn_remove_row":
            await self._handle_remove_row()
        elif button_id == "btn_apply":
            await self._handle_apply_changes()
        elif button_id in {"btn_remove", "btn_remove_selected"}:
            await self._handle_remove_component()
        elif button_id == "btn_save":
            self.action_save_layout()

    def action_back_to_main(self) -> None:
        self.app.pop_screen()

    def action_save_layout(self) -> None:
        if not self.config_manager or not self.layout_name:
            self.notify("No layout to save.")
            return
        self.layout_data = self._sanitize_layout(self.layout_data)
        self.layout_data["template_id"] = self.template.get("id", DEFAULT_TEMPLATE_ID)
        self.layout_data.setdefault("layout_class", self.template.get("layout_class"))
        self.layout_data.setdefault("name", f"Layout {self.layout_name}")
        self.config_manager.save_layout(self.layout_name, self.layout_data)
        self.notify(f"Layout saved: {self.layout_name}")

    def _load_layout(self) -> None:
        self.config_manager = self.app.config_manager if hasattr(self.app, "config_manager") else ConfigManager()
        self.template = self.config_manager.get_active_template() or {}
        template_id = self.template.get("id", DEFAULT_TEMPLATE_ID)
        self.layout_name = template_id
        layout_path = self.config_manager.layouts_dir / f"{self.layout_name}.json5"
        if layout_path.exists():
            layout_data = self.config_manager.load_layout(self.layout_name)
        else:
            layout_data = self._build_default_layout()
        self.layout_data = self._sanitize_layout(layout_data)
        self._apply_theme_class()

    def _build_default_layout(self) -> Dict[str, object]:
        return build_default_layout(self.template)

    def _sanitize_layout(self, layout_data: Dict[str, object]) -> Dict[str, object]:
        return sanitize_layout_data(layout_data, self.template)

    def _apply_theme_class(self) -> None:
        theme_class = self.template.get("theme_class") if self.template else None
        if self._active_theme_class:
            self.remove_class(self._active_theme_class)
        if theme_class:
            self.add_class(theme_class)
        self._active_theme_class = theme_class

    async def _refresh_editor_state(self) -> None:
        if self.selected_component_id is None:
            components = self._components()
            if components:
                self.selected_component_id = components[0].get("id")
        self._refresh_global_settings()
        await self._refresh_component_list()
        self._refresh_canvas()
        self._refresh_property_panel()
        if self.selected_tool_key is None and COMPONENT_TOOLS:
            self.selected_tool_key = COMPONENT_TOOLS[0].key

    def _refresh_global_settings(self) -> None:
        settings = self.config_manager.settings if self.config_manager else {}
        font_preset = settings.get("font_preset", "default")
        style_preset = settings.get("style_preset", "default")
        global_scale = settings.get("global_scale", 1.0)
        used, total, free = layout_usage(self.layout_data)
        manual_rows = max(0, self._safe_int(self.layout_data.get("manual_rows"), 0) or 0)
        self.query_one("#prop_font", Label).update(f"Font Preset: {font_preset} | Style: {style_preset}")
        self.query_one("#prop_scale", Label).update(f"Global Scale: {global_scale}")
        cols, rows = self._grid_size()
        self.query_one("#prop_grid", Label).update(f"{cols} cols x {rows} rows")
        self.query_one("#prop_usage", Label).update(
            f"Occupied: {used}/{total} cells | Free: {free} | Manual blank rows: {manual_rows}"
        )

    async def _refresh_component_list(self) -> None:
        list_view = self.query_one("#component_list", ListView)
        await list_view.clear()
        selected_index = None
        items = []
        for index, component in enumerate(self._components()):
            pos = component.get("pos", [0, 0, 1, 1])
            label = f"{component.get('id')} ({component.get('type')}) [{pos[0]},{pos[1]}] {pos[2]}x{pos[3]}"
            items.append(ListItem(Label(label), id=f"cmp_{component.get('id')}"))
            if component.get("id") == self.selected_component_id:
                selected_index = index
        if items:
            await list_view.extend(items)
        if selected_index is not None:
            list_view.index = selected_index

    def _refresh_canvas(self) -> None:
        canvas = self.query_one("#canvas_grid", Static)
        cols, rows = self._grid_size()
        grid = [["." for _ in range(cols)] for _ in range(rows)]
        token_map = self._component_tokens()
        for component in self._components():
            comp_id = component.get("id")
            if not comp_id:
                continue
            pos = component.get("pos", [0, 0, 1, 1])
            token = token_map.get(comp_id, "?")
            if comp_id == self.selected_component_id:
                token = token.upper()
            for row in range(pos[1], min(rows, pos[1] + pos[3])):
                for col in range(pos[0], min(cols, pos[0] + pos[2])):
                    grid[row][col] = token
        lines = ["   " + "".join(str(col % 10) for col in range(cols))]
        for row in range(rows):
            lines.append(f"{row:02d} " + "".join(grid[row]))
        canvas.update("\n".join(lines))

    def _refresh_property_panel(self) -> None:
        if not self.selected_component_id:
            self.query_one("#prop_selected", Static).update("No component selected.")
            self._set_input_value("#prop_col", "")
            self._set_input_value("#prop_row", "")
            self._set_input_value("#prop_col_span", "")
            self._set_input_value("#prop_row_span", "")
            self._set_input_value("#prop_image_path", "")
            return
        component = self._get_component(self.selected_component_id)
        if not component:
            self.selected_component_id = None
            self.query_one("#prop_selected", Static).update("No component selected.")
            self._set_input_value("#prop_col", "")
            self._set_input_value("#prop_row", "")
            self._set_input_value("#prop_col_span", "")
            self._set_input_value("#prop_row_span", "")
            self._set_input_value("#prop_image_path", "")
            return
        self.query_one("#prop_selected", Static).update(
            f"Selected: {component.get('id')} ({component.get('type')})"
        )
        col, row, col_span, row_span = component.get("pos", [0, 0, 1, 1])
        self._set_input_value("#prop_col", str(col))
        self._set_input_value("#prop_row", str(row))
        self._set_input_value("#prop_col_span", str(col_span))
        self._set_input_value("#prop_row_span", str(row_span))
        if component.get("type") == "ImageWidget":
            self._set_input_value("#prop_image_path", str(component.get("image_path") or ""))
        else:
            self._set_input_value("#prop_image_path", "")

    def _set_selected_tool(self, item: Optional[ListItem]) -> None:
        if not item or not item.id:
            return
        if item.id.startswith("tool_"):
            self.selected_tool_key = item.id.replace("tool_", "", 1)

    def _set_selected_component_from_item(self, item: Optional[ListItem]) -> None:
        component_id = self._component_id_from_item(item)
        if component_id:
            self.selected_component_id = component_id
            self._refresh_canvas()
            self._refresh_property_panel()

    async def _handle_add_component(self) -> None:
        if not self.selected_tool_key or self.selected_tool_key not in self._tool_lookup:
            self.notify("Select a component from the toolbox first.")
            return
        tool = self._tool_lookup[self.selected_tool_key]
        new_component = self._create_component_entry(tool)
        if not new_component:
            return
        self.layout_data.setdefault("components", []).append(new_component)
        self.layout_data = self._sanitize_layout(self.layout_data)
        self.selected_component_id = new_component["id"]
        self._refresh_global_settings()
        await self._refresh_component_list()
        self._refresh_canvas()
        self._refresh_property_panel()

    async def _handle_add_row(self) -> None:
        self.layout_data = add_manual_empty_row(self.layout_data)
        self._refresh_global_settings()
        await self._refresh_component_list()
        self._refresh_canvas()
        self._refresh_property_panel()
        self.notify("Added one blank row.")

    async def _handle_remove_row(self) -> None:
        before = max(0, self._safe_int(self.layout_data.get("manual_rows"), 0) or 0)
        self.layout_data = remove_manual_empty_row(self.layout_data)
        after = max(0, self._safe_int(self.layout_data.get("manual_rows"), 0) or 0)
        self._refresh_global_settings()
        await self._refresh_component_list()
        self._refresh_canvas()
        self._refresh_property_panel()
        if after < before:
            self.notify("Removed one trailing blank row.")
        else:
            self.notify("No manual blank row to remove.")

    async def _handle_apply_changes(self) -> None:
        if not self.selected_component_id:
            self.notify("No component selected.")
            return
        component = self._get_component(self.selected_component_id)
        if not component:
            return
        col = self._safe_int(self._get_input_value("#prop_col"), None)
        row = self._safe_int(self._get_input_value("#prop_row"), None)
        col_span = self._safe_int(self._get_input_value("#prop_col_span"), None)
        row_span = self._safe_int(self._get_input_value("#prop_row_span"), None)
        if None in (col, row, col_span, row_span):
            self.notify("Please enter valid numeric values.")
            return
        if not self._validate_position(self.selected_component_id, col, row, col_span, row_span):
            return
        component["pos"] = [col, row, col_span, row_span]
        image_path = self._get_input_value("#prop_image_path")
        if component.get("type") == "ImageWidget":
            if image_path:
                component["image_path"] = image_path
            else:
                component.pop("image_path", None)
        self.layout_data = self._sanitize_layout(self.layout_data)
        await self._refresh_component_list()
        self._refresh_global_settings()
        self._refresh_canvas()
        self._refresh_property_panel()

    async def _handle_remove_component(self) -> None:
        if not self.selected_component_id:
            self.notify("No component selected.")
            return
        components = self._components()
        current_id = self.selected_component_id
        current_index = 0
        for index, component in enumerate(components):
            if component.get("id") == current_id:
                current_index = index
                break

        remaining = [c for c in components if c.get("id") != current_id]
        self.layout_data["components"] = remaining
        self.layout_data = self._sanitize_layout(self.layout_data)
        remaining = self._components()
        if remaining:
            next_index = min(current_index, len(remaining) - 1)
            self.selected_component_id = str(remaining[next_index].get("id") or "")
        else:
            self.selected_component_id = None
        self._refresh_global_settings()
        await self._refresh_component_list()
        self._refresh_canvas()
        self._refresh_property_panel()
        if current_id:
            self.notify(f"Removed component: {current_id}")

    def _create_component_entry(self, tool: ComponentTool) -> Optional[Dict[str, object]]:
        base_id = tool.base_id
        component_id = self._unique_component_id(base_id)
        layout_class = self.layout_data.get("layout_class")
        col_span, row_span = self._resolve_span(layout_class, tool)
        placement = self._find_slot(col_span, row_span)
        if placement is None:
            used, total, free = layout_usage(self.layout_data)
            self.notify(
                f"No {col_span}x{row_span} slot available. Free cells: {free}/{total}. Move or shrink an existing widget first."
            )
            return None
        col, row = placement
        component = {
            "id": component_id,
            "type": tool.type_name,
            "variant": tool.variant,
            "pos": [col, row, col_span, row_span],
        }
        if tool.type_name == "ImageWidget":
            component["image_path"] = ""
        return component

    def _validate_position(self, component_id: str, col: int, row: int, col_span: int, row_span: int) -> bool:
        cols, rows = self._grid_size()
        if col < 0 or row < 0 or col_span <= 0 or row_span <= 0:
            self.notify("Position values must be zero or greater.")
            return False
        if col + col_span > cols or row + row_span > rows:
            self.notify("Component exceeds grid bounds.")
            return False
        if self._position_conflicts(component_id, col, row, col_span, row_span):
            self.notify("Component overlaps another component.")
            return False
        return True

    def _position_conflicts(self, component_id: str, col: int, row: int, col_span: int, row_span: int) -> bool:
        occupied = set()
        for component in self._components():
            if component.get("id") == component_id:
                continue
            pos = component.get("pos", [0, 0, 1, 1])
            occupied |= self._cells_for_pos(pos[0], pos[1], pos[2], pos[3])
        new_cells = self._cells_for_pos(col, row, col_span, row_span)
        return not occupied.isdisjoint(new_cells)

    def _find_slot(self, col_span: int, row_span: int) -> Optional[Tuple[int, int]]:
        cols, rows = self._grid_size()
        occupied = set()
        for component in self._components():
            pos = component.get("pos", [0, 0, 1, 1])
            occupied |= self._cells_for_pos(pos[0], pos[1], pos[2], pos[3])
        for row in range(rows):
            for col in range(cols):
                if col + col_span > cols or row + row_span > rows:
                    continue
                cells = self._cells_for_pos(col, row, col_span, row_span)
                if occupied.isdisjoint(cells):
                    return col, row
        return None

    def _auto_place_components(self, components: List[Dict[str, object]], cols: int, rows: int) -> None:
        occupied = set()
        for component in components:
            pos = component.get("pos", [0, 0, 1, 1])
            col_span = max(1, self._safe_int(pos[2], 1))
            row_span = max(1, self._safe_int(pos[3], 1))
            placed = False
            for row in range(rows):
                for col in range(cols):
                    if col + col_span > cols or row + row_span > rows:
                        continue
                    cells = self._cells_for_pos(col, row, col_span, row_span)
                    if occupied.isdisjoint(cells):
                        component["pos"] = [col, row, col_span, row_span]
                        occupied |= cells
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                component["pos"] = [0, 0, col_span, row_span]

    def _component_tokens(self) -> Dict[str, str]:
        token_map: Dict[str, str] = {}
        for index, component in enumerate(self._components()):
            comp_id = component.get("id")
            if not comp_id:
                continue
            token = TOKEN_SET[index] if index < len(TOKEN_SET) else "*"
            token_map[comp_id] = token
        return token_map

    def _component_id_from_item(self, item: Optional[ListItem]) -> Optional[str]:
        if not item or not item.id:
            return None
        if item.id.startswith("cmp_"):
            return item.id.replace("cmp_", "", 1)
        return None

    def _unique_component_id(self, base_id: str) -> str:
        existing = {component.get("id") for component in self._components()}
        if base_id not in existing:
            return base_id
        index = 2
        while f"{base_id}_{index}" in existing:
            index += 1
        return f"{base_id}_{index}"

    def _resolve_span(self, layout_class: Optional[str], tool: ComponentTool) -> Tuple[int, int]:
        if tool.default_span:
            return tool.default_span
        return self._default_span(layout_class, tool.base_id)

    def _default_span(self, layout_class: Optional[str], base_id: str) -> Tuple[int, int]:
        return default_span_for_component(layout_class, base_id)

    def _grid_size_for_class(self, layout_class: Optional[str]) -> Tuple[int, int]:
        return grid_size_for_layout_class(layout_class)

    def _grid_size(self) -> Tuple[int, int]:
        grid_size = self.layout_data.get("grid_size", {})
        if isinstance(grid_size, dict):
            cols = self._safe_int(grid_size.get("cols"), 6)
            rows = self._safe_int(grid_size.get("rows"), 4)
        else:
            cols, rows = (6, 4)
        return cols, rows

    def _components(self) -> List[Dict[str, object]]:
        components = self.layout_data.get("components")
        if isinstance(components, list):
            return components
        return []

    def _get_component(self, component_id: str) -> Optional[Dict[str, object]]:
        for component in self._components():
            if component.get("id") == component_id:
                return component
        return None

    def _cells_for_pos(self, col: int, row: int, col_span: int, row_span: int) -> set:
        return cells_for_pos(col, row, col_span, row_span)

    def _set_input_value(self, selector: str, value: str) -> None:
        self.query_one(selector, Input).value = value

    def _get_input_value(self, selector: str) -> str:
        return self.query_one(selector, Input).value.strip()

    def _safe_int(self, value: object, fallback: Optional[int]) -> Optional[int]:
        if value is None:
            return fallback
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

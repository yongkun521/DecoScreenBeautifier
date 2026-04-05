from __future__ import annotations

from typing import Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from components import create_component_widget
from components.base import BaseWidget
from core.layout_config import (
    build_default_layout,
    canonical_component_base_id,
    cells_for_pos,
    sanitize_layout_data,
)

try:
    from utils.startup_trace import trace_startup as _trace_startup
except Exception:
    def _trace_startup(message: str) -> None:
        return None


class _GridSpacer(Static):
    DEFAULT_CSS = """
    _GridSpacer {
        background: transparent;
        border: none;
        padding: 0;
        margin: 0;
    }
    """


class _ErrorTile(Static):
    def __init__(self, component_id: str, type_name: str, error_text: str) -> None:
        message = f"{component_id}: {type_name} unavailable\n{error_text}"
        super().__init__(message, classes="component-error")


class DisplayScreen(Screen):
    """主显示界面，用于展示各类 CLI 组件。"""

    BINDINGS = [
        ("b", "toggle_wt_border", "Toggle Border"),
        ("h", "toggle_header", "Toggle Header"),
        ("m", "toggle_toolbar", "Toggle Toolbar"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._active_template_classes: list[str] = []
        self._built_widget_ids: list[str] = []
        self._header_visible = True
        self._toolbar_visible = True

    def compose(self) -> ComposeResult:
        _trace_startup("display.compose: enter")
        yield Header(show_clock=True, id="app_header")
        yield Grid(id="main_grid")

        with Horizontal(id="bottom_toolbar"):
            yield Button("Zoom -", id="btn_zoom_out", classes="toolbar-btn toolbar-btn-compact")
            yield Button("Zoom +", id="btn_zoom_in", classes="toolbar-btn toolbar-btn-compact")
            yield Button("Border", id="btn_toggle_border", classes="toolbar-btn")
            yield Button("Header", id="btn_toggle_header", classes="toolbar-btn")
            yield Button("Toolbar", id="btn_toggle_toolbar", classes="toolbar-btn")

        yield Footer(id="app_footer")

    async def on_mount(self) -> None:
        _trace_startup("display.on_mount: enter")
        self.title = "DecoScreen :: Main Display"
        await self._reload_from_config()
        self._set_header_visible(self._header_visible)
        self._set_toolbar_visible(self._toolbar_visible)

    async def on_screen_resume(self, _event: events.ScreenResume) -> None:
        await self._reload_from_config()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn_zoom_in":
            self.action_zoom_in()
            return
        if button_id == "btn_zoom_out":
            self.action_zoom_out()
            return
        if button_id == "btn_toggle_border":
            self.action_toggle_wt_border()
            return
        if button_id == "btn_toggle_header":
            self.action_toggle_header()
            return
        if button_id == "btn_toggle_toolbar":
            self.action_toggle_toolbar()
            return

    def on_mouse_down(self, event: events.MouseDown) -> None:
        if self._toolbar_visible:
            return
        try:
            target_id = event.widget.id if event.widget is not None else None
        except Exception:
            target_id = None
        if target_id in {
            "btn_zoom_in",
            "btn_zoom_out",
            "btn_toggle_toolbar",
            "btn_toggle_header",
            "btn_toggle_border",
        }:
            return
        self._set_toolbar_visible(True)
        self.notify("Toolbar restored.")

    def action_zoom_in(self) -> None:
        action = getattr(self.app, "action_zoom_in", None)
        if callable(action):
            action()
            return
        self.notify("Zoom-in action unavailable.")

    def action_zoom_out(self) -> None:
        action = getattr(self.app, "action_zoom_out", None)
        if callable(action):
            action()
            return
        self.notify("Zoom-out action unavailable.")

    def action_toggle_wt_border(self) -> None:
        action = getattr(self.app, "action_toggle_wt_border", None)
        if callable(action):
            action()
            return
        self.notify("Toggle border action unavailable.")

    def action_toggle_header(self) -> None:
        self._set_header_visible(not self._header_visible)
        if self._header_visible:
            self.notify("Title bar shown.")
        else:
            self.notify("Title bar hidden.")

    def action_toggle_toolbar(self) -> None:
        self._set_toolbar_visible(not self._toolbar_visible)
        if self._toolbar_visible:
            self.notify("Toolbar shown.")
            return
        self.notify("Toolbar hidden. Click anywhere to restore.")

    async def _reload_from_config(self) -> None:
        config_manager = getattr(self.app, "config_manager", None)
        if config_manager is None:
            return

        template = config_manager.get_active_template() or {}
        template_id = str(template.get("id") or "")
        _trace_startup(f"display.reload: template={template_id}")

        layout_path = config_manager.layouts_dir / f"{template_id}.json5"
        if layout_path.exists():
            raw_layout = config_manager.load_layout(template_id)
        else:
            raw_layout = build_default_layout(template)
        layout_data = sanitize_layout_data(raw_layout, template)

        self._apply_template_classes(template, layout_data)
        await self._mount_layout_widgets(layout_data)
        self._apply_visual_preset()

    def _apply_template_classes(self, template: dict, layout_data: dict) -> None:
        layout_class = layout_data.get("layout_class") or template.get("layout_class")
        theme_class = template.get("theme_class")
        new_classes = [item for item in (layout_class, theme_class) if item]

        if self._active_template_classes:
            self.remove_class(*self._active_template_classes)
        if new_classes:
            self.add_class(*new_classes)
        self._active_template_classes = new_classes

    async def _mount_layout_widgets(self, layout_data: dict) -> None:
        grid = self.query_one("#main_grid", Grid)
        widgets = self._build_layout_widgets(layout_data)
        async with grid.batch():
            await grid.remove_children("*")
            if widgets:
                await grid.mount_all(widgets)

        _trace_startup("display.layout_widgets: " + ",".join(self._built_widget_ids))

    def _build_layout_widgets(self, layout_data: dict) -> list[Static]:
        self._built_widget_ids = []
        grid_size = layout_data.get("grid_size", {})
        cols = max(1, int(grid_size.get("cols", 1)))
        rows = max(1, int(grid_size.get("rows", 1)))
        components = layout_data.get("components", [])
        if not isinstance(components, list):
            components = []

        start_map: dict[tuple[int, int], dict] = {}
        occupied = set()
        for component in sorted(components, key=self._component_sort_key):
            if not isinstance(component, dict):
                continue
            pos = component.get("pos", [0, 0, 1, 1])
            if not isinstance(pos, list) or len(pos) < 4:
                continue
            col, row, col_span, row_span = (
                int(pos[0]),
                int(pos[1]),
                int(pos[2]),
                int(pos[3]),
            )
            covered = cells_for_pos(col, row, col_span, row_span)
            if not occupied.isdisjoint(covered):
                self.app.log(f"Skipping overlapping component: {component.get('id')}")
                continue
            start_map[(col, row)] = component
            occupied |= covered

        if not start_map:
            boot_hint = Static("[DecoScreen] No widgets enabled for current layout.", id="p_boot_hint")
            boot_hint.styles.column_span = cols
            return [boot_hint]

        rendered: list[Static] = []
        covered_cells = set()
        for row in range(rows):
            for col in range(cols):
                if (col, row) in covered_cells:
                    continue
                component = start_map.get((col, row))
                if component is None:
                    rendered.append(_GridSpacer(classes="grid-spacer"))
                    covered_cells.add((col, row))
                    continue
                widget = self._build_component_widget(component)
                if widget is not None:
                    rendered.append(widget)
                    pos = component.get("pos", [col, row, 1, 1])
                    covered_cells |= cells_for_pos(int(pos[0]), int(pos[1]), int(pos[2]), int(pos[3]))
        return rendered

    def _build_component_widget(self, component: dict) -> Optional[Static]:
        component_id = str(component.get("id") or "").strip()
        type_name = str(component.get("type") or "").strip()
        if not component_id or not type_name:
            return None

        pos = component.get("pos", [0, 0, 1, 1])
        if not isinstance(pos, list) or len(pos) < 4:
            pos = [0, 0, 1, 1]
        col_span = max(1, int(pos[2]))
        row_span = max(1, int(pos[3]))

        try:
            widget = create_component_widget(type_name, component_id, component)
        except Exception as exc:
            self.app.log(
                f"Widget init failed: {component_id}: {type_name}: {type(exc).__name__}: {exc}"
            )
            widget = _ErrorTile(component_id, type_name, f"{type(exc).__name__}: {exc}")

        widget.styles.column_span = col_span
        widget.styles.row_span = row_span

        base_id = canonical_component_base_id(component_id)
        if base_id:
            widget.add_class(f"component-{base_id.replace('p_', '')}")
        variant = str(component.get("variant") or "").strip()
        if variant:
            widget.add_class(variant)

        self._built_widget_ids.append(component_id)
        return widget

    def _apply_visual_preset(self) -> None:
        for widget in self.query(BaseWidget):
            widget.set_visual_preset(getattr(self.app, "visual_preset", {}))
            widget.set_style_preset(getattr(self.app, "style_preset", {}))

    def _set_header_visible(self, visible: bool) -> None:
        self._header_visible = bool(visible)
        try:
            header = self.query_one("#app_header", Header)
        except Exception:
            return
        header.display = self._header_visible

    def _set_toolbar_visible(self, visible: bool) -> None:
        self._toolbar_visible = bool(visible)
        try:
            toolbar = self.query_one("#bottom_toolbar", Horizontal)
        except Exception:
            toolbar = None
        if toolbar is not None:
            toolbar.display = self._toolbar_visible
        try:
            footer = self.query_one("#app_footer", Footer)
        except Exception:
            footer = None
        if footer is not None:
            footer.display = self._toolbar_visible

    @staticmethod
    def _component_sort_key(component: dict) -> tuple[int, int, str]:
        pos = component.get("pos", [0, 0, 1, 1])
        if not isinstance(pos, list) or len(pos) < 4:
            pos = [0, 0, 1, 1]
        return (int(pos[1]), int(pos[0]), str(component.get("id") or ""))

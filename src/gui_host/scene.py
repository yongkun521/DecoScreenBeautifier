from __future__ import annotations

from typing import Dict, Optional

from core.presets import DEFAULT_TEMPLATE_ID, get_font_preset, get_style_preset
from core.renderer import ColorRGB, RenderCell, RenderGrid, TextStyle
from core.retro_effects import apply_retro_effects

from gui_components import create_component
from gui_components.base import GuiComponent, GuiComponentBase, RenderContext
from gui_host.layout import LayoutEngine


class PlaceholderComponent(GuiComponentBase):
    def __init__(self, component_id: str, type_name: str) -> None:
        super().__init__(component_id, title="PLACEHOLDER", update_interval=1.0)
        self._type_name = type_name

    def update_content(self) -> None:
        from rich.align import Align
        from rich.text import Text

        message = Text(f"Missing component: {self._type_name}", style="bold red")
        self.set_renderable(Align.center(message, vertical="middle"))


class GuiScene:
    def __init__(self, config_manager) -> None:
        self.config_manager = config_manager
        self.layout_engine = LayoutEngine()
        self.layout_config: dict = {}
        self.components: Dict[str, GuiComponent] = {}
        self.visual_preset: dict = {}
        self.style_preset: dict = {}
        self.global_scale: float = 1.0
        self._effects_settings: Optional[dict] = None
        self._load_layout()
        self.refresh_presets()

    @property
    def template_id(self) -> str:
        return str(self.config_manager.settings.get("template_id", DEFAULT_TEMPLATE_ID))

    @property
    def template(self) -> dict:
        return self.config_manager.get_template(self.template_id) or {}

    def _load_layout(self) -> None:
        template_id = self.config_manager.settings.get("template_id", DEFAULT_TEMPLATE_ID)
        layout_config = self.config_manager.load_layout(str(template_id))
        if not isinstance(layout_config, dict):
            layout_config = {}
        self.layout_config = layout_config
        self._build_components()

    def _build_components(self) -> None:
        self.components.clear()
        components = self.layout_config.get("components", [])
        if not isinstance(components, list):
            return
        for component in components:
            if not isinstance(component, dict):
                continue
            component_id = str(component.get("id", "")).strip()
            type_name = str(component.get("type", "")).strip()
            if not component_id or not type_name:
                continue
            try:
                instance = create_component(type_name, component_id)
            except KeyError:
                instance = PlaceholderComponent(component_id, type_name)
            self.components[component_id] = instance

    def component_update_counts(self) -> Dict[str, int]:
        result: Dict[str, int] = {}
        for component_id, component in self.components.items():
            update_count = getattr(component, "update_count", 0)
            try:
                result[component_id] = int(update_count)
            except (TypeError, ValueError):
                result[component_id] = 0
        return result

    def refresh_presets(self) -> None:
        settings = self.config_manager.settings
        self.visual_preset = get_font_preset(settings.get("font_preset"))
        self.style_preset = get_style_preset(settings.get("style_preset"))
        try:
            self.global_scale = float(settings.get("global_scale", 1.0))
        except (TypeError, ValueError):
            self.global_scale = 1.0

        gui_settings = settings.get("gui_host", {})
        if not isinstance(gui_settings, dict):
            gui_settings = {}
        effects = gui_settings.get("effects")
        if not isinstance(effects, dict):
            effects = None
        if effects is None:
            terminal_settings = settings.get("terminal_integration", {})
            if isinstance(terminal_settings, dict):
                legacy_effects = terminal_settings.get("deco_effects")
                if isinstance(legacy_effects, dict):
                    effects = legacy_effects
        self._effects_settings = effects

        for component in self.components.values():
            if isinstance(component, GuiComponentBase):
                component.set_visual_preset(self.visual_preset)
                component.set_style_preset(self.style_preset)

    def apply_template(self, template_id: str) -> bool:
        template = self.config_manager.apply_template(template_id)
        if not template:
            return False
        self._load_layout()
        self.refresh_presets()
        return True

    def get_layout_data(self) -> dict:
        return self.layout_config

    def reload_layout(self) -> None:
        self._load_layout()
        self.refresh_presets()

    def update(self, now_ts: float) -> None:
        for component in self.components.values():
            component.update(now_ts)

    def render(self, width: int, height: int, frame_index: int, now_ts: float) -> RenderGrid:
        base_style = self._base_style()
        grid = RenderGrid.empty(width, height, base_style)
        if width <= 0 or height <= 0:
            return grid
        regions = self.layout_engine.compute_regions(width, height, self.layout_config)
        ctx = RenderContext(
            frame_index=frame_index,
            now_ts=now_ts,
            global_scale=self.global_scale,
            style_preset=self.style_preset,
            visual_preset=self.visual_preset,
        )
        for region in regions:
            component = self.components.get(region.component_id)
            if component is None:
                continue
            subgrid = component.render(region.width, region.height, ctx)
            self._blit(grid, subgrid, region.x, region.y)
        if self._effects_settings:
            grid = apply_retro_effects(grid, self._effects_settings, frame_index=frame_index)
        return grid

    def _blit(self, dest: RenderGrid, src: RenderGrid, x_offset: int, y_offset: int) -> None:
        max_y = min(dest.height, y_offset + src.height)
        max_x = min(dest.width, x_offset + src.width)
        for y in range(y_offset, max_y):
            src_row = src.cells[y - y_offset]
            dest_row = dest.cells[y]
            for x in range(x_offset, max_x):
                dest_row[x] = src_row[x - x_offset]

    def _base_style(self) -> Optional[TextStyle]:
        colors = self.style_preset.get("colors", {}) if isinstance(self.style_preset, dict) else {}
        fg_hex = colors.get("primary") or "#00FF41"
        bg_hex = colors.get("background")
        fg = ColorRGB.from_hex(fg_hex) if isinstance(fg_hex, str) else None
        bg = ColorRGB.from_hex(bg_hex) if isinstance(bg_hex, str) else None
        if fg is None and bg is None:
            return None
        return TextStyle(fg=fg, bg=bg)

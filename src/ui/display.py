from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import Screen
from textual.widgets import Static
from textual.widgets import Footer, Header

from components.audio import AudioVisualizer
from components.base import BaseWidget
from components.clock import ClockWidget
from components.hardware import HardwareMonitor
from components.image import ImageWidget
from components.network import NetworkMonitor
from components.status import StatusBadge
from components.stream import DataStreamWidget
from components.ticker import InfoTicker

try:
    from utils.startup_trace import trace_startup as _trace_startup
except Exception:
    def _trace_startup(message: str) -> None:
        return None


class DisplayScreen(Screen):
    """主显示界面，用于展示各类 CLI 组件。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._active_template_classes = []
        self._built_widget_ids = []

    def compose(self) -> ComposeResult:
        _trace_startup("display.compose: enter")
        yield Header(show_clock=True)

        with Grid(id="main_grid"):
            yield Static("[DecoScreen] Loading widgets...", id="p_boot_hint")
            # 按“可失败组件最后挂载”的策略，避免某个组件异常导致整屏空白。
            for widget in self._safe_build_widgets():
                yield widget

        yield Footer()
        _trace_startup(
            "display.compose: yielded widgets="
            + ",".join(self._built_widget_ids)
        )

    def _safe_build_widgets(self):
        specs = [
            ("p_hardware", lambda: HardwareMonitor(id="p_hardware")),
            ("p_network", lambda: NetworkMonitor(id="p_network")),
            ("p_clock", lambda: ClockWidget(id="p_clock")),
            ("p_audio", lambda: AudioVisualizer(id="p_audio")),
            ("p_image", lambda: ImageWidget(id="p_image", image_path="assets/logo.png")),
            ("p_ticker", lambda: InfoTicker(id="p_ticker")),
            ("p_badge", lambda: StatusBadge(id="p_badge")),
            ("p_stream", lambda: DataStreamWidget(id="p_stream")),
        ]
        self._built_widget_ids = []
        for widget_id, factory in specs:
            try:
                widget = factory()
            except Exception as exc:
                # 仅记录，不让单个组件构造失败中断整个应用。
                self.app.log(
                    f"Widget init failed: {widget_id}: {type(exc).__name__}: {exc}"
                )
                _trace_startup(
                    f"display.widget_init_failed: {widget_id}: {type(exc).__name__}: {exc}"
                )
                continue
            self._built_widget_ids.append(widget_id)
            yield widget

    def on_mount(self) -> None:
        _trace_startup("display.on_mount: enter")
        self.title = "DecoScreen :: Main Display"
        if hasattr(self.app, "config_manager"):
            template = self.app.config_manager.get_active_template()
            template_id = template.get("id") if isinstance(template, dict) else None
            _trace_startup(f"display.on_mount: template={template_id}")
            self.apply_template(template)

        widget_count = -1
        try:
            widget_count = len(list(self.query("*")))
        except Exception:
            pass
        _trace_startup(f"display.on_mount: widget_count={widget_count}")

        try:
            self.set_timer(1.0, self._trace_first_paint)
            _trace_startup("display.on_mount: first_paint timer scheduled")
        except Exception as exc:
            _trace_startup(
                f"display.on_mount: failed to schedule first_paint timer: {type(exc).__name__}: {exc}"
            )

    def _trace_first_paint(self) -> None:
        try:
            grid = self.query_one("#main_grid", Grid)
            grid_size = f"{grid.size.width}x{grid.size.height}"
        except Exception:
            grid_size = "<missing>"

        visible_count = 0
        hidden_count = 0
        all_query_count = -1
        base_query_count = -1
        direct_children_count = -1
        direct_child_types = ""
        try:
            for widget in self.query(BaseWidget):
                if widget.display:
                    visible_count += 1
                else:
                    hidden_count += 1
        except Exception:
            pass

        try:
            all_query_count = len(list(self.query("*")))
        except Exception:
            pass
        try:
            base_query_count = len(list(self.query(BaseWidget)))
        except Exception:
            pass
        try:
            direct_children = list(self.children)
            direct_children_count = len(direct_children)
            direct_child_types = ",".join(type(child).__name__ for child in direct_children[:6])
        except Exception:
            pass

        _trace_startup(
            "display.first_paint: "
            f"grid={grid_size} visible_widgets={visible_count} hidden_widgets={hidden_count} "
            f"query_all={all_query_count} query_base={base_query_count} "
            f"direct_children={direct_children_count} child_types={direct_child_types}"
        )

    def apply_template(self, template) -> None:
        if not template:
            return
        layout_class = template.get("layout_class")
        theme_class = template.get("theme_class")
        new_classes = [item for item in (layout_class, theme_class) if item]

        if self._active_template_classes:
            self.remove_class(*self._active_template_classes)
        if new_classes:
            self.add_class(*new_classes)
        self._active_template_classes = new_classes

        self._apply_component_variants(template.get("component_variants", {}))
        self._apply_component_visibility(template.get("active_components"))
        self._apply_visual_preset()

    def _apply_component_variants(self, variants: dict) -> None:
        variant_classes = {
            "variant-dense",
            "variant-slim",
            "variant-compact",
            "variant-minimal",
            "variant-banner",
            "variant-glow",
            "variant-outline",
        }
        for widget in self.query(BaseWidget):
            widget.remove_class(*variant_classes)
        for widget_id, variant in variants.items():
            try:
                widget = self.query_one(f"#{widget_id}", BaseWidget)
            except Exception:
                widget = None
            if widget and variant:
                widget.add_class(variant)

    def _apply_visual_preset(self) -> None:
        for widget in self.query(BaseWidget):
            widget.set_visual_preset(getattr(self.app, "visual_preset", {}))
            widget.set_style_preset(getattr(self.app, "style_preset", {}))

    def _apply_component_visibility(self, active_components) -> None:
        if active_components is None:
            active = {"p_hardware", "p_network", "p_clock", "p_audio", "p_image"}
        else:
            active = set(active_components)
        _trace_startup(
            "display.apply_visibility: active=" + ",".join(sorted(active))
        )
        for widget in self.query(BaseWidget):
            widget.display = widget.id in active

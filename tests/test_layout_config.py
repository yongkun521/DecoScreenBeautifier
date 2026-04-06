import unittest

from components import create_component_widget
from core.layout_config import (
    build_default_layout,
    sanitize_layout_data,
)
from core.presets import get_template


class LayoutConfigTest(unittest.TestCase):
    def test_default_layout_adds_ascii_render_mode_for_image_widget(self) -> None:
        layout = build_default_layout(
            {
                "id": "test_template",
                "layout_class": "layout-wide",
                "active_components": ["p_image"],
            }
        )

        image_component = layout["components"][0]
        self.assertEqual(image_component["type"], "ImageWidget")
        self.assertEqual(image_component["image_render_mode"], "ascii")

    def test_sanitize_layout_keeps_pixel_render_mode_and_backfills_old_layout(self) -> None:
        template = {"id": "test_template", "layout_class": "layout-wide"}

        modern_layout = {
            "template_id": "test_template",
            "layout_class": "layout-wide",
            "grid_size": {"cols": 8, "rows": 4},
            "components": [
                {
                    "id": "p_image",
                    "type": "ImageWidget",
                    "pos": [0, 0, 4, 2],
                    "image_path": "assets/logo.png",
                    "image_display_mode": "fill",
                    "image_render_mode": "pixel",
                }
            ],
        }
        modern_sanitized = sanitize_layout_data(modern_layout, template)
        self.assertEqual(modern_sanitized["components"][0]["image_render_mode"], "pixel")

        legacy_layout = {
            "template_id": "test_template",
            "layout_class": "layout-wide",
            "grid_size": {"cols": 8, "rows": 4},
            "components": [
                {
                    "id": "p_image",
                    "type": "ImageWidget",
                    "pos": [0, 0, 4, 2],
                    "image_path": "assets/logo.png",
                    "image_display_mode": "fit",
                }
            ],
        }
        legacy_sanitized = sanitize_layout_data(legacy_layout, template)
        self.assertEqual(legacy_sanitized["components"][0]["image_render_mode"], "ascii")

    def test_signal_lattice_template_defaults_to_pixel_hero_image(self) -> None:
        template = get_template("signal_lattice_max")
        self.assertIsNotNone(template)

        layout = build_default_layout(template)
        image_component = next(
            component for component in layout["components"] if component["type"] == "ImageWidget"
        )
        self.assertEqual(image_component["image_render_mode"], "pixel")
        self.assertEqual(image_component["image_display_mode"], "fill")
        self.assertEqual(image_component["variant"], "variant-hero")

    def test_create_component_widget_passes_image_render_mode(self) -> None:
        widget = create_component_widget(
            "ImageWidget",
            "p_image",
            {
                "image_path": "assets/logo.png",
                "image_display_mode": "fill",
                "image_render_mode": "pixel",
            },
        )
        self.assertEqual(widget.image_display_mode, "fill")
        self.assertEqual(widget.image_render_mode, "pixel")

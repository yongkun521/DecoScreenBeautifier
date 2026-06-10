import unittest
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

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
        self.assertEqual(image_component["image_effect_mode"], "none")
        self.assertEqual(image_component["image_effect_threshold"], 0.0)
        self.assertEqual(image_component["image_edge_strength"], 0.5)
        self.assertFalse(image_component["image_invert"])

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
                    "image_effect_mode": "silhouette",
                    "image_effect_threshold": 0.45,
                    "image_edge_strength": 0.75,
                    "image_invert": True,
                }
            ],
        }
        modern_sanitized = sanitize_layout_data(modern_layout, template)
        self.assertEqual(modern_sanitized["components"][0]["image_render_mode"], "pixel")
        self.assertEqual(modern_sanitized["components"][0]["image_effect_mode"], "silhouette")
        self.assertEqual(modern_sanitized["components"][0]["image_effect_threshold"], 0.45)
        self.assertEqual(modern_sanitized["components"][0]["image_edge_strength"], 0.75)
        self.assertTrue(modern_sanitized["components"][0]["image_invert"])

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
        self.assertEqual(legacy_sanitized["components"][0]["image_effect_mode"], "none")
        self.assertEqual(legacy_sanitized["components"][0]["image_effect_threshold"], 0.0)
        self.assertEqual(legacy_sanitized["components"][0]["image_edge_strength"], 0.5)
        self.assertFalse(legacy_sanitized["components"][0]["image_invert"])

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
                "image_effect_mode": "edge",
                "image_effect_threshold": 0.25,
                "image_edge_strength": 0.9,
                "image_invert": True,
            },
        )
        self.assertEqual(widget.image_display_mode, "fill")
        self.assertEqual(widget.image_render_mode, "pixel")
        self.assertEqual(widget.image_effect_mode, "edge")
        self.assertEqual(widget.image_effect_threshold, 0.25)
        self.assertEqual(widget.image_edge_strength, 0.9)
        self.assertTrue(widget.image_invert)

    def test_create_v3_graphic_components(self) -> None:
        dot_art = create_component_widget(
            "DotMatrixArtWidget",
            "p_dot_art",
            {
                "image_path": "assets/logo.png",
                "image_render_mode": "pixel",
                "image_effect_mode": "silhouette",
            },
        )
        backdrop = create_component_widget("BackdropPatternWidget", "p_backdrop")
        hud = create_component_widget("HudDecorWidget", "p_hud")

        self.assertEqual(dot_art.image_render_mode, "pixel")
        self.assertEqual(dot_art.image_effect_mode, "silhouette")
        self.assertEqual(backdrop.id, "p_backdrop")
        self.assertEqual(hud.id, "p_hud")

    def test_silhouette_deck_v3_layout_contains_dot_art_defaults(self) -> None:
        template = get_template("silhouette_deck_v3")
        self.assertIsNotNone(template)

        layout = build_default_layout(template)
        dot_art = next(
            component for component in layout["components"] if component["type"] == "DotMatrixArtWidget"
        )
        component_types = {component["type"] for component in layout["components"]}

        self.assertIn("BackdropPatternWidget", component_types)
        self.assertIn("HudDecorWidget", component_types)
        self.assertEqual(dot_art["image_render_mode"], "pixel")
        self.assertEqual(dot_art["image_display_mode"], "fill")
        self.assertEqual(dot_art["image_effect_mode"], "silhouette")
        self.assertEqual(dot_art["variant"], "variant-hero")

    def test_image_widget_loads_gif_frames_for_shared_render_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "anim.gif"
            frame_a = Image.fromarray(np.zeros((4, 4, 3), dtype=np.uint8))
            frame_b = Image.fromarray(np.full((4, 4, 3), 255, dtype=np.uint8))
            frame_a.save(
                image_path,
                save_all=True,
                append_images=[frame_b],
                duration=[90, 130],
                loop=0,
            )

            widget = create_component_widget(
                "ImageWidget",
                "p_image",
                {
                    "image_path": str(image_path),
                    "image_render_mode": "pixel",
                    "image_effect_mode": "duotone",
                },
            )

            self.assertTrue(widget._ensure_media_frames(image_path))
            self.assertEqual(len(widget._media_frames), 2)
            self.assertEqual(len(widget._media_durations), 2)

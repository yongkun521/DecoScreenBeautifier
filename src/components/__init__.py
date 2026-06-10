from __future__ import annotations

from .base import BaseWidget
from .hardware import HardwareMonitor
from .clock import ClockWidget
from .audio import AudioVisualizer
from .image import ImageWidget
from .network import NetworkMonitor
from .status import StatusBadge
from .stream import DataStreamWidget
from .ticker import InfoTicker
from core.layout_config import (
    DEFAULT_IMAGE_EDGE_STRENGTH,
    DEFAULT_IMAGE_EFFECT_MODE,
    DEFAULT_IMAGE_EFFECT_THRESHOLD,
    DEFAULT_IMAGE_DISPLAY_MODE,
    DEFAULT_IMAGE_INVERT,
    DEFAULT_IMAGE_PATH,
    DEFAULT_IMAGE_RENDER_MODE,
    normalize_image_edge_strength,
    normalize_image_effect_mode,
    normalize_image_effect_threshold,
    normalize_image_display_mode,
    normalize_image_invert,
    normalize_image_render_mode,
)

COMPONENT_REGISTRY = {
    "HardwareMonitor": HardwareMonitor,
    "ClockWidget": ClockWidget,
    "AudioVisualizer": AudioVisualizer,
    "ImageWidget": ImageWidget,
    "NetworkMonitor": NetworkMonitor,
    "InfoTicker": InfoTicker,
    "StatusBadge": StatusBadge,
    "DataStreamWidget": DataStreamWidget,
}


def create_component_widget(
    type_name: str,
    component_id: str,
    component_config: dict | None = None,
) -> BaseWidget:
    component_cls = COMPONENT_REGISTRY.get(str(type_name or "").strip())
    if component_cls is None:
        raise KeyError(type_name)

    kwargs = {"id": component_id}
    if component_cls is ImageWidget:
        image_path = ""
        image_display_mode = DEFAULT_IMAGE_DISPLAY_MODE
        image_render_mode = DEFAULT_IMAGE_RENDER_MODE
        image_effect_mode = DEFAULT_IMAGE_EFFECT_MODE
        image_effect_threshold = DEFAULT_IMAGE_EFFECT_THRESHOLD
        image_edge_strength = DEFAULT_IMAGE_EDGE_STRENGTH
        image_invert = DEFAULT_IMAGE_INVERT
        if isinstance(component_config, dict):
            image_path = str(component_config.get("image_path") or "").strip()
            image_display_mode = normalize_image_display_mode(
                component_config.get("image_display_mode")
            )
            image_render_mode = normalize_image_render_mode(
                component_config.get("image_render_mode")
            )
            image_effect_mode = normalize_image_effect_mode(
                component_config.get("image_effect_mode")
            )
            image_effect_threshold = normalize_image_effect_threshold(
                component_config.get("image_effect_threshold")
            )
            image_edge_strength = normalize_image_edge_strength(
                component_config.get("image_edge_strength")
            )
            image_invert = normalize_image_invert(
                component_config.get("image_invert")
            )
        kwargs["image_path"] = image_path or DEFAULT_IMAGE_PATH
        kwargs["image_display_mode"] = image_display_mode
        kwargs["image_render_mode"] = image_render_mode
        kwargs["image_effect_mode"] = image_effect_mode
        kwargs["image_effect_threshold"] = image_effect_threshold
        kwargs["image_edge_strength"] = image_edge_strength
        kwargs["image_invert"] = image_invert
    return component_cls(**kwargs)

__all__ = [
    "BaseWidget",
    "HardwareMonitor",
    "ClockWidget",
    "AudioVisualizer",
    "ImageWidget",
    "NetworkMonitor",
    "InfoTicker",
    "StatusBadge",
    "DataStreamWidget",
    "COMPONENT_REGISTRY",
    "create_component_widget",
]

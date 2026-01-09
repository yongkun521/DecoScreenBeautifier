from __future__ import annotations

from typing import Dict, List, Optional

DEFAULT_FONT_PRESET_ID = "neon_block"
DEFAULT_TEMPLATE_ID = "neon_panorama"

FONT_PRESETS: Dict[str, Dict[str, object]] = {
    "neon_block": {
        "name": "Neon Block",
        "bar_full": "█",
        "bar_empty": "░",
        "sparkline": "▁▂▃▄▅▆▇█",
        "spectrum": [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"],
        "arrow_up": "▲",
        "arrow_down": "▼",
        "image_chars": "@%#*+=-:. ",
    },
    "amber_ascii": {
        "name": "Amber Terminal",
        "bar_full": "#",
        "bar_empty": ".",
        "sparkline": " .:-=+*#",
        "spectrum": [" ", ".", ":", "-", "=", "+", "*", "#"],
        "arrow_up": "^",
        "arrow_down": "v",
        "image_chars": "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
    },
    "ice_thin": {
        "name": "Ice Thin",
        "bar_full": "■",
        "bar_empty": "·",
        "sparkline": " ·.:=+*#",
        "spectrum": [" ", "·", ".", ":", "=", "+", "*", "#"],
        "arrow_up": "↑",
        "arrow_down": "↓",
        "image_chars": "@%#*+=-:. ",
    },
    "mono_dot": {
        "name": "Mono Dot",
        "bar_full": "=",
        "bar_empty": " ",
        "sparkline": " .-:=+*#",
        "spectrum": [" ", ".", "-", "=", "+", "*", "#"],
        "arrow_up": "^",
        "arrow_down": "v",
        "image_chars": "@%#*+=-:. ",
    },
}

TEMPLATE_PRESETS: List[Dict[str, object]] = [
    {
        "id": "neon_panorama",
        "name": "Neon Panorama",
        "description": "超宽横屏信息墙，适合 1920x480 / 2560x720。",
        "screen_profile": "ultrawide",
        "recommended_resolution": "1920x480",
        "layout_class": "layout-ultrawide",
        "theme_class": "theme-neon",
        "font_preset": "neon_block",
        "global_scale": 1.0,
        "tags": ["ultrawide", "cyber", "dashboard"],
        "component_variants": {
            "p_hardware": "variant-dense",
            "p_network": "variant-slim",
            "p_clock": "variant-minimal",
            "p_audio": "variant-banner",
            "p_image": "variant-compact",
        },
    },
    {
        "id": "amber_console",
        "name": "Amber Console",
        "description": "复古终端风格，适合中等宽屏与低分辨率屏幕。",
        "screen_profile": "wide",
        "recommended_resolution": "1280x480",
        "layout_class": "layout-wide",
        "theme_class": "theme-amber",
        "font_preset": "amber_ascii",
        "global_scale": 0.9,
        "tags": ["retro", "wide", "terminal"],
        "component_variants": {
            "p_hardware": "variant-compact",
            "p_network": "variant-minimal",
            "p_clock": "variant-minimal",
            "p_audio": "variant-banner",
            "p_image": "variant-compact",
        },
    },
    {
        "id": "ice_matrix",
        "name": "Ice Matrix",
        "description": "冷色矩阵风格，强调细线与留白。",
        "screen_profile": "wide",
        "recommended_resolution": "1920x540",
        "layout_class": "layout-wide",
        "theme_class": "theme-ice",
        "font_preset": "ice_thin",
        "global_scale": 1.1,
        "tags": ["matrix", "wide", "cool"],
        "component_variants": {
            "p_hardware": "variant-slim",
            "p_network": "variant-slim",
            "p_clock": "variant-minimal",
            "p_audio": "variant-banner",
            "p_image": "variant-slim",
        },
    },
    {
        "id": "signal_column",
        "name": "Signal Column",
        "description": "细长竖屏专用，组件垂直堆叠。",
        "screen_profile": "portrait",
        "recommended_resolution": "480x1280",
        "layout_class": "layout-portrait",
        "theme_class": "theme-neon",
        "font_preset": "neon_block",
        "global_scale": 0.9,
        "tags": ["portrait", "vertical", "stack"],
        "component_variants": {
            "p_hardware": "variant-dense",
            "p_network": "variant-minimal",
            "p_clock": "variant-minimal",
            "p_audio": "variant-compact",
            "p_image": "variant-compact",
        },
    },
    {
        "id": "tower_radar",
        "name": "Tower Radar",
        "description": "高而窄的纵向屏幕，信息自上而下分区。",
        "screen_profile": "tall",
        "recommended_resolution": "400x1200",
        "layout_class": "layout-tall",
        "theme_class": "theme-ice",
        "font_preset": "ice_thin",
        "global_scale": 0.85,
        "tags": ["portrait", "tall", "scanner"],
        "component_variants": {
            "p_hardware": "variant-slim",
            "p_network": "variant-minimal",
            "p_clock": "variant-minimal",
            "p_audio": "variant-compact",
            "p_image": "variant-slim",
        },
    },
    {
        "id": "square_hub",
        "name": "Square Hub",
        "description": "方形小屏多宫格布局，适合 800x800。",
        "screen_profile": "square",
        "recommended_resolution": "800x800",
        "layout_class": "layout-square",
        "theme_class": "theme-amber",
        "font_preset": "amber_ascii",
        "global_scale": 1.0,
        "tags": ["square", "grid", "hub"],
        "component_variants": {
            "p_hardware": "variant-compact",
            "p_network": "variant-compact",
            "p_clock": "variant-minimal",
            "p_audio": "variant-compact",
            "p_image": "variant-compact",
        },
    },
    {
        "id": "mono_strip",
        "name": "Mono Strip",
        "description": "底部状态条式布局，适合超低高度副屏。",
        "screen_profile": "strip",
        "recommended_resolution": "1920x360",
        "layout_class": "layout-strip",
        "theme_class": "theme-mono",
        "font_preset": "mono_dot",
        "global_scale": 0.8,
        "tags": ["strip", "minimal", "status"],
        "component_variants": {
            "p_hardware": "variant-minimal",
            "p_network": "variant-minimal",
            "p_clock": "variant-minimal",
            "p_audio": "variant-banner",
            "p_image": "variant-minimal",
        },
    },
    {
        "id": "neon_grid",
        "name": "Neon Grid",
        "description": "高对比网格布局，强调模块边界与层次。",
        "screen_profile": "wide",
        "recommended_resolution": "1600x600",
        "layout_class": "layout-wide",
        "theme_class": "theme-neon",
        "font_preset": "neon_block",
        "global_scale": 1.0,
        "tags": ["grid", "cyber", "wide"],
        "component_variants": {
            "p_hardware": "variant-dense",
            "p_network": "variant-slim",
            "p_clock": "variant-minimal",
            "p_audio": "variant-banner",
            "p_image": "variant-compact",
        },
    },
]


def list_templates() -> List[Dict[str, object]]:
    return TEMPLATE_PRESETS


def get_template(template_id: Optional[str]) -> Optional[Dict[str, object]]:
    if not template_id:
        return None
    for template in TEMPLATE_PRESETS:
        if template.get("id") == template_id:
            return template
    return None


def get_font_preset(preset_id: Optional[str]) -> Dict[str, object]:
    if not preset_id:
        return FONT_PRESETS[DEFAULT_FONT_PRESET_ID]
    return FONT_PRESETS.get(preset_id, FONT_PRESETS[DEFAULT_FONT_PRESET_ID])


def list_font_presets() -> List[Dict[str, object]]:
    return [{"id": key, "name": value.get("name", key)} for key, value in FONT_PRESETS.items()]

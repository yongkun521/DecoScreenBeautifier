from __future__ import annotations

from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from core.presets import DEFAULT_TEMPLATE_ID

DEFAULT_IMAGE_PATH = "assets/logo.png"

DEFAULT_ACTIVE_COMPONENTS = ["p_hardware", "p_network", "p_clock", "p_audio", "p_image"]

BASE_COMPONENTS: Dict[str, str] = {
    "p_hardware": "HardwareMonitor",
    "p_network": "NetworkMonitor",
    "p_clock": "ClockWidget",
    "p_audio": "AudioVisualizer",
    "p_image": "ImageWidget",
    "p_ticker": "InfoTicker",
    "p_badge": "StatusBadge",
    "p_stream": "DataStreamWidget",
}

LAYOUT_GRID_SIZES: Dict[str, Tuple[int, int]] = {
    "layout-ultrawide": (12, 3),
    "layout-ultrawide-plus": (12, 4),
    "layout-wide": (8, 4),
    "layout-wide-plus": (8, 5),
    "layout-portrait": (4, 8),
    "layout-portrait-plus": (4, 10),
    "layout-tall": (3, 10),
    "layout-square": (6, 6),
    "layout-strip": (12, 2),
    "layout-strip-plus": (12, 3),
}

DEFAULT_SPANS: Dict[str, Dict[str, Tuple[int, int]]] = {
    "layout-ultrawide": {
        "p_hardware": (4, 2),
        "p_network": (4, 1),
        "p_clock": (4, 1),
        "p_audio": (8, 1),
        "p_image": (12, 1),
        "p_ticker": (12, 1),
        "p_badge": (3, 1),
        "p_stream": (4, 2),
    },
    "layout-ultrawide-plus": {
        "p_hardware": (4, 2),
        "p_network": (4, 1),
        "p_clock": (4, 1),
        "p_audio": (8, 1),
        "p_image": (12, 1),
        "p_ticker": (9, 1),
        "p_badge": (3, 1),
        "p_stream": (6, 1),
    },
    "layout-wide": {
        "p_hardware": (4, 2),
        "p_network": (4, 1),
        "p_clock": (4, 1),
        "p_audio": (8, 1),
        "p_image": (8, 1),
        "p_ticker": (8, 1),
        "p_badge": (2, 1),
        "p_stream": (4, 2),
    },
    "layout-wide-plus": {
        "p_hardware": (4, 2),
        "p_network": (4, 1),
        "p_clock": (4, 1),
        "p_audio": (8, 1),
        "p_image": (8, 1),
        "p_ticker": (8, 1),
        "p_badge": (2, 1),
        "p_stream": (8, 1),
    },
    "layout-portrait": {
        "p_hardware": (4, 2),
        "p_network": (4, 1),
        "p_clock": (4, 1),
        "p_audio": (4, 2),
        "p_image": (4, 2),
        "p_ticker": (4, 1),
        "p_badge": (4, 1),
        "p_stream": (4, 2),
    },
    "layout-portrait-plus": {
        "p_hardware": (4, 3),
        "p_network": (4, 1),
        "p_clock": (4, 1),
        "p_audio": (4, 2),
        "p_image": (4, 2),
        "p_ticker": (4, 1),
        "p_badge": (4, 1),
        "p_stream": (4, 4),
    },
    "layout-tall": {
        "p_hardware": (3, 3),
        "p_network": (3, 1),
        "p_clock": (3, 1),
        "p_audio": (3, 3),
        "p_image": (3, 2),
        "p_ticker": (3, 1),
        "p_badge": (3, 1),
        "p_stream": (3, 3),
    },
    "layout-square": {
        "p_hardware": (3, 2),
        "p_network": (3, 1),
        "p_clock": (3, 1),
        "p_audio": (6, 1),
        "p_image": (6, 3),
        "p_ticker": (6, 1),
        "p_badge": (6, 1),
        "p_stream": (6, 2),
    },
    "layout-strip": {
        "p_hardware": (3, 1),
        "p_network": (3, 1),
        "p_clock": (3, 1),
        "p_audio": (3, 1),
        "p_image": (12, 1),
        "p_ticker": (12, 1),
        "p_badge": (3, 1),
        "p_stream": (6, 1),
    },
    "layout-strip-plus": {
        "p_hardware": (4, 1),
        "p_network": (6, 1),
        "p_clock": (6, 1),
        "p_audio": (12, 1),
        "p_image": (12, 1),
        "p_ticker": (9, 1),
        "p_badge": (3, 1),
        "p_stream": (12, 1),
    },
}


def canonical_component_base_id(component_id: object) -> Optional[str]:
    text = str(component_id or "").strip()
    if not text:
        return None
    for base_id in sorted(BASE_COMPONENTS, key=len, reverse=True):
        if text == base_id or text.startswith(f"{base_id}_"):
            return base_id
    return None


def grid_size_for_layout_class(layout_class: Optional[str]) -> Tuple[int, int]:
    return LAYOUT_GRID_SIZES.get(str(layout_class or ""), (6, 4))


def default_span_for_component(layout_class: Optional[str], component_id: str) -> Tuple[int, int]:
    base_id = canonical_component_base_id(component_id) or component_id
    spans = DEFAULT_SPANS.get(str(layout_class or ""), {})
    return spans.get(base_id, (2, 1))


def build_default_layout(template: Optional[dict]) -> Dict[str, object]:
    template = template or {}
    template_id = str(template.get("id") or DEFAULT_TEMPLATE_ID)
    layout_class = template.get("layout_class")
    cols, rows = grid_size_for_layout_class(layout_class)
    variant_map = template.get("component_variants", {})
    if not isinstance(variant_map, dict):
        variant_map = {}

    active_components = template.get("active_components")
    if not isinstance(active_components, list):
        active_components = DEFAULT_ACTIVE_COMPONENTS

    components: List[Dict[str, object]] = []
    for base_id in active_components:
        type_name = BASE_COMPONENTS.get(str(base_id))
        if not type_name:
            continue
        col_span, row_span = default_span_for_component(layout_class, str(base_id))
        component: Dict[str, object] = {
            "id": str(base_id),
            "type": type_name,
            "variant": variant_map.get(str(base_id)),
            "pos": [0, 0, col_span, row_span],
        }
        if type_name == "ImageWidget":
            component["image_path"] = DEFAULT_IMAGE_PATH
        components.append(component)

    _auto_place_components(components, cols, rows)
    return {
        "name": f"Layout {template.get('name', template_id)}",
        "template_id": template_id,
        "layout_class": layout_class,
        "grid_size": {"cols": cols, "rows": rows},
        "components": components,
    }


def sanitize_layout_data(layout_data: object, template: Optional[dict]) -> Dict[str, object]:
    if not isinstance(layout_data, dict):
        return build_default_layout(template)

    template = template or {}
    layout = deepcopy(layout_data)
    layout_class = layout.get("layout_class") or template.get("layout_class")

    grid_size = layout.get("grid_size", {})
    if not isinstance(grid_size, dict):
        grid_size = {}
    cols = _safe_int(grid_size.get("cols"), 0)
    rows = _safe_int(grid_size.get("rows"), 0)
    if cols <= 0 or rows <= 0:
        cols, rows = grid_size_for_layout_class(layout_class)

    layout["grid_size"] = {"cols": cols, "rows": rows}
    layout["layout_class"] = layout_class
    layout.setdefault("template_id", template.get("id", DEFAULT_TEMPLATE_ID))
    layout.setdefault("name", f"Layout {layout.get('template_id', DEFAULT_TEMPLATE_ID)}")

    raw_components = layout.get("components")
    if not isinstance(raw_components, list):
        raw_components = []

    occupied = set()
    seen_ids: set[str] = set()
    clean_components: List[Dict[str, object]] = []
    for raw_component in raw_components:
        if not isinstance(raw_component, dict):
            continue
        component = deepcopy(raw_component)
        component_id = str(component.get("id") or "").strip()
        if not component_id or component_id in seen_ids:
            continue

        base_id = canonical_component_base_id(component_id)
        type_name = str(component.get("type") or "").strip()
        if not type_name and base_id:
            type_name = BASE_COMPONENTS.get(base_id, "")
        if not type_name:
            continue

        pos = component.get("pos", [0, 0, 1, 1])
        if not isinstance(pos, list):
            pos = [0, 0, 1, 1]
        while len(pos) < 4:
            pos.append(1)

        col = max(0, min(cols - 1, _safe_int(pos[0], 0)))
        row = max(0, min(rows - 1, _safe_int(pos[1], 0)))
        col_span = max(1, min(cols - col, _safe_int(pos[2], 1)))
        row_span = max(1, min(rows - row, _safe_int(pos[3], 1)))

        placed = _place_or_find_slot(occupied, cols, rows, col, row, col_span, row_span)
        if placed is None:
            continue

        component["id"] = component_id
        component["type"] = type_name
        component["pos"] = [placed[0], placed[1], placed[2], placed[3]]
        if type_name != "ImageWidget":
            component.pop("image_path", None)

        seen_ids.add(component_id)
        occupied |= cells_for_pos(*placed)
        clean_components.append(component)

    layout["components"] = clean_components
    return layout


def layout_usage(layout_data: object) -> Tuple[int, int, int]:
    if not isinstance(layout_data, dict):
        return (0, 0, 0)
    grid_size = layout_data.get("grid_size", {})
    if not isinstance(grid_size, dict):
        return (0, 0, 0)
    cols = max(0, _safe_int(grid_size.get("cols"), 0))
    rows = max(0, _safe_int(grid_size.get("rows"), 0))
    if cols <= 0 or rows <= 0:
        return (0, 0, 0)

    occupied = set()
    components = layout_data.get("components")
    if isinstance(components, list):
        for component in components:
            if not isinstance(component, dict):
                continue
            pos = component.get("pos", [0, 0, 1, 1])
            if not isinstance(pos, list):
                continue
            while len(pos) < 4:
                pos.append(1)
            col = max(0, min(cols - 1, _safe_int(pos[0], 0)))
            row = max(0, min(rows - 1, _safe_int(pos[1], 0)))
            col_span = max(1, min(cols - col, _safe_int(pos[2], 1)))
            row_span = max(1, min(rows - row, _safe_int(pos[3], 1)))
            occupied |= cells_for_pos(col, row, col_span, row_span)

    total = cols * rows
    used = len(occupied)
    return used, total, max(0, total - used)


def cells_for_pos(col: int, row: int, col_span: int, row_span: int) -> set[tuple[int, int]]:
    return {
        (c, r)
        for c in range(col, col + col_span)
        for r in range(row, row + row_span)
    }


def _auto_place_components(components: List[Dict[str, object]], cols: int, rows: int) -> None:
    occupied = set()
    for component in components:
        pos = component.get("pos", [0, 0, 1, 1])
        if not isinstance(pos, list):
            pos = [0, 0, 1, 1]
        while len(pos) < 4:
            pos.append(1)
        col_span = max(1, _safe_int(pos[2], 1))
        row_span = max(1, _safe_int(pos[3], 1))
        placed = _find_first_available_slot(occupied, cols, rows, col_span, row_span)
        if placed is None:
            component["pos"] = [0, 0, col_span, row_span]
            continue
        component["pos"] = [placed[0], placed[1], col_span, row_span]
        occupied |= cells_for_pos(placed[0], placed[1], col_span, row_span)


def _place_or_find_slot(
    occupied: set[tuple[int, int]],
    cols: int,
    rows: int,
    col: int,
    row: int,
    col_span: int,
    row_span: int,
) -> Optional[Tuple[int, int, int, int]]:
    requested = cells_for_pos(col, row, col_span, row_span)
    if occupied.isdisjoint(requested):
        return (col, row, col_span, row_span)

    placed = _find_first_available_slot(occupied, cols, rows, col_span, row_span)
    if placed is None:
        return None
    return (placed[0], placed[1], col_span, row_span)


def _find_first_available_slot(
    occupied: set[tuple[int, int]],
    cols: int,
    rows: int,
    col_span: int,
    row_span: int,
) -> Optional[Tuple[int, int]]:
    for row in range(rows):
        for col in range(cols):
            if col + col_span > cols or row + row_span > rows:
                continue
            target = cells_for_pos(col, row, col_span, row_span)
            if occupied.isdisjoint(target):
                return (col, row)
    return None


def _safe_int(value: object, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List


@dataclass(frozen=True)
class LayoutRegion:
    component_id: str
    type_name: str
    x: int
    y: int
    width: int
    height: int
    variant: str = ""


class LayoutEngine:
    def compute_regions(
        self,
        grid_width: int,
        grid_height: int,
        layout_config: dict,
    ) -> List[LayoutRegion]:
        if grid_width <= 0 or grid_height <= 0:
            return []
        grid_size = layout_config.get("grid_size", {}) if isinstance(layout_config, dict) else {}
        cols = _safe_int(grid_size.get("cols"), 1)
        rows = _safe_int(grid_size.get("rows"), 1)
        cols = max(1, cols)
        rows = max(1, rows)

        col_sizes = _split_sizes(grid_width, cols)
        row_sizes = _split_sizes(grid_height, rows)
        col_starts = _prefix_sums(col_sizes)
        row_starts = _prefix_sums(row_sizes)

        regions: List[LayoutRegion] = []
        components = layout_config.get("components", []) if isinstance(layout_config, dict) else []
        if not isinstance(components, list):
            return regions
        for component in components:
            if not isinstance(component, dict):
                continue
            component_id = str(component.get("id", "")).strip()
            type_name = str(component.get("type", "")).strip()
            if not component_id or not type_name:
                continue
            pos = component.get("pos", [0, 0, 1, 1])
            if not isinstance(pos, list):
                pos = [0, 0, 1, 1]
            while len(pos) < 4:
                pos.append(1)
            col = max(0, _safe_int(pos[0], 0))
            row = max(0, _safe_int(pos[1], 0))
            col_span = max(1, _safe_int(pos[2], 1))
            row_span = max(1, _safe_int(pos[3], 1))
            if col >= cols or row >= rows:
                continue
            col_span = min(col_span, cols - col)
            row_span = min(row_span, rows - row)
            x = col_starts[col]
            y = row_starts[row]
            width = sum(col_sizes[col : col + col_span])
            height = sum(row_sizes[row : row + row_span])
            if width <= 0 or height <= 0:
                continue
            regions.append(
                LayoutRegion(
                    component_id=component_id,
                    type_name=type_name,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    variant=str(component.get("variant", "") or ""),
                )
            )
        return regions


def _safe_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _split_sizes(total: int, count: int) -> List[int]:
    if count <= 0:
        return []
    base = total // count
    remainder = total % count
    sizes = [base for _ in range(count)]
    for i in range(remainder):
        sizes[i] += 1
    return sizes


def _prefix_sums(values: Iterable[int]) -> List[int]:
    total = 0
    starts = []
    for value in values:
        starts.append(total)
        total += value
    return starts

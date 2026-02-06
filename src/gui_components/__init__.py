from .base import GuiComponent, GuiComponentBase, RenderContext
from .clock import ClockComponent
from .hardware import HardwareComponent
from .network import NetworkComponent

COMPONENT_REGISTRY = {
    "HardwareMonitor": HardwareComponent,
    "ClockWidget": ClockComponent,
    "NetworkMonitor": NetworkComponent,
}


def create_component(type_name: str, component_id: str) -> GuiComponent:
    component_cls = COMPONENT_REGISTRY.get(type_name)
    if component_cls is None:
        raise KeyError(type_name)
    return component_cls(component_id=component_id)

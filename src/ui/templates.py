from textual.screen import Screen
from textual.containers import Grid, Vertical
from textual.widgets import Header, Footer, Button, Label, ListView, ListItem
from textual.app import ComposeResult
from config.manager import ConfigManager

class TemplateScreen(Screen):
    """
    模板选择界面
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()

    def compose(self) -> ComposeResult:
        """构建模板界面布局"""
        yield Header()
        
        with Vertical(id="template_layout"):
            yield Label("Select a Template", id="template_title")
            
            # 获取所有布局/模板
            layouts = self.config_manager.list_layouts()
            if not layouts:
                layouts = ["Default (Built-in)"]
            
            items = []
            for layout in layouts:
                # Sanitize id: replace non-alphanumeric with underscore
                safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in layout)
                items.append(ListItem(Label(layout), id=f"tpl_{safe_id}"))

            yield ListView(
                *items,
                id="template_list"
            )
            
            with Grid(id="template_actions"):
                yield Button("Apply", variant="success", id="btn_apply")
                yield Button("Cancel", variant="error", id="btn_cancel")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.app.pop_screen()
        elif event.button.id == "btn_apply":
            # 实际应用逻辑需要配合主界面重新加载
            self.notify("Template applied (mock)")
            self.app.pop_screen()

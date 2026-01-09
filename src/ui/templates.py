from textual.screen import Screen
from textual.containers import Grid, Vertical
from textual.widgets import Header, Footer, Button, Label, ListView, ListItem, Static
from textual.app import ComposeResult
from config.manager import ConfigManager

class TemplateScreen(Screen):
    """
    模板选择界面
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = None
        self._templates = []
        self._template_lookup = {}
        self._selected_template_id = None

    def compose(self) -> ComposeResult:
        """构建模板界面布局"""
        yield Header()
        
        with Vertical(id="template_layout"):
            yield Label("Select a Template", id="template_title")
            
            # 获取所有模板
            self.config_manager = self.app.config_manager if hasattr(self.app, "config_manager") else ConfigManager()
            self._templates = self.config_manager.list_templates()
            self._template_lookup = {tpl["id"]: tpl for tpl in self._templates}
            self._selected_template_id = self.config_manager.settings.get("template_id")

            items = []
            for template in self._templates:
                template_id = template["id"]
                label_text = f"{template['name']} · {template['screen_profile']} · {', '.join(template['tags'])}"
                items.append(ListItem(Label(label_text), id=f"tpl_{template_id}"))

            yield ListView(*items, id="template_list")
            yield Static("", id="template_desc")
            
            with Grid(id="template_actions"):
                yield Button("Apply", variant="success", id="btn_apply")
                yield Button("Cancel", variant="error", id="btn_cancel")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.app.pop_screen()
        elif event.button.id == "btn_apply":
            template_id = self._selected_template_id
            if template_id:
                self.app.apply_template(template_id)
                self.notify(f"Template applied: {template_id}")
            else:
                self.notify("No template selected.")
            self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id if event.item else None
        if not item_id:
            return
        template_id = item_id.replace("tpl_", "")
        if template_id in self._template_lookup:
            self._selected_template_id = template_id
            desc = self._template_lookup[template_id].get("description", "")
            desc_widget = self.query_one("#template_desc", Static)
            desc_widget.update(desc)

    def on_mount(self) -> None:
        if self._selected_template_id in self._template_lookup:
            desc = self._template_lookup[self._selected_template_id].get("description", "")
            desc_widget = self.query_one("#template_desc", Static)
            desc_widget.update(desc)

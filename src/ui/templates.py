from textual.screen import Screen
from textual.containers import Grid, Vertical
from textual.widgets import Header, Footer, Button, Label, ListView, ListItem, Static, Select
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
        self._filter_profile = "all"
        self._filter_purpose = "all"
        self._filter_style = "all"

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

            with Grid(id="template_filters"):
                yield Select(
                    self._build_filter_options("screen_profile"),
                    prompt="Profile",
                    value=self._filter_profile,
                    allow_blank=False,
                    id="filter_profile",
                )
                yield Select(
                    self._build_filter_options("purpose_tags"),
                    prompt="Purpose",
                    value=self._filter_purpose,
                    allow_blank=False,
                    id="filter_purpose",
                )
                yield Select(
                    self._build_filter_options("style_tags"),
                    prompt="Style",
                    value=self._filter_style,
                    allow_blank=False,
                    id="filter_style",
                )

            yield ListView(id="template_list")
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
            self._update_description(template_id)

    async def on_mount(self) -> None:
        await self._refresh_template_list(keep_selection=True)

    async def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "filter_profile":
            self._filter_profile = event.value
        elif event.select.id == "filter_purpose":
            self._filter_purpose = event.value
        elif event.select.id == "filter_style":
            self._filter_style = event.value
        await self._refresh_template_list(keep_selection=False)

    def _build_filter_options(self, key: str) -> list[tuple[str, str]]:
        values = set()
        for template in self._templates:
            if key == "screen_profile":
                value = template.get("screen_profile")
                if value:
                    values.add(value)
            else:
                for tag in template.get(key, []):
                    values.add(tag)
        options = [("All", "all")]
        for value in sorted(values):
            label = str(value).replace("_", " ").title()
            options.append((label, str(value)))
        return options

    def _filtered_templates(self) -> list:
        result = []
        for template in self._templates:
            if self._filter_profile != "all" and template.get("screen_profile") != self._filter_profile:
                continue
            if self._filter_purpose != "all" and self._filter_purpose not in template.get("purpose_tags", []):
                continue
            if self._filter_style != "all" and self._filter_style not in template.get("style_tags", []):
                continue
            result.append(template)
        return result

    def _template_label(self, template: dict) -> str:
        purpose = "/".join(template.get("purpose_tags", []))
        style = "/".join(template.get("style_tags", []))
        return f"{template['name']} · {template['screen_profile']} · {purpose} · {style}"

    async def _refresh_template_list(self, keep_selection: bool = True) -> None:
        list_view = self.query_one("#template_list", ListView)
        templates = self._filtered_templates()
        await list_view.clear()
        selected_index = None
        items = []
        for index, template in enumerate(templates):
            items.append(ListItem(Label(self._template_label(template)), id=f"tpl_{template['id']}"))
            if keep_selection and template.get("id") == self._selected_template_id:
                selected_index = index
        if items:
            await list_view.extend(items)
        if templates and selected_index is None:
            self._selected_template_id = templates[0]["id"]
            selected_index = 0
        if selected_index is not None:
            list_view.index = selected_index
            self._update_description(self._selected_template_id)
        else:
            self._selected_template_id = None
            self.query_one("#template_desc", Static).update("No templates match the current filters.")

    def _update_description(self, template_id: str) -> None:
        template = self._template_lookup.get(template_id, {})
        desc = template.get("description", "")
        resolution = template.get("recommended_resolution", "-")
        profile = template.get("screen_profile", "-")
        purpose = ", ".join(template.get("purpose_tags", []))
        style = ", ".join(template.get("style_tags", []))
        detail = f"{desc}\nProfile: {profile} · Resolution: {resolution}\nPurpose: {purpose} · Style: {style}"
        desc_widget = self.query_one("#template_desc", Static)
        desc_widget.update(detail)

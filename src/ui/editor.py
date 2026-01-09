from textual.screen import Screen
from textual.containers import Grid, Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Label, ListView, ListItem, Static
from textual.app import ComposeResult
from textual.binding import Binding

class EditorScreen(Screen):
    """
    可视化编辑器界面
    """
    
    BINDINGS = [
        Binding("escape", "back_to_main", "Back to Display"),
        Binding("s", "save_layout", "Save Layout"),
    ]

    def compose(self) -> ComposeResult:
        """构建编辑器布局"""
        yield Header()
        
        settings = self.app.config_manager.settings if hasattr(self.app, "config_manager") else {}
        font_preset = settings.get("font_preset", "default")
        global_scale = settings.get("global_scale", 1.0)

        with Horizontal(id="editor_layout"):
            # 左侧工具箱
            with Vertical(id="toolbox"):
                yield Label("Components", id="toolbox_title")
                yield ListView(
                    ListItem(Label("Hardware Monitor · Dense"), id="tool_hardware_dense"),
                    ListItem(Label("Hardware Monitor · Slim"), id="tool_hardware_slim"),
                    ListItem(Label("Network Monitor · Ribbon"), id="tool_network_ribbon"),
                    ListItem(Label("Network Monitor · Minimal"), id="tool_network_min"),
                    ListItem(Label("Clock · Minimal"), id="tool_clock_min"),
                    ListItem(Label("Clock · Glitch"), id="tool_clock_glitch"),
                    ListItem(Label("Audio Visualizer · Spectrum"), id="tool_audio_spectrum"),
                    ListItem(Label("Audio Visualizer · Bars"), id="tool_audio_bars"),
                    ListItem(Label("Image · Poster"), id="tool_image_poster"),
                    ListItem(Label("Image · Matrix"), id="tool_image_matrix"),
                    ListItem(Label("Info Ticker"), id="tool_ticker"),
                    ListItem(Label("Status Badge"), id="tool_badge"),
                )
                yield Button("Add Component", variant="primary", id="btn_add")

            # 中间编辑区域 (模拟预览)
            with Static(id="editor_canvas"):
                yield Label("Editor Canvas (Drag & Drop not fully implemented yet)", id="canvas_hint")
                # 这里应该加载当前的布局组件，但为了简化，暂时留空或显示网格
                
            # 右侧属性面板
            with Vertical(id="properties"):
                yield Label("Properties", id="prop_title")
                yield Label("Select a component to edit", id="prop_hint")
                yield Label("Global Settings", id="prop_section")
                yield Label(f"Font Preset: {font_preset}", id="prop_font")
                yield Label(f"Global Scale: {global_scale}", id="prop_scale")
                # 属性控件将动态生成

        yield Footer()

    def action_back_to_main(self) -> None:
        """返回主界面"""
        self.app.pop_screen()

    def action_save_layout(self) -> None:
        """保存布局"""
        self.notify("Layout saved (mock)")

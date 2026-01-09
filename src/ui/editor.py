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
        
        with Horizontal(id="editor_layout"):
            # 左侧工具箱
            with Vertical(id="toolbox"):
                yield Label("Components", id="toolbox_title")
                yield ListView(
                    ListItem(Label("Hardware Monitor"), id="tool_hardware"),
                    ListItem(Label("Clock"), id="tool_clock"),
                    ListItem(Label("Audio Visualizer"), id="tool_audio"),
                    ListItem(Label("Image"), id="tool_image"),
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
                # 属性控件将动态生成

        yield Footer()

    def action_back_to_main(self) -> None:
        """返回主界面"""
        self.app.pop_screen()

    def action_save_layout(self) -> None:
        """保存布局"""
        self.notify("Layout saved (mock)")

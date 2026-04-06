from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class UnsavedChangesDialog(ModalScreen[str]):
    """Confirm how to handle unsaved editor changes."""

    DEFAULT_CSS = """
    UnsavedChangesDialog {
        align: center middle;
    }

    #unsaved_changes_dialog {
        width: 64;
        max-width: 92%;
        border: heavy $warning;
        background: $surface;
        padding: 1 2;
    }

    #unsaved_changes_title {
        text-style: bold;
        margin-bottom: 1;
    }

    #unsaved_changes_message {
        margin-bottom: 1;
    }

    #unsaved_changes_actions {
        layout: horizontal;
        height: auto;
    }

    #unsaved_changes_actions Button {
        width: 1fr;
        margin-right: 1;
    }

    #unsaved_changes_actions Button:last-child {
        margin-right: 0;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Keep Editing", show=False),
    ]

    def __init__(self, *, title: str, message: str) -> None:
        super().__init__()
        self._title = title
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="unsaved_changes_dialog"):
            yield Label(self._title, id="unsaved_changes_title")
            yield Static(self._message, id="unsaved_changes_message")
            with Horizontal(id="unsaved_changes_actions"):
                yield Button("Save and Exit", variant="success", id="btn_dialog_save")
                yield Button("Discard", variant="warning", id="btn_dialog_discard")
                yield Button("Keep Editing", variant="primary", id="btn_dialog_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_dialog_save":
            self.dismiss("save")
        elif event.button.id == "btn_dialog_discard":
            self.dismiss("discard")
        else:
            self.dismiss("cancel")

    def action_cancel(self) -> None:
        self.dismiss("cancel")

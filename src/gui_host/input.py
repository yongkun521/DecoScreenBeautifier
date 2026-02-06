from PySide6.QtCore import Qt

KEY_ACTIONS = {
    Qt.Key.Key_Q: "quit",
    Qt.Key.Key_D: "toggle_dark",
    Qt.Key.Key_E: "toggle_editor",
    Qt.Key.Key_T: "toggle_templates",
    Qt.Key.Key_S: "toggle_settings",
}


def action_from_key(event) -> str:
    key = event.key()
    if key in KEY_ACTIONS:
        return KEY_ACTIONS[key]
    text = event.text().lower() if event.text() else ""
    return {
        "q": "quit",
        "d": "toggle_dark",
        "e": "toggle_editor",
        "t": "toggle_templates",
        "s": "toggle_settings",
    }.get(text, "")

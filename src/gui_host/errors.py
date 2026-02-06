import sys


def show_fatal_error(title: str, message: str, details: str = "") -> None:
    try:
        from PySide6.QtWidgets import QMessageBox

        text = message
        if details:
            text = f"{message}\n\n{details}"
        QMessageBox.critical(None, title, text)
    except Exception:
        sys.stderr.write(f"{title}: {message}\n")
        if details:
            sys.stderr.write(f"{details}\n")

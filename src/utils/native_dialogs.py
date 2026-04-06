from __future__ import annotations

import subprocess
import sys
from pathlib import Path


IMAGE_FILE_FILTER = (
    "Image Files|*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp;*.tiff;*.tif|All Files|*.*"
)


def browse_for_image_file(initial_path: str | None = None) -> str | None:
    if sys.platform == "win32":
        return _browse_for_image_file_windows(initial_path)
    return _browse_for_image_file_tk(initial_path)


def read_system_clipboard() -> str:
    if sys.platform == "win32":
        return _read_system_clipboard_windows()
    return _read_system_clipboard_tk()


def normalize_path_text(text: str | None) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return ""

    candidate = lines[0].strip().strip('"').strip("'")
    lowered = candidate.lower()
    if lowered.startswith("file:///"):
        candidate = candidate[8:]
    elif lowered.startswith("file://"):
        candidate = candidate[7:]
    return candidate


def _browse_for_image_file_windows(initial_path: str | None) -> str | None:
    initial_directory = _resolve_initial_directory(initial_path)
    initial_directory_assignment = ""
    if initial_directory:
        initial_directory_assignment = (
            f"$dialog.InitialDirectory = {_powershell_quote(initial_directory)}\n"
        )

    script = f"""
Add-Type -AssemblyName System.Windows.Forms
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = 'Select an image for DecoScreenBeautifier'
$dialog.Filter = {_powershell_quote(IMAGE_FILE_FILTER)}
$dialog.CheckFileExists = $true
$dialog.Multiselect = $false
{initial_directory_assignment}if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {{
    Write-Output $dialog.FileName
}}
"""
    return normalize_path_text(_run_powershell(script))


def _read_system_clipboard_windows() -> str:
    script = """
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try {
    $files = Get-Clipboard -Format FileDropList -ErrorAction Stop
    if ($files -and $files.Count -gt 0) {
        Write-Output $files[0]
        exit 0
    }
} catch {
}
$text = Get-Clipboard -Raw -ErrorAction SilentlyContinue
if ($text) {
    Write-Output $text
}
"""
    return _run_powershell(script).strip()


def _run_powershell(script: str) -> str:
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-STA", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _resolve_initial_directory(initial_path: str | None) -> str:
    raw_path = normalize_path_text(initial_path)
    if not raw_path:
        return ""

    try:
        candidate = Path(raw_path).expanduser()
        if candidate.is_file():
            return str(candidate.parent.resolve())
        if candidate.is_dir():
            return str(candidate.resolve())
        if candidate.parent.exists():
            return str(candidate.parent.resolve())
    except Exception:
        return ""
    return ""


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _browse_for_image_file_tk(initial_path: str | None) -> str | None:
    try:
        from tkinter import Tk, filedialog
    except Exception:
        return None

    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    initial_directory = _resolve_initial_directory(initial_path)
    try:
        path = filedialog.askopenfilename(
            title="Select an image for DecoScreenBeautifier",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tiff *.tif"),
                ("All Files", "*.*"),
            ],
            initialdir=initial_directory or None,
        )
    finally:
        root.destroy()
    return normalize_path_text(path)


def _read_system_clipboard_tk() -> str:
    try:
        from tkinter import Tk
    except Exception:
        return ""

    root = Tk()
    root.withdraw()
    try:
        return root.clipboard_get().strip()
    except Exception:
        return ""
    finally:
        root.destroy()

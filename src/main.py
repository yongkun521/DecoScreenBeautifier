import importlib
import os
import sys
from pathlib import Path
from typing import Optional

# 将 src 目录添加到 Python 路径，以便可以导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_MODULES = {
    "textual": "textual",
    "rich": "rich",
    "psutil": "psutil",
    "pyaudio": "pyaudio",
    "numpy": "numpy",
    "PIL": "pillow",
    "cv2": "opencv-python",
    "json5": "json5",
    "appdirs": "appdirs",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _venv_python() -> Optional[Path]:
    root = _project_root()
    if os.name == "nt":
        candidate = root / "venv" / "Scripts" / "python.exe"
    else:
        candidate = root / "venv" / "bin" / "python"
    return candidate if candidate.is_file() else None


def _missing_modules() -> list[str]:
    missing = []
    for module_name, package_name in REQUIRED_MODULES.items():
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                missing.append(package_name)
            else:
                raise
    return missing


def _maybe_reexec_with_venv() -> None:
    venv_python = _venv_python()
    if not venv_python:
        return
    try:
        if Path(sys.executable).resolve() == venv_python.resolve():
            return
    except FileNotFoundError:
        return
    sys.stderr.write(
        f"Missing dependencies detected. Re-launching with venv: {venv_python}\n"
    )
    sys.stderr.flush()
    try:
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    except OSError as exc:
        sys.stderr.write(f"Failed to re-launch with venv: {exc}\n")


def _ensure_dependencies() -> None:
    missing = _missing_modules()
    if not missing:
        return
    _maybe_reexec_with_venv()
    requirements = _project_root() / "requirements.txt"
    missing_list = ", ".join(sorted(set(missing)))
    sys.stderr.write("Missing Python dependencies: ")
    sys.stderr.write(missing_list)
    sys.stderr.write("\n")
    sys.stderr.write(f"Python: {sys.executable}\n")
    if requirements.is_file():
        sys.stderr.write("Install them with:\n")
        sys.stderr.write(f"  python -m pip install -r {requirements}\n")
    else:
        sys.stderr.write("Install them with:\n")
        sys.stderr.write("  python -m pip install -r requirements.txt\n")
    sys.stderr.write(
        "If you are using the local venv, activate it first:\n"
        "  .\\venv\\Scripts\\activate\n"
    )
    raise SystemExit(1)

def main():
    """应用程序入口点"""
    _ensure_dependencies()
    from ui.app import DecoScreenApp

    app = DecoScreenApp()
    app.run()

if __name__ == "__main__":
    main()

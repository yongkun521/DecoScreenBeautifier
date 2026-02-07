import importlib
import os
import sys
import traceback
import ctypes
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

APP_STARTUP_ERROR_TITLE = "DecoScreenBeautifier Legacy Startup Error"
WT_HOSTED_SENTINEL_ENV_KEY = "DSB_WT_HOSTED"


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _stderr_write(message: str) -> None:
    text = str(message)
    stream = getattr(sys, "stderr", None)
    if stream is not None and hasattr(stream, "write"):
        try:
            stream.write(text)
            if hasattr(stream, "flush"):
                stream.flush()
            return
        except Exception:
            pass
    try:
        os.write(2, text.encode("utf-8", errors="replace"))
    except Exception:
        pass


def _append_startup_error_log(message: str) -> None:
    try:
        log_path = _project_root() / "legacy_terminal_error.log"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(str(message))
            if not str(message).endswith("\n"):
                f.write("\n")
    except Exception:
        pass


def _running_in_terminal_host() -> bool:
    if os.environ.get(WT_HOSTED_SENTINEL_ENV_KEY):
        return True
    if os.environ.get("WT_SESSION"):
        return True
    term_program = str(os.environ.get("TERM_PROGRAM") or "").strip().lower()
    if term_program == "windows_terminal":
        return True
    stderr = getattr(sys, "stderr", None)
    try:
        if stderr is not None and hasattr(stderr, "isatty") and stderr.isatty():
            return True
    except Exception:
        return False
    return False


def _show_startup_error(message: str, title: str = APP_STARTUP_ERROR_TITLE) -> None:
    text = str(message)
    _stderr_write(text + "\n")
    _append_startup_error_log(text)
    if os.name != "nt":
        return
    if _running_in_terminal_host():
        return
    try:
        flags = 0x10 | 0x00010000 | 0x00040000
        ctypes.windll.user32.MessageBoxW(None, text, title, flags)
    except Exception:
        pass


def _write_legacy_error_log(exc: BaseException) -> Path | None:
    try:
        log_path = _project_root() / "legacy_terminal_error.log"
        lines = [
            f"sys.executable={sys.executable}",
            f"sys.argv={sys.argv}",
            f"sys.frozen={getattr(sys, 'frozen', False)}",
            f"cwd={os.getcwd()}",
            "traceback=",
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        ]
        log_path.write_text("\n".join(lines), encoding="utf-8")
        return log_path
    except Exception:
        return None


def _is_frozen_legacy_terminal_exe() -> bool:
    if not getattr(sys, "frozen", False):
        return False
    try:
        return "legacy_terminal" in Path(sys.executable).stem.lower()
    except Exception:
        return False


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
    _stderr_write(
        f"Missing dependencies detected. Re-launching with venv: {venv_python}\n"
    )
    try:
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    except OSError as exc:
        _stderr_write(f"Failed to re-launch with venv: {exc}\n")


def _ensure_dependencies() -> None:
    missing = _missing_modules()
    if not missing:
        return
    _maybe_reexec_with_venv()
    requirements = _project_root() / "requirements.txt"
    missing_list = ", ".join(sorted(set(missing)))
    lines = [
        "Missing Python dependencies:",
        f"  {missing_list}",
        f"Python: {sys.executable}",
    ]
    if requirements.is_file():
        lines.append("Install them with:")
        lines.append(f"  python -m pip install -r {requirements}")
    else:
        lines.append("Install them with:")
        lines.append("  python -m pip install -r requirements.txt")
    lines.append("If you are using the local venv, activate it first:")
    lines.append("  .\\venv\\Scripts\\activate")
    _show_startup_error("\n".join(lines))
    raise SystemExit(1)

def _prepare_terminal() -> bool:
    try:
        from config.manager import ConfigManager
        from utils.terminal_launcher import maybe_prepare_terminal
    except Exception:
        return False

    try:
        config_manager = ConfigManager()
        config_manager.load_settings()
    except Exception:
        return False

    _apply_fps_limit(config_manager.settings)

    terminal_settings = config_manager.settings.get("terminal_integration")
    if isinstance(terminal_settings, dict):
        force_bundled_wt_only = bool(
            terminal_settings.get("force_bundled_wt_only", True)
        )
        if getattr(sys, "frozen", False) and force_bundled_wt_only:
            terminal_settings["enabled"] = True
            terminal_settings["backend"] = "windows_terminal"
            terminal_settings["fallback_backend"] = "classic"
            terminal_settings["prefer_bundled_wt"] = True

    return maybe_prepare_terminal(config_manager.settings, sys.argv)


def _apply_fps_limit(settings: dict) -> None:
    fps_limit = settings.get("fps_limit")
    try:
        fps_value = int(fps_limit)
    except (TypeError, ValueError):
        return
    if fps_value <= 0:
        return
    os.environ["TEXTUAL_FPS"] = str(fps_value)
    try:
        import textual.constants as textual_constants
        import textual.screen as textual_screen
    except Exception:
        return
    textual_constants.MAX_FPS = fps_value
    try:
        textual_screen.UPDATE_PERIOD = 1 / fps_value
    except Exception:
        return

def main():
    """应用程序入口点"""
    _ensure_dependencies()
    if _prepare_terminal():
        return
    from ui.app import DecoScreenApp

    app = DecoScreenApp()
    app.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
    except SystemExit:
        raise
    except Exception as exc:
        log_path = _write_legacy_error_log(exc)
        lines = [
            "Legacy terminal mode failed to start.",
            f"{type(exc).__name__}: {exc}",
        ]
        if log_path:
            lines.append(f"Error log: {log_path}")
        _show_startup_error("\n".join(lines))
        raise SystemExit(1)

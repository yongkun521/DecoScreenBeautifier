import importlib
import os
import sys
import traceback
import ctypes
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import psutil
except Exception:
    psutil = None

# 将 src 目录添加到 Python 路径，以便可以导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.startup_trace import (
        STARTUP_TRACE_LOG_NAME,
        trace_startup as _shared_trace_startup,
    )
except Exception:
    STARTUP_TRACE_LOG_NAME = "legacy_terminal_startup_trace.log"
    _shared_trace_startup = None

REQUIRED_MODULES = {
    "textual": "textual",
    "rich": "rich",
    "psutil": "psutil",
    "numpy": "numpy",
    "json5": "json5",
    "appdirs": "appdirs",
}

APP_STARTUP_ERROR_TITLE = "DecoScreenBeautifier Legacy Startup Error"
WT_HOSTED_SENTINEL_ENV_KEY = "DSB_WT_HOSTED"


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _startup_log_candidates() -> list[Path]:
    candidates: list[Path] = []
    candidates.append(_project_root() / "legacy_terminal_error.log")
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidates.append(
            Path(local_appdata)
            / "DecoTeam"
            / "DecoScreenBeautifier"
            / "legacy_terminal_error.log"
        )
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(Path(key))
    return unique


def _startup_trace_log_candidates() -> list[Path]:
    result: list[Path] = []
    for base_path in _startup_log_candidates():
        result.append(base_path.with_name(STARTUP_TRACE_LOG_NAME))
    return result


def _trace_startup(message: str) -> None:
    if _shared_trace_startup is not None:
        try:
            _shared_trace_startup(message)
            return
        except Exception:
            pass

    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"[{timestamp}] {message}"
    for log_path in _startup_trace_log_candidates():
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(line)
                f.write("\n")
            break
        except Exception:
            continue
    try:
        import tempfile
        fallback = Path(tempfile.gettempdir()) / STARTUP_TRACE_LOG_NAME
        with fallback.open("a", encoding="utf-8") as f:
            f.write(line)
            f.write("\n")
    except Exception:
        pass


def _append_text_to_startup_log(message: str) -> Path | None:
    text = str(message)
    for log_path in _startup_log_candidates():
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(text)
                if not text.endswith("\n"):
                    f.write("\n")
            return log_path
        except Exception:
            continue
    return None


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
    _append_text_to_startup_log(message)


def _running_in_terminal_host() -> bool:
    if os.environ.get(WT_HOSTED_SENTINEL_ENV_KEY):
        return True
    if os.environ.get("WT_SESSION"):
        return True
    term_program = str(os.environ.get("TERM_PROGRAM") or "").strip().lower()
    if term_program == "windows_terminal":
        return True

    if psutil is not None:
        try:
            current = psutil.Process(os.getpid())
        except Exception:
            current = None
        if current is not None:
            terminal_host_names = {
                "windowsterminal.exe",
                "openconsole.exe",
                "wt.exe",
                "conhost.exe",
            }
            node = current
            for _ in range(6):
                try:
                    node = node.parent() if node is not None else None
                except Exception:
                    node = None
                if node is None:
                    break
                try:
                    process_name = str(node.name() or "").strip().lower()
                except Exception:
                    continue
                if process_name in terminal_host_names:
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
    _trace_startup(f"show_startup_error: {text}")
    _stderr_write(text + "\n")
    _append_startup_error_log(text)
    if os.name != "nt":
        return
    if _running_in_terminal_host() and not getattr(sys, "frozen", False):
        return
    try:
        flags = 0x10 | 0x00010000 | 0x00040000
        ctypes.windll.user32.MessageBoxW(None, text, title, flags)
    except Exception:
        pass


def _write_legacy_error_log(exc: BaseException) -> Path | None:
    lines = [
        f"sys.executable={sys.executable}",
        f"sys.argv={sys.argv}",
        f"sys.frozen={getattr(sys, 'frozen', False)}",
        f"cwd={os.getcwd()}",
        f"WT_SESSION={os.environ.get('WT_SESSION', '')}",
        f"TERM_PROGRAM={os.environ.get('TERM_PROGRAM', '')}",
        f"{WT_HOSTED_SENTINEL_ENV_KEY}={os.environ.get(WT_HOSTED_SENTINEL_ENV_KEY, '')}",
        "traceback=",
        "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    ]
    text = "\n".join(lines)
    for log_path in _startup_log_candidates():
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(text, encoding="utf-8")
            return log_path
        except Exception:
            continue
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
        _trace_startup("ensure_dependencies: all required modules available")
        return
    _trace_startup(f"ensure_dependencies: missing modules: {missing}")
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
        use_safe_visual_defaults = bool(
            terminal_settings.get("bundled_wt_safe_visual_defaults", True)
        )
        if getattr(sys, "frozen", False) and force_bundled_wt_only:
            terminal_settings["enabled"] = True
            terminal_settings["backend"] = "windows_terminal"
            terminal_settings["fallback_backend"] = "classic"
            terminal_settings["prefer_bundled_wt"] = True
        if (
            getattr(sys, "frozen", False)
            and terminal_settings.get("backend") == "windows_terminal"
            and use_safe_visual_defaults
        ):
            terminal_settings["bundled_wt_use_acrylic"] = False
            terminal_settings["bundled_wt_opacity"] = 100
            terminal_settings["bundled_wt_enable_pixel_shader"] = False

        _trace_startup(
            "_prepare_terminal: "
            f"enabled={terminal_settings.get('enabled')} "
            f"backend={terminal_settings.get('backend')} "
            f"prefer_bundled_wt={terminal_settings.get('prefer_bundled_wt')} "
            f"safe_visual_defaults={use_safe_visual_defaults}"
        )

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
    _trace_startup("main: enter")
    stdout_tty = False
    stderr_tty = False
    stdin_tty = False
    try:
        stdout_tty = bool(getattr(sys.stdout, "isatty", lambda: False)())
    except Exception:
        stdout_tty = False
    try:
        stderr_tty = bool(getattr(sys.stderr, "isatty", lambda: False)())
    except Exception:
        stderr_tty = False
    try:
        stdin_tty = bool(getattr(sys.stdin, "isatty", lambda: False)())
    except Exception:
        stdin_tty = False

    _trace_startup(
        "main: context "
        f"pid={os.getpid()} ppid={os.getppid()} "
        f"frozen={getattr(sys, 'frozen', False)} "
        f"exe={sys.executable} "
        f"cwd={os.getcwd()} "
        f"stdin_tty={stdin_tty} stdout_tty={stdout_tty} stderr_tty={stderr_tty} "
        f"WT_SESSION={os.environ.get('WT_SESSION', '')} "
        f"TERM_PROGRAM={os.environ.get('TERM_PROGRAM', '')} "
        f"TERM={os.environ.get('TERM', '')} "
        f"COLORTERM={os.environ.get('COLORTERM', '')}"
    )
    _ensure_dependencies()
    terminal_prepared = _prepare_terminal()
    _trace_startup(f"main: terminal_prepared={terminal_prepared}")
    if terminal_prepared:
        _trace_startup("main: launched in terminal host, parent exits")
        return

    _trace_startup("main: importing DecoScreenApp")
    from ui.app import DecoScreenApp
    _trace_startup("main: DecoScreenApp imported")

    app = DecoScreenApp()
    _trace_startup("main: app initialized")
    _trace_startup("main: app.run start")
    try:
        app.run()
    except Exception as exc:
        _trace_startup(f"main: app.run exception: {type(exc).__name__}: {exc}")
        raise
    _trace_startup("main: app.run end")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
    except SystemExit:
        raise
    except Exception as exc:
        _trace_startup(f"main: unhandled exception: {type(exc).__name__}: {exc}")
        log_path = _write_legacy_error_log(exc)
        lines = [
            "Legacy terminal mode failed to start.",
            f"{type(exc).__name__}: {exc}",
        ]
        if log_path:
            lines.append(f"Error log: {log_path}")
        _show_startup_error("\n".join(lines))
        raise SystemExit(1)

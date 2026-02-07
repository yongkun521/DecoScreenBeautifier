import importlib
import os
import sys
import argparse
import ctypes
from copy import deepcopy
from pathlib import Path
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_MODULES = {
    "PySide6": "PySide6",
    "rich": "rich",
    "psutil": "psutil",
    "json5": "json5",
    "appdirs": "appdirs",
}

APP_STARTUP_ERROR_TITLE = "DecoScreenBeautifier Startup Error"


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


def _show_startup_error(message: str, title: str = APP_STARTUP_ERROR_TITLE) -> None:
    text = str(message)
    _stderr_write(text + "\n")
    if os.name != "nt":
        return
    try:
        ctypes.windll.user32.MessageBoxW(None, text, title, 0x10)
    except Exception:
        pass


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
    _stderr_write(
        f"Missing dependencies detected. Re-launching with venv: {venv_python}\n"
    )
    try:
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    except OSError as exc:
        _stderr_write(f"Failed to re-launch with venv: {exc}\n")


def _ensure_dependencies() -> None:
    missing = _missing_modules()
    if missing:
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

    qt_runtime_error = _check_qt_runtime()
    if qt_runtime_error:
        _show_startup_error(
            "\n".join(
                [
                    "Qt runtime check failed:",
                    f"  {qt_runtime_error}",
                    "Try installing Microsoft Visual C++ Redistributable (2015-2022 x64), then retry.",
                ]
            )
        )
        raise SystemExit(1)


def _check_qt_runtime() -> str:
    try:
        import PySide6  # noqa: F401
        from PySide6 import QtCore  # noqa: F401
    except Exception as exc:
        return str(exc)
    return ""


def _build_runtime_options(argv: Optional[list[str]] = None) -> dict:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--readonly-config", action="store_true")
    parser.add_argument("--auto-exit-seconds", type=float, default=0.0)
    parser.add_argument("--runtime-options", type=str, default="")
    parser.add_argument("--metrics-output", type=str, default="")
    parser.add_argument("--gui-monitor", type=str, default="")
    parser.add_argument("--gui-size-px", type=str, default="")
    parser.add_argument("--gui-pos-px", type=str, default="")
    parser.add_argument("--gui-fps", type=int, default=0)
    parser.add_argument("--gui-font-face", type=str, default="")
    parser.add_argument("--gui-font-size", type=int, default=0)
    parser.add_argument("--gui-cell-aspect", type=float, default=0.0)
    parser.add_argument("--gui-borderless", dest="gui_borderless", action="store_true")
    parser.add_argument("--gui-windowed", dest="gui_borderless", action="store_false")
    parser.add_argument("--gui-always-on-top", dest="gui_always_on_top", action="store_true")
    parser.add_argument("--gui-not-topmost", dest="gui_always_on_top", action="store_false")
    parser.add_argument("--gui-use-work-area", dest="gui_use_work_area", action="store_true")
    parser.add_argument("--gui-full-screen-area", dest="gui_use_work_area", action="store_false")
    parser.add_argument("--effects-enabled", dest="effects_enabled", action="store_true")
    parser.add_argument("--effects-disabled", dest="effects_enabled", action="store_false")
    parser.add_argument("--crt-shader-enabled", dest="crt_shader_enabled", action="store_true")
    parser.add_argument("--crt-shader-disabled", dest="crt_shader_enabled", action="store_false")
    parser.add_argument("--perf-enabled", dest="perf_enabled", action="store_true")
    parser.add_argument("--perf-disabled", dest="perf_enabled", action="store_false")
    parser.add_argument("--perf-interval", type=float, default=0.0)
    parser.add_argument("--perf-log-path", type=str, default="")
    parser.set_defaults(
        gui_borderless=None,
        gui_always_on_top=None,
        gui_use_work_area=None,
        effects_enabled=None,
        crt_shader_enabled=None,
        perf_enabled=None,
    )

    args, _unknown = parser.parse_known_args(argv)
    runtime_options: dict = {}

    if args.runtime_options:
        runtime_options = _load_runtime_options_file(args.runtime_options)
        if not isinstance(runtime_options, dict):
            runtime_options = {}
    runtime_options = deepcopy(runtime_options)

    if args.readonly_config:
        runtime_options["readonly_config"] = True
    if args.auto_exit_seconds > 0:
        runtime_options["auto_exit_seconds"] = float(args.auto_exit_seconds)
    if args.metrics_output:
        runtime_options["metrics_output"] = str(args.metrics_output)

    gui_settings = runtime_options.get("gui_settings")
    if not isinstance(gui_settings, dict):
        gui_settings = {}
        runtime_options["gui_settings"] = gui_settings

    if args.gui_monitor:
        gui_settings["monitor"] = str(args.gui_monitor)
    if args.gui_size_px:
        gui_settings["size_px"] = str(args.gui_size_px)
    if args.gui_pos_px:
        gui_settings["pos_px"] = str(args.gui_pos_px)
    if args.gui_fps > 0:
        gui_settings["fps"] = int(args.gui_fps)
    if args.gui_font_face:
        gui_settings["font_face"] = str(args.gui_font_face)
    if args.gui_font_size > 0:
        gui_settings["font_size"] = int(args.gui_font_size)
    if args.gui_cell_aspect > 0:
        gui_settings["cell_aspect"] = float(args.gui_cell_aspect)
    if args.gui_borderless is not None:
        gui_settings["borderless"] = bool(args.gui_borderless)
    if args.gui_always_on_top is not None:
        gui_settings["always_on_top"] = bool(args.gui_always_on_top)
    if args.gui_use_work_area is not None:
        gui_settings["use_work_area"] = bool(args.gui_use_work_area)

    if args.effects_enabled is not None:
        effects = gui_settings.get("effects")
        if not isinstance(effects, dict):
            effects = {}
            gui_settings["effects"] = effects
        effects["enabled"] = bool(args.effects_enabled)

    if args.crt_shader_enabled is not None:
        crt_shader = gui_settings.get("crt_shader")
        if not isinstance(crt_shader, dict):
            crt_shader = {}
            gui_settings["crt_shader"] = crt_shader
        crt_shader["enabled"] = bool(args.crt_shader_enabled)

    performance_monitor = runtime_options.get("performance_monitor")
    if not isinstance(performance_monitor, dict):
        performance_monitor = {}
        runtime_options["performance_monitor"] = performance_monitor

    if args.perf_enabled is not None:
        performance_monitor["enabled"] = bool(args.perf_enabled)
    if args.perf_interval > 0:
        performance_monitor["sample_interval"] = float(args.perf_interval)
    if args.perf_log_path:
        performance_monitor["log_path"] = str(args.perf_log_path)

    return runtime_options


def _load_runtime_options_file(file_path: str) -> dict:
    import json5

    path = Path(file_path).expanduser()
    if not path.is_absolute():
        path = _project_root() / path
    if not path.is_file():
        raise SystemExit(f"Runtime options file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json5.load(handle)
    except Exception as exc:
        raise SystemExit(f"Failed to load runtime options: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("Runtime options must be an object/dict")
    return payload


def main() -> int:
    _ensure_dependencies()
    runtime_options = _build_runtime_options(sys.argv[1:])
    from gui_host.app import run_gui

    return run_gui(runtime_options=runtime_options)


if __name__ == "__main__":
    raise SystemExit(main())

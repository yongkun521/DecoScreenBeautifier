from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import json5

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None

try:
    from utils.startup_trace import trace_startup as _trace_startup
except Exception:
    def _trace_startup(message: str) -> None:
        return None

DEFAULT_WT_TITLE = "DecoScreenBeautifier"
DEFAULT_WINDOW_TARGET = "new"
DEFAULT_BUNDLED_PROFILE_NAME = "DecoScreenBeautifier-CRT"
DEFAULT_WT_SETTINGS_RELATIVE_PATH = Path("settings") / "settings.json"
DEFAULT_PIXEL_SHADER_FILE_NAME = "deco_placeholder.hlsl"
DEFAULT_PIXEL_SHADER_RELATIVE_PATH = (
    Path("vendor") / "windows_terminal" / "shaders" / DEFAULT_PIXEL_SHADER_FILE_NAME
)
BUNDLED_WT_EXECUTABLE_NAMES = (
    "wt.exe",
    "WindowsTerminal.exe",
)
BUNDLED_WT_RELATIVE_CANDIDATES = (
    Path("vendor") / "windows_terminal" / "wt.exe",
    Path("vendor") / "windows_terminal" / "WindowsTerminal.exe",
    Path("vendor") / "windows_terminal" / "x64" / "wt.exe",
    Path("vendor") / "windows_terminal" / "x64" / "WindowsTerminal.exe",
    Path("windows_terminal") / "wt.exe",
    Path("windows_terminal") / "WindowsTerminal.exe",
)
PYTHON_RELAUNCH_ENV_KEYS = {
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTHONEXECUTABLE",
    "PYTHONUTF8",
    "PYTHONNOUSERSITE",
    "PYTHONSAFEPATH",
    "PYTHONPLATLIBDIR",
}
WT_HOSTED_SENTINEL_ENV_KEY = "DSB_WT_HOSTED"


def _is_windows() -> bool:
    return os.name == "nt"


def _in_windows_terminal() -> bool:
    if os.environ.get(WT_HOSTED_SENTINEL_ENV_KEY):
        return True

    if os.environ.get("WT_SESSION"):
        return True

    term_program = str(os.environ.get("TERM_PROGRAM") or "").strip().lower()
    if term_program == "windows_terminal":
        return True

    if psutil is None:
        return False

    try:
        current = psutil.Process(os.getpid())
    except Exception:
        return False

    terminal_host_names = {
        "windowsterminal.exe",
        "openconsole.exe",
        "wt.exe",
        "conhost.exe",
    }
    node = current
    for _ in range(5):
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

    return False


def _application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _normalize_bundled_wt_path(path_value: Any) -> Optional[Path]:
    if path_value is None:
        return None
    text = str(path_value).strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = _application_root() / path
    if path.is_dir():
        for executable_name in BUNDLED_WT_EXECUTABLE_NAMES:
            candidate = path / executable_name
            if candidate.is_file():
                return candidate
        path = path / BUNDLED_WT_EXECUTABLE_NAMES[0]
    return path


def _resolve_path(path_value: Any, *, base_dir: Optional[Path] = None) -> Optional[Path]:
    if path_value is None:
        return None
    text = str(path_value).strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        if base_dir is None:
            base_dir = _application_root()
        path = base_dir / path
    return path


def _find_system_wt_executable() -> Optional[str]:
    path = shutil.which("wt")
    if path:
        return path
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        candidate = Path(local_appdata) / "Microsoft" / "WindowsApps" / "wt.exe"
        if candidate.is_file():
            return str(candidate)
    return None


def _find_bundled_wt_executable(terminal_settings: Mapping[str, Any]) -> Optional[str]:
    configured_path = _normalize_bundled_wt_path(
        terminal_settings.get("bundled_wt_path")
    )
    checked: set[Path] = set()

    if configured_path is not None:
        configured_path = configured_path.resolve()
        checked.add(configured_path)
        if configured_path.is_file():
            return str(configured_path)

    app_root = _application_root()
    for relative_path in BUNDLED_WT_RELATIVE_CANDIDATES:
        candidate = (app_root / relative_path).resolve()
        if candidate in checked:
            continue
        checked.add(candidate)
        if candidate.is_file():
            return str(candidate)
    return None


def _select_wt_executable(
    terminal_settings: Mapping[str, Any],
) -> tuple[Optional[str], bool]:
    prefer_bundled = bool(terminal_settings.get("prefer_bundled_wt", True))
    bundled_path = _find_bundled_wt_executable(terminal_settings)
    system_path = _find_system_wt_executable()

    if prefer_bundled:
        if bundled_path:
            return bundled_path, True
        if system_path:
            return system_path, False
    else:
        if system_path:
            return system_path, False
        if bundled_path:
            return bundled_path, True

    return None, False


def _prefer_wt_cli_executable(path_text: str) -> str:
    path = Path(path_text).resolve()
    if path.name.lower() != "windowsterminal.exe":
        return str(path)
    candidate = path.with_name("wt.exe")
    if candidate.is_file():
        return str(candidate)
    return str(path)


def _ensure_wt_portable_mode(
    wt_exe: str, terminal_settings: Mapping[str, Any], *, use_bundled: bool
) -> None:
    if not use_bundled:
        return
    if not bool(terminal_settings.get("use_wt_portable_mode", True)):
        return
    marker = Path(wt_exe).resolve().parent / ".portable"
    if marker.exists():
        return
    try:
        marker.touch(exist_ok=True)
    except OSError as exc:
        sys.stderr.write(f"Failed to enable bundled WT portable mode: {exc}\n")


def _resolve_bundled_wt_profile_name(terminal_settings: Mapping[str, Any]) -> str:
    configured = terminal_settings.get("bundled_wt_profile_name")
    if configured is None:
        configured = terminal_settings.get("profile")
    name = str(configured or "").strip()
    return name or DEFAULT_BUNDLED_PROFILE_NAME


def _resolve_bundled_wt_settings_path(
    wt_exe: str,
    terminal_settings: Mapping[str, Any],
) -> Path:
    configured = terminal_settings.get("bundled_wt_settings_path")
    if configured:
        resolved = _resolve_path(configured)
        if resolved is not None:
            return resolved
    wt_root = Path(wt_exe).resolve().parent
    return wt_root / DEFAULT_WT_SETTINGS_RELATIVE_PATH


def _resolve_bundled_wt_pixel_shader_path(
    wt_exe: str,
    terminal_settings: Mapping[str, Any],
) -> Optional[Path]:
    configured = _resolve_path(terminal_settings.get("bundled_wt_pixel_shader_path"))
    if configured is not None:
        return configured

    wt_root = Path(wt_exe).resolve().parent
    bundled_candidate = wt_root.parent / "shaders" / DEFAULT_PIXEL_SHADER_FILE_NAME
    if bundled_candidate.exists():
        return bundled_candidate

    app_candidate = _application_root() / DEFAULT_PIXEL_SHADER_RELATIVE_PATH
    if app_candidate.exists():
        return app_candidate

    return bundled_candidate


def _load_json5_document(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            loaded = json5.load(f)
    except Exception as exc:
        sys.stderr.write(f"Failed to parse bundled WT settings: {path} ({exc})\n")
        return {}
    if isinstance(loaded, dict):
        return loaded
    return {}


def _write_json_document(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(document, f, indent=4, ensure_ascii=False)
        f.write("\n")


def _ensure_mapping(target: dict[str, Any], key: str) -> dict[str, Any]:
    value = target.get(key)
    if isinstance(value, dict):
        return value
    replacement: dict[str, Any] = {}
    target[key] = replacement
    return replacement


def _ensure_profile_list(document: dict[str, Any]) -> list[dict[str, Any]]:
    profiles = _ensure_mapping(document, "profiles")
    profile_list = profiles.get("list")
    if isinstance(profile_list, list):
        normalized = [item for item in profile_list if isinstance(item, dict)]
        profiles["list"] = normalized
        return normalized
    profiles["list"] = []
    return profiles["list"]


def _normalize_key_binding(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return text.replace(" ", "")


def _extract_actions(document: dict[str, Any]) -> list[dict[str, Any]]:
    actions = document.get("actions")
    if isinstance(actions, list):
        normalized = [item for item in actions if isinstance(item, dict)]
        document["actions"] = normalized
        return normalized

    keybindings = document.get("keybindings")
    if isinstance(keybindings, list):
        normalized = [item for item in keybindings if isinstance(item, dict)]
        document["keybindings"] = normalized
        return normalized

    document["actions"] = []
    return document["actions"]


def _action_is_toggle_focus_mode(item: Mapping[str, Any]) -> bool:
    command = item.get("command")
    if isinstance(command, str):
        return command.strip().lower() == "togglefocusmode"
    if isinstance(command, dict):
        action_name = str(command.get("action") or "").strip().lower()
        return action_name == "togglefocusmode"
    return False


def _ensure_focus_toggle_binding(
    settings_document: dict[str, Any],
    terminal_settings: Mapping[str, Any],
) -> None:
    if not bool(
        terminal_settings.get("bundled_wt_enable_focus_toggle_binding", True)
    ):
        return

    configured_key = terminal_settings.get("focus_mode_toggle_key", "alt+shift+f")
    key_text = _normalize_key_binding(configured_key)
    if not key_text:
        return

    actions = _extract_actions(settings_document)
    existing_toggle = [item for item in actions if _action_is_toggle_focus_mode(item)]
    if existing_toggle:
        primary = existing_toggle[0]
        primary["keys"] = [key_text]
        for duplicate in existing_toggle[1:]:
            try:
                actions.remove(duplicate)
            except ValueError:
                continue
        return

    actions.append(
        {
            "command": "toggleFocusMode",
            "keys": [key_text],
        }
    )


def _resolve_virtual_key(key_token: str) -> Optional[int]:
    key = str(key_token or "").strip().lower()
    if not key:
        return None

    special_keys = {
        "tab": 0x09,
        "enter": 0x0D,
        "return": 0x0D,
        "esc": 0x1B,
        "escape": 0x1B,
        "space": 0x20,
        "left": 0x25,
        "up": 0x26,
        "right": 0x27,
        "down": 0x28,
        "insert": 0x2D,
        "delete": 0x2E,
        "home": 0x24,
        "end": 0x23,
        "pgup": 0x21,
        "pageup": 0x21,
        "pgdn": 0x22,
        "pagedown": 0x22,
        "minus": 0xBD,
        "-": 0xBD,
        "equal": 0xBB,
        "equals": 0xBB,
        "=": 0xBB,
    }
    if key in special_keys:
        return special_keys[key]

    if key.startswith("f") and key[1:].isdigit():
        index = int(key[1:])
        if 1 <= index <= 24:
            return 0x6F + index

    if len(key) == 1 and "a" <= key <= "z":
        return ord(key.upper())
    if len(key) == 1 and "0" <= key <= "9":
        return ord(key)

    return None


def _send_hotkey(binding: str) -> tuple[bool, str]:
    text = _normalize_key_binding(binding)
    if not text:
        return False, "Empty hotkey binding"

    parts = [part for part in text.split("+") if part]
    if not parts:
        return False, "Invalid hotkey binding"

    modifier_map = {
        "ctrl": 0x11,
        "control": 0x11,
        "shift": 0x10,
        "alt": 0x12,
    }
    modifiers: list[int] = []
    main_key_token: Optional[str] = None
    for part in parts:
        if part in modifier_map:
            modifiers.append(modifier_map[part])
        else:
            main_key_token = part

    if main_key_token is None:
        return False, "No main key in hotkey binding"

    shifted_key_aliases = {
        "plus": "equal",
        "_": "minus",
    }
    shifted_token = shifted_key_aliases.get(main_key_token)
    if shifted_token:
        main_key_token = shifted_token
        if modifier_map["shift"] not in modifiers:
            modifiers.append(modifier_map["shift"])

    main_key = _resolve_virtual_key(main_key_token)
    if main_key is None:
        return False, f"Unsupported key token: {main_key_token}"

    try:
        import ctypes
    except Exception as exc:
        return False, f"ctypes unavailable: {exc}"

    KEYEVENTF_KEYUP = 0x0002
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    for mod_key in modifiers:
        user32.keybd_event(mod_key, 0, 0, 0)
    user32.keybd_event(main_key, 0, 0, 0)
    user32.keybd_event(main_key, 0, KEYEVENTF_KEYUP, 0)
    for mod_key in reversed(modifiers):
        user32.keybd_event(mod_key, 0, KEYEVENTF_KEYUP, 0)
    return True, "Hotkey sent"


def toggle_focus_mode_in_running_wt(
    terminal_settings: Mapping[str, Any],
) -> tuple[bool, str]:
    if not _is_windows():
        return False, "Only supported on Windows"

    settings = _normalize_settings(terminal_settings)
    if settings.get("backend") not in {None, "", "windows_terminal"}:
        return False, "Current backend is not windows_terminal"

    if not _in_windows_terminal():
        return False, "Not running inside Windows Terminal"

    key_text = _normalize_key_binding(settings.get("focus_mode_toggle_key", "alt+shift+f"))
    if not key_text:
        key_text = "alt+shift+f"

    sent, message = _send_hotkey(key_text)
    if sent:
        return True, "Sent focus-mode hotkey"
    return False, message


def adjust_zoom_in_running_wt(
    terminal_settings: Mapping[str, Any],
    *,
    zoom_in: bool,
) -> tuple[bool, str]:
    if not _is_windows():
        return False, "Only supported on Windows"

    settings = _normalize_settings(terminal_settings)
    if settings.get("backend") not in {None, "", "windows_terminal"}:
        return False, "Current backend is not windows_terminal"

    if not _in_windows_terminal():
        return False, "Not running inside Windows Terminal"

    key_name = "zoom_in_key" if zoom_in else "zoom_out_key"
    default_key = "ctrl+plus" if zoom_in else "ctrl+minus"
    key_text = _normalize_key_binding(settings.get(key_name, default_key))
    if not key_text:
        key_text = default_key

    sent, message = _send_hotkey(key_text)
    if sent:
        direction = "in" if zoom_in else "out"
        return True, f"Sent zoom-{direction} hotkey"
    return False, message


def _upsert_bundled_wt_profile(
    profile_list: list[dict[str, Any]],
    profile_name: str,
) -> dict[str, Any]:
    for profile in profile_list:
        if str(profile.get("name") or "").strip() == profile_name:
            return profile
    profile: dict[str, Any] = {"name": profile_name}
    profile_list.append(profile)
    return profile


def _apply_bundled_wt_profile_defaults(
    profile: dict[str, Any],
    terminal_settings: Mapping[str, Any],
    *,
    pixel_shader_path: Optional[Path],
) -> None:
    safe_visual_defaults = bool(
        terminal_settings.get("bundled_wt_safe_visual_defaults", False)
    )
    retro_enabled = bool(terminal_settings.get("bundled_wt_retro_effect", True))
    use_pixel_shader = bool(terminal_settings.get("bundled_wt_enable_pixel_shader", False))

    if safe_visual_defaults:
        use_pixel_shader = False

    profile["hidden"] = False
    profile["colorScheme"] = str(
        terminal_settings.get("bundled_wt_color_scheme", "Campbell")
    )
    profile["useAcrylic"] = (
        False
        if safe_visual_defaults
        else bool(terminal_settings.get("bundled_wt_use_acrylic", True))
    )
    opacity = 100 if safe_visual_defaults else terminal_settings.get("bundled_wt_opacity", 88)
    try:
        profile["opacity"] = max(0, min(100, int(opacity)))
    except (TypeError, ValueError):
        profile["opacity"] = 100 if safe_visual_defaults else 88
    font = profile.get("font")
    if not isinstance(font, dict):
        font = {}
        profile["font"] = font
    font["face"] = str(terminal_settings.get("bundled_wt_font_face", "Cascadia Mono"))
    font_size = terminal_settings.get("bundled_wt_font_size", 14)
    try:
        font["size"] = max(8, int(font_size))
    except (TypeError, ValueError):
        font["size"] = 14

    profile["experimental.retroTerminalEffect"] = retro_enabled
    profile["retroTerminalEffect"] = retro_enabled

    if safe_visual_defaults:
        profile.pop("backgroundImage", None)
        profile.pop("backgroundImageOpacity", None)
        profile.pop("backgroundImageStretchMode", None)
        profile.pop("backgroundImageAlignment", None)

    if use_pixel_shader and pixel_shader_path is not None:
        shader_text = str(pixel_shader_path)
        profile["experimental.pixelShaderPath"] = shader_text
        profile["pixelShaderPath"] = shader_text
    else:
        profile.pop("experimental.pixelShaderPath", None)
        profile.pop("pixelShaderPath", None)


def _ensure_bundled_wt_profile(
    wt_exe: str,
    terminal_settings: Mapping[str, Any],
) -> Optional[str]:
    if not bool(terminal_settings.get("bundled_wt_auto_setup_profile", True)):
        return None

    profile_name = _resolve_bundled_wt_profile_name(terminal_settings)
    settings_path = _resolve_bundled_wt_settings_path(wt_exe, terminal_settings)
    settings_document = _load_json5_document(settings_path)
    if not settings_document:
        settings_document = {
            "$schema": "https://aka.ms/terminal-profiles-schema",
            "copyFormatting": "none",
            "copyOnSelect": False,
            "profiles": {
                "defaults": {
                    "font": {"face": "Cascadia Mono", "size": 14},
                },
                "list": [],
            },
        }
    else:
        settings_document.setdefault("$schema", "https://aka.ms/terminal-profiles-schema")

    profile_list = _ensure_profile_list(settings_document)
    profile = _upsert_bundled_wt_profile(profile_list, profile_name)
    pixel_shader_path = _resolve_bundled_wt_pixel_shader_path(wt_exe, terminal_settings)
    _apply_bundled_wt_profile_defaults(
        profile,
        terminal_settings,
        pixel_shader_path=pixel_shader_path,
    )
    _ensure_focus_toggle_binding(settings_document, terminal_settings)

    try:
        _write_json_document(settings_path, settings_document)
    except OSError as exc:
        sys.stderr.write(
            f"Failed to write bundled WT profile settings: {settings_path} ({exc})\n"
        )
        return None

    return profile_name


def _candidate_bundled_wt_paths(terminal_settings: Mapping[str, Any]) -> list[Path]:
    candidates: list[Path] = []
    configured = _normalize_bundled_wt_path(terminal_settings.get("bundled_wt_path"))
    if configured is not None:
        candidates.append(configured)
    app_root = _application_root()
    for relative_path in BUNDLED_WT_RELATIVE_CANDIDATES:
        candidates.append(app_root / relative_path)

    normalized: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        path_text = str(path.resolve())
        if path_text in seen:
            continue
        seen.add(path_text)
        normalized.append(Path(path_text))
    return normalized


def _warn_bundled_wt_fallback(
    terminal_settings: Mapping[str, Any],
    *,
    system_wt_path: str,
) -> None:
    if not bool(terminal_settings.get("prefer_bundled_wt", True)):
        return
    candidates = _candidate_bundled_wt_paths(terminal_settings)
    checked = ", ".join(str(path) for path in candidates)
    sys.stderr.write(
        "Bundled Windows Terminal not found; fallback to system wt.exe. "
        f"Checked: {checked}. Using: {system_wt_path}.\n"
    )


def _warn_wt_unavailable(terminal_settings: Mapping[str, Any]) -> None:
    candidates = _candidate_bundled_wt_paths(terminal_settings)
    checked = ", ".join(str(path) for path in candidates)
    sys.stderr.write(
        "Windows Terminal not found (bundled/system); continuing in current console. "
        "To use bundled WT, place wt.exe (or WindowsTerminal.exe) in vendor/windows_terminal/x64. "
        f"Checked bundled candidates: {checked}.\n"
    )


def _normalize_settings(settings: Any) -> dict:
    if isinstance(settings, dict):
        return settings
    return {}


def _build_child_environment() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env.keys()):
        key_upper = key.upper()
        if key_upper in PYTHON_RELAUNCH_ENV_KEYS:
            env.pop(key, None)
            continue
        if key_upper.startswith("_PYI_"):
            env.pop(key, None)
            continue
        if key_upper.startswith("PYI_"):
            env.pop(key, None)
            continue
    env[WT_HOSTED_SENTINEL_ENV_KEY] = "1"
    return env


def _build_app_command(argv: Iterable[str]) -> list[str]:
    argv_list = list(argv)
    if not argv_list:
        return [sys.executable]
    script_candidate = Path(argv_list[0])
    if script_candidate.suffix.lower() in {".py", ".pyw"}:
        script_path = str(script_candidate.resolve())
        return [sys.executable, script_path] + argv_list[1:]
    return [sys.executable] + argv_list[1:]


def _build_wt_command(
    wt_exe: str, terminal_settings: Mapping[str, Any], argv: Iterable[str]
) -> list[str]:
    settings = _normalize_settings(terminal_settings)
    args = [wt_exe]

    window_target = settings.get("window_target") or DEFAULT_WINDOW_TARGET
    if window_target:
        args += ["--window", str(window_target)]

    if settings.get("focus_mode"):
        args.append("--focus")
    if settings.get("fullscreen"):
        args.append("--fullscreen")
    if settings.get("maximized"):
        args.append("--maximized")

    position = settings.get("position")
    if position:
        args += ["--pos", str(position)]
    size = settings.get("size")
    if size:
        args += ["--size", str(size)]

    args.append("new-tab")

    profile = settings.get("profile")
    if profile:
        args += ["--profile", str(profile)]

    title = settings.get("title") or DEFAULT_WT_TITLE
    if title:
        args += ["--title", str(title)]

    starting_directory = settings.get("starting_directory")
    if starting_directory:
        args += ["--startingDirectory", str(starting_directory)]

    args += _build_app_command(argv)
    return args


def maybe_launch_in_windows_terminal(
    terminal_settings: Mapping[str, Any], argv: Iterable[str]
) -> bool:
    if not _is_windows():
        return False
    if _in_windows_terminal():
        return False
    if os.environ.get("DSB_DISABLE_WT"):
        return False

    terminal_settings = _normalize_settings(terminal_settings)
    if not terminal_settings or not terminal_settings.get("enabled"):
        return False

    bundled_wt_exe = _find_bundled_wt_executable(terminal_settings)
    system_wt_exe = _find_system_wt_executable()
    wt_exe, using_bundled = _select_wt_executable(terminal_settings)
    if not wt_exe:
        _warn_wt_unavailable(terminal_settings)
        return False

    _trace_startup(
        f"wt.launcher: selected_exe={wt_exe} using_bundled={using_bundled}"
    )

    if (not using_bundled) and bundled_wt_exe is None and system_wt_exe:
        _warn_bundled_wt_fallback(terminal_settings, system_wt_path=system_wt_exe)

    wt_exe = _prefer_wt_cli_executable(wt_exe)
    _trace_startup(f"wt.launcher: normalized_exe={wt_exe}")

    _ensure_wt_portable_mode(
        wt_exe,
        terminal_settings,
        use_bundled=using_bundled,
    )

    launch_settings = dict(terminal_settings)
    if using_bundled:
        profile_name = _ensure_bundled_wt_profile(wt_exe, launch_settings)
        if profile_name and not str(launch_settings.get("profile") or "").strip():
            launch_settings["profile"] = profile_name

    args = _build_wt_command(wt_exe, launch_settings, argv)
    _trace_startup(
        "wt.launcher: command=" + " ".join(f'"{arg}"' if " " in arg else arg for arg in args)
    )
    child_env = _build_child_environment()
    try:
        subprocess.Popen(args, env=child_env)
    except OSError as exc:
        _trace_startup(
            f"wt.launcher: popen failed {type(exc).__name__}: {exc}"
        )
        sys.stderr.write(f"Failed to launch Windows Terminal: {exc}\n")
        return False
    _trace_startup("wt.launcher: launched")
    return True


def maybe_prepare_terminal(settings: Mapping[str, Any], argv: Iterable[str]) -> bool:
    terminal_settings = _normalize_settings(settings.get("terminal_integration"))
    if not terminal_settings or not terminal_settings.get("enabled"):
        return False

    backend = terminal_settings.get("backend", "windows_terminal")
    if backend == "windows_terminal":
        return maybe_launch_in_windows_terminal(terminal_settings, argv)
    if backend == "deco_terminal":
        try:
            from utils.deco_terminal import apply_deco_terminal_mode
        except Exception as exc:
            sys.stderr.write(f"Deco-terminal unavailable: {exc}\n")
            apply_ok = False
        else:
            apply_ok = apply_deco_terminal_mode(terminal_settings)
        if apply_ok:
            return False
        fallback = terminal_settings.get("fallback_backend", "classic")
        if fallback == "windows_terminal":
            return maybe_launch_in_windows_terminal(terminal_settings, argv)
        return False
    return False

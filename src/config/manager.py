import os
from copy import deepcopy
import json5
import appdirs
from pathlib import Path

from core.presets import (
    DEFAULT_FONT_PRESET_ID,
    DEFAULT_STYLE_PRESET_ID,
    DEFAULT_TEMPLATE_ID,
    get_font_preset,
    get_style_preset,
    get_template,
    list_templates,
)

DEFAULT_WT_ZOOM_OUT_KEY = "ctrl+shift+f7"
DEFAULT_WT_ZOOM_IN_KEY = "ctrl+shift+f8"


def _normalize_key_binding(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return text.replace(" ", "")


class ConfigManager:
    """
    配置管理器
    负责加载和保存用户配置、布局和模板
    """

    APP_NAME = "DecoScreenBeautifier"
    AUTHOR = "DecoTeam"

    def __init__(self):
        # 获取用户数据目录
        self.data_dir = Path(appdirs.user_data_dir(self.APP_NAME, self.AUTHOR))
        self.config_dir = Path(appdirs.user_config_dir(self.APP_NAME, self.AUTHOR))
        
        self.layouts_dir = self.data_dir / "layouts"
        self.templates_dir = self.data_dir / "templates"
        
        # 确保目录存在
        self._ensure_dirs()
        
        # 默认配置
        deco_effects_defaults = {
            "enabled": True,
            "scanlines": {
                "enabled": True,
                "spacing": 2,
                "intensity": 0.15,
                "speed": 1,
                "mode": "darken",
            },
            "glow": {
                "enabled": True,
                "intensity": 0.35,
                "radius": 1,
                "halo_alpha": 0.35,
            },
            "noise": {
                "enabled": True,
                "density": 0.02,
                "chars": " .`,",
                "color": "",
                "on_text": False,
            },
            "warp": {
                "enabled": True,
                "strength": 1,
                "probability": 0.12,
            },
        }
        crt_shader_defaults = {
            "enabled": False,
            "curvature": 0.07,
            "scanline_intensity": 0.14,
            "scanline_spacing": 2,
            "chromatic_aberration": 1,
            "vignette": 0.22,
            "noise": 0.025,
            "blur": 0.1,
            "mask_strength": 0.08,
            "jitter": 0.0,
        }
        terminal_defaults = {
            "enabled": False,
            "backend": "windows_terminal",
            "fallback_backend": "classic",
            "prefer_bundled_wt": True,
            "bundled_wt_path": "",
            "use_wt_portable_mode": True,
            "bundled_wt_auto_setup_profile": True,
            "bundled_wt_profile_name": "DecoScreenBeautifier-CRT",
            "bundled_wt_settings_path": "",
            "bundled_wt_retro_effect": True,
            "bundled_wt_enable_pixel_shader": False,
            "bundled_wt_pixel_shader_path": "",
            "bundled_wt_color_scheme": "Campbell",
            "bundled_wt_use_acrylic": True,
            "bundled_wt_opacity": 88,
            "bundled_wt_font_face": "Cascadia Mono",
            "bundled_wt_font_size": 14,
            "bundled_wt_safe_visual_defaults": True,
            "bundled_wt_enable_focus_toggle_binding": True,
            "force_bundled_wt_only": True,
            "focus_mode": True,
            "focus_mode_toggle_key": "alt+shift+f",
            "zoom_in_key": DEFAULT_WT_ZOOM_IN_KEY,
            "zoom_out_key": DEFAULT_WT_ZOOM_OUT_KEY,
            "fullscreen": False,
            "maximized": False,
            "window_target": "new",
            "profile": "",
            "title": "DecoScreenBeautifier",
            "starting_directory": "",
            "position": "",
            "size": "",
            "deco_borderless": True,
            "deco_topmost": False,
            "deco_position": "",
            "deco_size": "",
            "deco_auto_fit": True,
            "deco_monitor": "auto",
            "deco_use_work_area": False,
            "deco_effects": deco_effects_defaults,
        }
        gui_host_defaults = {
            "enabled": True,
            "monitor": "auto",
            "use_work_area": True,
            "borderless": True,
            "always_on_top": False,
            "size_px": "",
            "pos_px": "",
            "fps": 60,
            "font_face": "Cascadia Mono",
            "font_size": 14,
            "cell_aspect": 1.0,
            "effects": deepcopy(deco_effects_defaults),
            "crt_shader": deepcopy(crt_shader_defaults),
        }
        performance_defaults = {
            "enabled": False,
            "sample_interval": 1.0,
            "log_path": "",
        }
        self.settings = {
            "fps_limit": 30,
            "theme": "cyberpunk",
            "startup_enabled": False,
            "template_id": DEFAULT_TEMPLATE_ID,
            "font_preset": DEFAULT_FONT_PRESET_ID,
            "style_preset": DEFAULT_STYLE_PRESET_ID,
            "global_scale": 1.0,
            "performance_monitor": performance_defaults,
            "terminal_integration": terminal_defaults,
            "gui_host": gui_host_defaults,
        }
        self.current_template = self.settings["template_id"]

    def _ensure_dirs(self):
        """创建必要的目录"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.layouts_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def load_settings(self):
        """加载全局设置"""
        settings_path = self.config_dir / "settings.json5"
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    self.settings.update(json5.load(f))
            except Exception as e:
                print(f"Failed to load settings: {e}")
        else:
            self.save_settings()
        # 补全缺失项，兼容旧版本设置
        self.settings.setdefault("template_id", DEFAULT_TEMPLATE_ID)
        self.settings.setdefault("font_preset", DEFAULT_FONT_PRESET_ID)
        self.settings.setdefault("style_preset", DEFAULT_STYLE_PRESET_ID)
        self.settings.setdefault("global_scale", 1.0)
        terminal_settings = self.settings.get("terminal_integration")
        if not isinstance(terminal_settings, dict):
            terminal_settings = {}
            self.settings["terminal_integration"] = terminal_settings
        deco_effects_defaults = {
            "enabled": True,
            "scanlines": {
                "enabled": True,
                "spacing": 2,
                "intensity": 0.15,
                "speed": 1,
                "mode": "darken",
            },
            "glow": {
                "enabled": True,
                "intensity": 0.35,
                "radius": 1,
                "halo_alpha": 0.35,
            },
            "noise": {
                "enabled": True,
                "density": 0.02,
                "chars": " .`,",
                "color": "",
                "on_text": False,
            },
            "warp": {
                "enabled": True,
                "strength": 1,
                "probability": 0.12,
            },
        }
        crt_shader_defaults = {
            "enabled": False,
            "curvature": 0.07,
            "scanline_intensity": 0.14,
            "scanline_spacing": 2,
            "chromatic_aberration": 1,
            "vignette": 0.22,
            "noise": 0.025,
            "blur": 0.1,
            "mask_strength": 0.08,
            "jitter": 0.0,
        }
        terminal_defaults = {
            "enabled": False,
            "backend": "windows_terminal",
            "fallback_backend": "classic",
            "prefer_bundled_wt": True,
            "bundled_wt_path": "",
            "use_wt_portable_mode": True,
            "bundled_wt_auto_setup_profile": True,
            "bundled_wt_profile_name": "DecoScreenBeautifier-CRT",
            "bundled_wt_settings_path": "",
            "bundled_wt_retro_effect": True,
            "bundled_wt_enable_pixel_shader": False,
            "bundled_wt_pixel_shader_path": "",
            "bundled_wt_color_scheme": "Campbell",
            "bundled_wt_use_acrylic": True,
            "bundled_wt_opacity": 88,
            "bundled_wt_font_face": "Cascadia Mono",
            "bundled_wt_font_size": 14,
            "bundled_wt_safe_visual_defaults": True,
            "bundled_wt_enable_focus_toggle_binding": True,
            "force_bundled_wt_only": True,
            "focus_mode": True,
            "focus_mode_toggle_key": "alt+shift+f",
            "zoom_in_key": DEFAULT_WT_ZOOM_IN_KEY,
            "zoom_out_key": DEFAULT_WT_ZOOM_OUT_KEY,
            "fullscreen": False,
            "maximized": False,
            "window_target": "new",
            "profile": "",
            "title": "DecoScreenBeautifier",
            "starting_directory": "",
            "position": "",
            "size": "",
            "deco_borderless": True,
            "deco_topmost": False,
            "deco_position": "",
            "deco_size": "",
            "deco_auto_fit": True,
            "deco_monitor": "auto",
            "deco_use_work_area": False,
            "deco_effects": deco_effects_defaults,
        }
        for key, value in terminal_defaults.items():
            terminal_settings.setdefault(key, value)
        if _normalize_key_binding(terminal_settings.get("zoom_in_key")) in {"", "ctrl+plus"}:
            terminal_settings["zoom_in_key"] = DEFAULT_WT_ZOOM_IN_KEY
        if _normalize_key_binding(terminal_settings.get("zoom_out_key")) in {"", "ctrl+minus"}:
            terminal_settings["zoom_out_key"] = DEFAULT_WT_ZOOM_OUT_KEY
        deco_effects = terminal_settings.get("deco_effects")
        if not isinstance(deco_effects, dict):
            deco_effects = {}
            terminal_settings["deco_effects"] = deco_effects
        for key, value in deco_effects_defaults.items():
            if isinstance(value, dict):
                section = deco_effects.get(key)
                if not isinstance(section, dict):
                    section = {}
                    deco_effects[key] = section
                for sub_key, sub_value in value.items():
                    section.setdefault(sub_key, sub_value)
            else:
                deco_effects.setdefault(key, value)
        gui_defaults = {
            "enabled": True,
            "monitor": "auto",
            "use_work_area": True,
            "borderless": True,
            "always_on_top": False,
            "size_px": "",
            "pos_px": "",
            "fps": 60,
            "font_face": "Cascadia Mono",
            "font_size": 14,
            "cell_aspect": 1.0,
            "effects": deepcopy(deco_effects_defaults),
            "crt_shader": deepcopy(crt_shader_defaults),
        }
        gui_settings = self.settings.get("gui_host")
        if not isinstance(gui_settings, dict):
            gui_settings = {}
            self.settings["gui_host"] = gui_settings
        for key, value in gui_defaults.items():
            gui_settings.setdefault(key, value)
        gui_effects = gui_settings.get("effects")
        if not isinstance(gui_effects, dict):
            gui_effects = {}
            gui_settings["effects"] = gui_effects
        for key, value in deco_effects_defaults.items():
            if isinstance(value, dict):
                section = gui_effects.get(key)
                if not isinstance(section, dict):
                    section = {}
                    gui_effects[key] = section
                for sub_key, sub_value in value.items():
                    section.setdefault(sub_key, sub_value)
            else:
                gui_effects.setdefault(key, value)
        crt_shader = gui_settings.get("crt_shader")
        if not isinstance(crt_shader, dict):
            crt_shader = {}
            gui_settings["crt_shader"] = crt_shader
        for key, value in crt_shader_defaults.items():
            crt_shader.setdefault(key, value)
        if gui_settings.get("monitor") in {None, ""}:
            gui_settings["monitor"] = terminal_settings.get("deco_monitor", "auto")
        if gui_settings.get("use_work_area") in {None, ""}:
            gui_settings["use_work_area"] = terminal_settings.get("deco_use_work_area", True)
        if gui_settings.get("borderless") in {None, ""}:
            gui_settings["borderless"] = terminal_settings.get("deco_borderless", True)
        if gui_settings.get("always_on_top") in {None, ""}:
            gui_settings["always_on_top"] = terminal_settings.get("deco_topmost", False)
        if gui_settings.get("pos_px") in {None, ""}:
            gui_settings["pos_px"] = terminal_settings.get("deco_position", "")
        if gui_settings.get("size_px") in {None, ""}:
            gui_settings["size_px"] = terminal_settings.get("deco_size", "")
        performance_defaults = {
            "enabled": False,
            "sample_interval": 1.0,
            "log_path": "",
        }
        self.settings.setdefault("performance_monitor", performance_defaults)
        perf_settings = self.settings.get("performance_monitor")
        if not isinstance(perf_settings, dict):
            perf_settings = {}
            self.settings["performance_monitor"] = perf_settings
        for key, value in performance_defaults.items():
            perf_settings.setdefault(key, value)
        self.current_template = self.settings.get("template_id", DEFAULT_TEMPLATE_ID)

    def save_settings(self):
        """保存全局设置"""
        settings_path = self.config_dir / "settings.json5"
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json5.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def list_templates(self) -> list:
        """列出所有内置模板"""
        return list_templates()

    def get_template(self, template_id: str):
        """获取模板详情"""
        return get_template(template_id)

    def get_active_template(self):
        """返回当前激活模板"""
        return get_template(self.settings.get("template_id")) or get_template(DEFAULT_TEMPLATE_ID)

    def apply_template(self, template_id: str):
        """应用模板并更新设置"""
        template = get_template(template_id) or get_template(DEFAULT_TEMPLATE_ID)
        if not template:
            return None
        self.settings["template_id"] = template["id"]
        self.settings["theme"] = template.get("theme_class", "cyberpunk")
        self.settings["font_preset"] = template.get("font_preset", DEFAULT_FONT_PRESET_ID)
        self.settings["style_preset"] = template.get("style_preset", DEFAULT_STYLE_PRESET_ID)
        self.settings["global_scale"] = template.get("global_scale", 1.0)
        self.current_template = template["id"]
        self.save_settings()
        return template

    def get_font_preset(self, preset_id: str):
        return get_font_preset(preset_id)

    def get_style_preset(self, preset_id: str):
        return get_style_preset(preset_id)

    def load_layout(self, layout_name: str) -> dict:
        """加载指定布局"""
        layout_path = self.layouts_dir / f"{layout_name}.json5"
        if layout_path.exists():
            try:
                with open(layout_path, "r", encoding="utf-8") as f:
                    return json5.load(f)
            except Exception as e:
                print(f"Failed to load layout {layout_name}: {e}")
                return {}
        return self._get_default_layout()

    def save_layout(self, layout_name: str, layout_data: dict):
        """保存布局"""
        layout_path = self.layouts_dir / f"{layout_name}.json5"
        try:
            with open(layout_path, "w", encoding="utf-8") as f:
                json5.dump(layout_data, f, indent=4)
        except Exception as e:
            print(f"Failed to save layout {layout_name}: {e}")

    def list_layouts(self) -> list:
        """列出所有可用布局"""
        return [f.stem for f in self.layouts_dir.glob("*.json5")]

    def _get_default_layout(self) -> dict:
        """返回默认布局配置"""
        return {
            "name": "Default Layout",
            "grid_size": {"rows": 2, "cols": 4},
            "components": [
                {"id": "p_hardware", "type": "HardwareMonitor", "pos": [0, 0, 2, 1]},
                {"id": "p_network", "type": "NetworkMonitor", "pos": [0, 1, 2, 1]},
                {"id": "p_clock", "type": "ClockWidget", "pos": [2, 0, 2, 2]},
            ]
        }

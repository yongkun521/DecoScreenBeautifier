import os
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
        terminal_defaults = {
            "enabled": False,
            "backend": "windows_terminal",
            "fallback_backend": "classic",
            "focus_mode": True,
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
        }
        self.settings = {
            "fps_limit": 30,
            "theme": "cyberpunk",
            "startup_enabled": False,
            "template_id": DEFAULT_TEMPLATE_ID,
            "font_preset": DEFAULT_FONT_PRESET_ID,
            "style_preset": DEFAULT_STYLE_PRESET_ID,
            "global_scale": 1.0,
            "terminal_integration": terminal_defaults,
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
        terminal_defaults = {
            "enabled": False,
            "backend": "windows_terminal",
            "fallback_backend": "classic",
            "focus_mode": True,
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
        }
        for key, value in terminal_defaults.items():
            terminal_settings.setdefault(key, value)
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
                {"id": "hardware", "type": "HardwareMonitor", "pos": [0, 0, 1, 2]},
                {"id": "clock", "type": "ClockWidget", "pos": [0, 2, 1, 2]},
                {"id": "audio", "type": "AudioVisualizer", "pos": [1, 0, 1, 4]}
            ]
        }

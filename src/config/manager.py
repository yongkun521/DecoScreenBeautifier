import os
import json5
import appdirs
from pathlib import Path

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
        self.settings = {
            "fps_limit": 30,
            "theme": "cyberpunk",
            "startup_enabled": False
        }
        self.current_layout = "default"

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

    def save_settings(self):
        """保存全局设置"""
        settings_path = self.config_dir / "settings.json5"
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json5.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings: {e}")

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

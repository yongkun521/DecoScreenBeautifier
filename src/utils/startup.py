import sys
import winreg
import os

class StartupManager:
    """
    Windows 开机自启动管理器
    """
    
    KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "DecoScreenBeautifier"

    @staticmethod
    def set_startup(enable: bool = True):
        """设置或取消开机自启动"""
        # 获取当前 Python 解释器路径和入口脚本
        # 注意：如果是打包后的 EXE，sys.executable 就是程序本身
        # 如果是脚本运行，需要 python.exe + script
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            # 开发环境：使用 pythonw.exe 避免弹窗（如果有），这里暂用 python.exe
            # 假设 main.py 在 src 目录下
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            main_script = os.path.join(project_root, "main.py")
            exe_path = f'"{sys.executable}" "{main_script}"'

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, StartupManager.KEY_PATH, 0, winreg.KEY_ALL_ACCESS)
            
            if enable:
                winreg.SetValueEx(key, StartupManager.APP_NAME, 0, winreg.REG_SZ, exe_path)
                print(f"Startup enabled: {exe_path}")
            else:
                try:
                    winreg.DeleteValue(key, StartupManager.APP_NAME)
                    print("Startup disabled")
                except FileNotFoundError:
                    pass # 已经不存在
            
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Failed to set startup: {e}")
            return False

    @staticmethod
    def check_startup() -> bool:
        """检查是否已设置开机自启动"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, StartupManager.KEY_PATH, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, StartupManager.APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

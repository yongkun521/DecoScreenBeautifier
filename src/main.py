import sys
import os

# 将 src 目录添加到 Python 路径，以便可以导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.app import DecoScreenApp

def main():
    """应用程序入口点"""
    app = DecoScreenApp()
    app.run()

if __name__ == "__main__":
    main()

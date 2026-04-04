# DecoScreenBeautifier

**DecoScreenBeautifier** 是一款专为电脑桌搭和机箱副屏设计的 CLI 风格美化软件，采用赛博朋克和复古未来主义设计语言。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)

## ✨ 核心特性

- **💻 赛博朋克 CLI 界面**：纯命令行界面，复古与未来的完美结合。
- **📊 实时硬件监控**：CPU、内存使用率实时可视化。
- **🎵 音频可视化**：支持频谱动态显示（需音频输入设备）。
- **🖼️ 字符画转换**：自动将图片转换为 ASCII/ANSI 字符画。
- **🎨 丰富的主题与模板**：内置赛博朋克风格，支持自定义布局。
- **🛠️ 可视化编辑器**：内置布局编辑器，支持组件管理。

## 🚀 快速开始

### 运行源码

1. 克隆仓库：
   ```bash
   git clone https://github.com/yourusername/DecoScreenBeautifier.git
   cd DecoScreenBeautifier
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 运行程序：
   ```bash
   python src/main.py
   ```

### 快捷键指南

| 按键 | 功能 |
| --- | --- |
| `d` | 切换 明亮/暗黑 模式 |
| `e` | 打开 **布局编辑器** |
| `t` | 打开 **模板选择器** |
| `q` | 退出程序 |

## 🛠️ 自定义配置

配置文件位于用户数据目录中（Windows 下通常为 `AppData\Local\DecoTeam\DecoScreenBeautifier`）。

- **settings.json5**: 全局设置（FPS、主题等）。
- **layouts/**: 存放自定义布局文件。

## 📦 构建发行版

使用 PyInstaller 打包为独立 EXE：

```bash
pip install pyinstaller
pyinstaller DecoScreenBeautifier.spec
```

构建完成后，主入口可执行文件位于 `dist/DecoScreenBeautifier.exe`。

若需要分发“开箱即用”的内置 Windows Terminal 体验，还需要一并分发 `dist/vendor/windows_terminal/` 目录。

## 📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

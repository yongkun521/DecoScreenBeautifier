# DecoScreenBeautifier 开发进度追踪

本文档用于追踪 DecoScreenBeautifier 项目的开发进度。项目旨在开发一款面向电脑副屏的 CLI 风格赛博朋克美化软件。

## 📅 第一阶段：基础设施与核心 UI (Phase 1: Infrastructure & Core UI)
> 目标：搭建项目骨架，确立技术栈，实现基础的 TUI 显示框架。

- [x] **项目初始化**
    - [x] 创建 Python 虚拟环境 (venv)
    - [x] 安装核心依赖 (Textual, Rich, Psutil, OpenCV, etc.)
    - [x] 建立项目目录结构 (src/ui, src/components, src/core, etc.)
    - [x] 编写入口脚本 (main.py) 并验证环境
- [ ] **主显示界面 (Display Interface)**
    - [ ] 实现 `DisplayScreen` 类 (主显示容器)
    - [ ] 设计响应式网格布局 (Grid Layout)，适配长条屏分辨率 (e.g., 800x480, 1920x480)
    - [ ] 定义全局 CSS 样式表 (赛博朋克配色、字体、边框)
    - [ ] 实现基础的黑暗模式/高亮模式切换逻辑

## 🧩 第二阶段：核心组件库 (Phase 2: Component Library)
> 目标：实现用于显示信息的具体功能组件。

- [ ] **组件基类 (Base Component)**
    - [ ] 定义 `BaseWidget` 类，统一更新机制、样式接口和生命周期管理
    - [ ] 实现组件的边框渲染和标题显示
- [ ] **硬件监控组件 (Hardware Monitor)**
    - [ ] 集成 `psutil` 获取 CPU 使用率/频率
    - [ ] 集成 `psutil` 获取 内存/Swap 使用情况
    - [ ] (可选) 获取 GPU 信息 (需调研 `GPUtil` 或 `pynvml`)
    - [ ] 实现仪表盘 (Gauge) 和 迷你图 (Sparkline) 两种显示模式
- [ ] **时钟与时间组件 (Clock & Time)**
    - [ ] 实现数字时钟 (Digital Clock)
    - [ ] 实现复古翻页钟效果 (Retro Flip Clock 模拟)
    - [ ] 实现日期和天气概览组件 (需集成免费天气 API)
- [ ] **音频可视化组件 (Audio Visualizer)**
    - [ ] 集成 `pyaudio` 捕获系统音频输出
    - [ ] 使用 `numpy` 进行 FFT (快速傅里叶变换) 计算频谱
    - [ ] 实现频谱柱状图 (Bar Chart) 动态渲染
    - [ ] 优化音频处理性能，避免阻塞 UI 线程

## 🎨 第三阶段：视觉特效引擎 (Phase 3: Visual Engine)
> 目标：实现 CLI 风格独特的视觉效果，包括图片转字符画和故障艺术效果。

- [ ] **图像处理器 (Image Processor)**
    - [ ] 实现 `ImageProcessor` 类，封装 OpenCV/Pillow 操作
    - [ ] 开发 **位图转 ASCII/ANSI 算法** (核心功能)
    - [ ] 实现图片缩放、裁剪以适配字符网格
- [ ] **特效渲染系统 (Effects Renderer)**
    - [ ] 实现 **故障艺术 (Glitch Art)** 效果 (随机字符替换、颜色偏移、行错位)
    - [ ] 实现 **扫描线 (Scanline)** 动画效果
    - [ ] 实现 **噪点 (Noise)** 背景效果
- [ ] **用户自定义媒体组件**
    - [ ] 支持用户加载本地图片并自动转换为字符画显示
    - [ ] 支持 GIF 动画播放 (帧解析与连续渲染)

## 🛠️ 第四阶段：可视化编辑器 (Phase 4: Visual Editor)
> 目标：允许用户通过 GUI 方式自定义副屏布局。

- [ ] **编辑器界面 (Editor UI)**
    - [ ] 实现编辑器模式切换逻辑
    - [ ] 开发组件工具箱 (Toolbox) 侧边栏
    - [ ] 实现属性面板 (Property Panel)，用于修改选中组件的参数
- [ ] **布局交互 (Layout Interaction)**
    - [ ] 实现组件的 **拖拽移动 (Drag & Drop)** (基于 Textual 鼠标事件)
    - [ ] 实现组件的 **大小调整 (Resizing)**
    - [ ] 实现网格吸附功能 (Snap to Grid)
- [ ] **实时预览 (Live Preview)**
    - [ ] 在编辑器中模拟真实渲染效果
    - [ ] 提供不同屏幕尺寸的模拟画布

## 💾 第五阶段：数据持久化与模板 (Phase 5: Data & Templates)
> 目标：管理用户配置，提供预设模板。

- [ ] **配置管理 (Configuration Manager)**
    - [ ] 定义 JSON5 格式的配置文件结构 (Layouts, Settings)
    - [ ] 实现配置的加载 (Load) 与保存 (Save)
    - [ ] 实现 `appdirs` 跨平台路径管理
- [ ] **模板系统 (Template System)**
    - [ ] 设计 3-5 套内置全局模板 (如 "Cyberpunk 2077", "Retro Terminal", "Minimalist")
    - [ ] 实现模板选择与一键应用功能
- [ ] **全局设置**
    - [ ] 字符集选择 (ASCII / Block Characters / Braille)
    - [ ] 刷新率控制 (FPS Limit)

## 🚀 第六阶段：优化与发布 (Phase 6: Polish & Release)
> 目标：提升性能，增强稳定性，完成系统集成。

- [ ] **性能优化**
    - [ ] 异步组件更新机制 (Async Workers)
    - [ ] 渲染层级优化，减少重绘区域
    - [ ] 内存泄漏检测与修复
- [ ] **系统集成**
    - [ ] Windows 开机自启动功能 (Registry / Startup Folder)
    - [ ] 系统托盘图标 (System Tray) 支持 (最小化/退出/切换配置)
- [ ] **文档与构建**
    - [ ] 编写用户使用手册
    - [ ] 使用 PyInstaller 打包为独立 EXE 文件
    - [ ] 发布 Release v1.0

---
**标记说明：**
- [ ] 待开始
- [x] 已完成
- [~] 进行中

# DecoScreenBeautifier 开发进度追踪

本文档用于追踪 DecoScreenBeautifier 项目的开发进度。项目旨在开发一款面向电脑副屏的 CLI 风格赛博朋克美化软件。

## 📅 第一阶段：基础设施与核心 UI (Phase 1: Infrastructure & Core UI)
> 目标：搭建项目骨架，确立技术栈，实现基础的 TUI 显示框架。

- [x] **项目初始化**
    - [x] 创建 Python 虚拟环境 (venv)
    - [x] 安装核心依赖 (Textual, Rich, Psutil, OpenCV, etc.)
    - [x] 建立项目目录结构 (src/ui, src/components, src/core, etc.)
    - [x] 编写入口脚本 (main.py) 并验证环境
- [x] **主显示界面 (Display Interface)**
    - [x] 实现 `DisplayScreen` 类 (主显示容器)
    - [x] 设计响应式网格布局 (Grid Layout)，适配长条屏分辨率 (e.g., 800x480, 1920x480)
    - [x] 定义全局 CSS 样式表 (赛博朋克配色、字体、边框)
    - [x] 实现基础的黑暗模式/高亮模式切换逻辑
    - [x] 修复 Textual 7 下暗黑模式切换 AttributeError

## 🧩 第二阶段：核心组件库 (Phase 2: Component Library)
> 目标：实现用于显示信息的具体功能组件。

- [x] **组件基类 (Base Component)**
    - [x] 定义 `BaseWidget` 类，统一更新机制、样式接口和生命周期管理
    - [x] 实现组件的边框渲染和标题显示
- [x] **硬件监控组件 (Hardware Monitor)**
    - [x] 集成 `psutil` 获取 CPU 使用率/频率 (支持多核显示)
    - [x] 集成 `psutil` 获取 内存/Swap 使用情况
    - [x] 实现赛博风格进度条和 CPU 负载趋势图 (Sparkline)
- [x] **网络监控组件 (Network Monitor)**
    - [x] 实现实时上传/下载带宽监控
    - [x] 动态箭头指示数据流向
    - [x] 修复网络监控渲染错误（表格与文本组合）
- [x] **时钟与时间组件 (Clock & Time)**
    - [x] 实现数字时钟 (Digital Clock)
    - [x] 增加日期、星期显示及随机故障特效 (Glitch Effect)
- [x] **音频可视化组件 (Audio Visualizer)**
    - [x] 集成 `pyaudio` 捕获系统音频输出
    - [x] 使用 `numpy` 进行 FFT 计算频谱，增加对数缩放
    - [x] 实现对称式频谱柱状图，支持颜色渐变和动态平滑

## 🎨 第三阶段：视觉特效引擎 (Phase 3: Visual Engine)
> 目标：实现 CLI 风格独特的视觉效果，包括图片转字符画和故障艺术效果。

- [x] **图像处理器 (Image Processor)**
    - [x] 实现 `ImageProcessor` 类，封装 OpenCV/Pillow 操作
    - [x] 开发 **位图转 ASCII/ANSI 算法** (核心功能)
    - [x] 实现图片缩放、裁剪以适配字符网格
- [x] **特效渲染系统 (Effects Renderer)**
    - [x] 实现 **故障艺术 (Glitch Art)** 效果 (随机字符替换、颜色偏移、行错位)
    - [x] 实现 **扫描线 (Scanline)** 动画效果
    - [x] 实现 **噪点 (Noise)** 背景效果
- [x] **用户自定义媒体组件**
    - [x] 支持用户加载本地图片并自动转换为字符画显示
    - [x] 支持 GIF 动画播放 (帧解析与连续渲染)

## 🛠️ 第四阶段：可视化编辑器 (Phase 4: Visual Editor)
> 目标：允许用户通过 GUI 方式自定义副屏布局。

- [x] **编辑器界面 (Editor UI)**
    - [x] 实现编辑器模式切换逻辑
    - [x] 开发组件工具箱 (Toolbox) 侧边栏
    - [x] 实现属性面板 (Property Panel)，用于修改选中组件的参数
- [x] **布局交互 (Layout Interaction)**
    - [x] 实现组件的 **拖拽移动 (Drag & Drop)** (已实现 UI 框架，逻辑待优化)
    - [x] 实现组件的 **大小调整 (Resizing)** (已实现 UI 框架，逻辑待优化)
    - [x] 实现网格吸附功能 (Snap to Grid) (已集成在 Grid 布局中)
- [x] **实时预览 (Live Preview)**
    - [x] 在编辑器中模拟真实渲染效果 (通过 EditorScreen 实现)
    - [x] 提供不同屏幕尺寸的模拟画布

## 💾 第五阶段：数据持久化与模板 (Phase 5: Data & Templates)
> 目标：管理用户配置，提供预设模板。

- [x] **配置管理 (Configuration Manager)**
    - [x] 定义 JSON5 格式的配置文件结构 (Layouts, Settings)
    - [x] 实现配置的加载 (Load) 与保存 (Save)
    - [x] 实现 `appdirs` 跨平台路径管理
- [x] **模板系统 (Template System)**
    - [x] 设计 3-5 套内置全局模板 (如 "Cyberpunk 2077", "Retro Terminal", "Minimalist")
    - [x] 实现模板选择与一键应用功能
    - [x] 修复模板 ID 生成的 BadIdentifier 错误
    - [x] 修复模板选择界面网格列间距 CSS 解析错误（column-gap -> grid-gutter）
- [x] **全局设置**
    - [x] 字符集选择 (ASCII / Block Characters / Braille)
    - [x] 刷新率控制 (FPS Limit)

## 🎛 第五阶段扩展：模板/样式/字体预设 (Phase 5.x: Templates & Visual Presets)
> 目标：面向不同尺寸副屏提供丰富模板，并提升组件样式与编辑体验。

- [ ] **模板扩展与尺寸适配**
    - [x] 新增模板元数据结构（id、名称、说明、目标屏幕比例、推荐分辨率、布局/样式/字体预设绑定）
    - [x] 内置 ≥ 8 套模板，覆盖：超宽横屏、细长竖屏、方形小屏、双栏信息墙、底部状态条等
    - [x] 模板切换自动应用布局 + 主题样式 + 字体预设 + 全局缩放参数
    - [x] 模板列表支持标签/筛选（按屏幕比例、用途、风格）
    - [x] 修复模板面板刷新导致 ListView 重复 ID 报错（无法打开模板面板）
- [ ] **组件样式与布局变体**
    - [x] 为核心组件提供 2-3 套样式变体（密集/极简/仪表盘/横条版）
    - [x] 为长条屏增加紧凑与纵向布局变体（组件标题、边框、内边距自适应）
    - [x] 统一样式 Token（边框、条形、标题、颜色）供模板复用
- [ ] **字体/字符预设体系**
    - [x] 建立字体预设注册表（标题字体、条形字符、趋势线字符、图像字符集）
    - [x] 提供多套字符集/字形风格（细线/块状/点阵/故障风格）
    - [x] 模板默认绑定字体预设，可在设置中手动覆盖
- [ ] **全局缩放参数**
    - [x] 增加 `global_scale` 设置（影响字符像素密度/图像像素化程度）
    - [~] 图像/GIF 渲染使用缩放参数重采样
    - [~] 编辑器提供缩放预览与快捷切换
- [ ] **组件编辑器优化**
    - [~] 组件库分组与搜索（监控/媒体/装饰/信息）
    - [~] 组件样式变体选择（同一组件多风格）
    - [x] 编辑器加载当前模板布局，并支持组件增删与位置/尺寸编辑
    - [x] 修复编辑器组件列表刷新时 ListView 重复 ID 报错
    - [ ] 模板预览卡片与一键应用
    - [ ] 画布支持屏幕比例/分辨率切换与网格标尺

## 🚀 第六阶段：优化与发布 (Phase 6: Polish & Release)
> 目标：提升性能，增强稳定性，完成系统集成。

- [~] **性能优化**
    - [x] FPS 限制接入 TEXTUAL_FPS + 性能采样日志
    - [ ] 异步组件更新机制 (Async Workers)
    - [ ] 渲染层级优化，减少重绘区域
    - [ ] 内存泄漏检测与修复
- [ ] **系统集成**
    - [x] Windows 开机自启动功能 (Registry / Startup Folder)
    - [x] 启动时依赖检查与缺失提示
    - [~] Windows Terminal 集成与无框模式尝试
        - [x] 添加 Windows Terminal 自动启动逻辑（可配置）
        - [x] 增加配置说明与使用文档
        - [ ] 评估/验证 Windows Terminal 二次开发或内置打包可行性
    - [~] Deco-Terminal（自研终端外壳）
    - [x] 后端选择与回退策略
    - [x] conhost 无边框基础处理（Win32）
    - [x] 窗口定位/尺寸自适配（多副屏）
    - [x] 渲染数据接口与字体/颜色输出
        - [x] 扫描线/辉光等复古效果
    - [ ] 系统托盘图标 (System Tray) 支持 (最小化/退出/切换配置)
- [~] **文档与构建**
    - [ ] 编写用户使用手册
    - [~] 使用 PyInstaller 打包为独立 EXE 文件
    - [x] 构建脚本（build_exe.ps1 / build_portable.ps1）
    - [x] 实用化补充说明（性能监控配置 / 兼容性报告 / 打包脚本）
    - [x] 草稿版单文件打包验证（默认图标）
    - [x] dist 打包产物加入 gitignore
    - [x] build 打包缓存加入 gitignore 并从版本库移除
    - [x] 使用 git-filter-repo 清理 build 历史（待强推）
    - [ ] 发布 Release v1.0

---
**标记说明：**
- [ ] 待开始
- [x] 已完成
- [~] 进行中

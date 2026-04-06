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
        - [~] 评估/验证 Windows Terminal 二次开发或内置打包可行性
            - [x] 方案调研（2026-02-07）：Windows Terminal 可通过 Unpackaged(Zip)+Portable 模式随软件分发，并将 `settings` 与运行状态隔离在应用目录，不干扰用户既有配置
            - [x] 方案决策（2026-02-07）：采用“Windows Terminal 作为可选捆绑宿主”路线（GUI 宿主继续默认入口）
            - [x] 开发待办文档（2026-02-07）：`docs/WindowsTerminal_可选捆绑宿主_开发待办.md`
            - [~] M1+M2 实施（2026-02-07）：已完成内置 WT 目录/版本元信息、构建开关、启动器“内置优先+回退+portable”、配置项补齐
            - [x] M3 实施（2026-02-07）：完成内置 WT 专用 `DecoScreenBeautifier-CRT` profile 自动初始化，默认写入 `experimental.retroTerminalEffect`，并支持可选 `experimental.pixelShaderPath`（含占位 shader）
            - [x] M4 实施（2026-02-07）：已补齐标准包/增强包分级、启动自检回退提示、WT 验收脚本与文档；增强包实打包后评审结论升级为“继续”
            - [x] PoC 验证（2026-02-07）：已完成内置便携版 Windows Terminal 实打包与验证，启动专用 `Deco` 配置通过（含 `experimental.retroTerminalEffect`，并支持可选 `experimental.pixelShaderPath`）
            - [x] 体验验证（2026-02-07，本机内置+系统 WT）：1080x480 / 1920x480 两档在 `focus/fullscreen` 下 smoke 启动通过（见 `build/validation/wt_bundle/wt_bundle_report.json`）
            - [x] 入口纠偏（2026-02-07）：`DecoScreenBeautifier.exe` 改为终端宿主入口并强制内置 WT 优先；GUI 入口调整为 `DecoScreenBeautifier_gui.exe`
            - [x] 崩溃修复（2026-02-07）：修复内置 WT 启动时 `No module named encodings`（清理继承的 PyInstaller Python 环境变量后再拉起子进程）
            - [x] 灰屏修复（2026-02-08）：增强 WT 宿主判定（`DSB_WT_HOSTED` + 父进程链）避免重复拉起；终端宿主内异常改为 stderr+日志，避免“有错误音效但无可见弹窗”
    - [~] GUI 宿主（方案B：自带渲染，不依赖外部终端）
    - [x] 设计文档（docs/方案B_GUI自带渲染_设计文档.md）
    - [x] 设计文档待办梳理：为可执行项补充方框并校准 4.x 状态
    - [x] MVP：窗口/渲染/布局/特效管线
    - [x] 打包：GUI 默认入口 EXE
    - [x] V1：模板选择/最小设置/缩放/窗口持久化
    - [x] V2：像素级 CRT 后处理（曲率/色散/扫描线/噪点/暗角）
    - [x] V2：GUI 版布局编辑器（拖拽/网格对齐/尺寸预览）
    - [x] 启动健壮性（2026-02-07）：`main_gui.py` 增加 Windows Qt DLL 路径预热（`PATH` + `os.add_dll_directory`）
    - [x] 启动提示改进（2026-02-07）：Qt 运行时报错弹窗增加 VC++ 2015-2022 x64 官方下载链接
    - [x] 打包修复（2026-02-07）：`DecoScreenBeautifier.spec` 统一优先使用 PySide6 自带 `VCRUNTIME140*.dll`，规避根目录运行库版本冲突
    - [x] 启动诊断（2026-02-07）：Qt 预检查失败时写出 `qt_runtime_error.log`（含 `_MEIPASS`/PATH/traceback）
    - [x] 打包修复（2026-02-07）：移除根目录 `api-ms-win-crt-* / ucrtbase.dll` 注入，仅保留 PySide6 侧 CRT 运行库
    - [x] 启动诊断（2026-02-07）：新增 DLL 逐项探测与预加载记录（`dll_probe` / `preload_notes`）用于定位 `QtCore` 依赖链失败点
    - [x] 打包修复（2026-02-07）：`DecoScreenBeautifier.spec` 全面排除 Anaconda 来源 DLL（含 ICU/API-SET），避免 onefile 运行时混装
    - [x] 启动修复（2026-02-07）：`main_gui.py` 启动前清理 PATH 中 conda 目录，降低 Qt 依赖解析误命中概率
    - [x] legacy 启动修复（2026-02-07）：`main.py` 在 `DecoScreenBeautifier_legacy_terminal.exe` 冻结运行时不再二次拉起 Windows Terminal；新增启动异常弹窗与 `legacy_terminal_error.log`，避免“只有报错音效无可见错误”
    - [ ] 下一步优化计划（2026-02-07）：`docs/GUI观感与窗口交互_下一步待办.md`（文字排布稳定性、抖动控制、窗口化与可调尺寸）
    - [~] 验收：按设计文档 10.1/10.2 逐项验证（已新增自动化脚本与报告产物）
        - [x] `scripts/validate_gui_host.py`：功能验收闭环（metrics/perf/report）
        - [x] `scripts/benchmark_gui_host.py`：性能验收闭环（1080x480/1920x480）
        - [x] 环境阻塞已解除：2026-02-07 本机 Qt 运行时问题已排除（升级项目 venv 至 Python 3.11）
        - [~] 性能待优化：2026-02-07 本机基准未达临时阈值（FPS 偏低、CPU 偏高）
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
## 2026-02-08 Windows Terminal 灰屏修复记录
- [x] 复现并定位：`DecoScreenBeautifier.exe` 在部分机器通过内置 `WindowsTerminal.exe` 直接拉起时，会出现灰屏无光标（有错误音效但无可见弹窗）。
- [x] 根因修复：`src/utils/terminal_launcher.py` 改为优先调用内置 `wt.exe`（CLI 入口）而不是直接调用 `WindowsTerminal.exe`，并兼容目录自动识别 `wt.exe/WindowsTerminal.exe`。
- [x] 启动链路增强：新增 `BUNDLED_WT_EXECUTABLE_NAMES` 与更多候选路径，缺失提示文案同步更新为支持两种可执行文件名。
- [x] 验证通过：执行 `scripts/validate_wt_bundle.py --with-smoke-run --mode focus --mode fullscreen`，报告显示 `selection.selected_path` 已指向 `vendor/windows_terminal/x64/wt.exe` 且 smoke 全通过。

## 2026-02-08 灰屏问题续修（中断后继续）
- [x] 启动错误可见性修复：`src/main.py` 中冻结版（`sys.frozen=True`）不再因“终端宿主误判”而跳过 `MessageBox`，避免出现“有错误音效但无可见弹窗”。
- [x] 启动链路追踪：新增 `legacy_terminal_startup_trace.log` 追踪日志（并兜底写入 `%TEMP%`），记录 `main: enter`、`terminal_prepared`、`app.run start/end`、异常与错误提示触发点。
- [x] 依赖降级：将 `pyaudio`、`cv2`、`Pillow` 从强制启动依赖中移除，改为组件级降级（音频组件自动 mock，图像组件显示可用性提示），避免因单组件依赖缺失导致整屏灰屏。
- [x] 组件容错：`src/ui/display.py` 改为安全构造组件（单个组件初始化失败不阻塞全屏挂载）。
- [x] 终端链路回归：`scripts/validate_wt_bundle.py --with-smoke-run --mode focus --mode fullscreen` 通过，仍为“继续”。
- [ ] 待用户现场复测：若仍灰屏，需回传 `%TEMP%\legacy_terminal_startup_trace.log` 与 `legacy_terminal_error.log`（项目目录或 `%LOCALAPPDATA%\DecoTeam\DecoScreenBeautifier`）用于精确定位。

## 2026-02-08 灰屏根因闭环（Rich Unicode 动态模块）
- [x] 根因定位：通过 `app._handle_exception` 启动追踪发现渲染期异常 `ModuleNotFoundError: No module named 'rich._unicode_data.unicode17-0-0'`，导致 Textual 合成器首帧崩溃并呈现灰屏。
- [x] 打包修复：`DecoScreenBeautifier.spec` 增加 `collect_submodules('rich._unicode_data')`，将 Rich 的 Unicode 数据动态子模块完整打入 onefile。
- [x] 稳定性增强：
  - `src/components/base.py` 增加 `_safe_update_content`（组件更新异常隔离与降级占位）。
  - `src/components/audio.py` 冻结版默认 mock（可通过 `DSB_ENABLE_AUDIO_CAPTURE=1` 开启真实采集）。
  - `src/utils/terminal_launcher.py` 增加 WT 启动命令追踪，便于现场排查。
- [x] 视觉安全默认：冻结版默认 `bundled_wt_safe_visual_defaults=true`，并将内置 WT profile 强制为 `useAcrylic=false`、`opacity=100`、`retro=false`。
- [x] 复测通过（2026-02-08）：
  - `scripts/validate_wt_bundle.py --with-smoke-run --mode focus --mode fullscreen`
  - `dist/DecoScreenBeautifier.exe` 直启（父进程拉起 WT + 子进程入屏）
  - `dist/legacy_terminal_startup_trace.log` 显示 `display.first_paint ... query_all=20`，无未处理异常。

## 2026-02-08 内置 WT 布局与复古效果修复
- [x] 右上组件错位修复：`src/ui/display.py` 中将 `p_boot_hint` 初始设为 `display=false`，避免其占用网格格位导致主组件布局偏移。
- [x] “Loading widgets...” 常驻问题修复：新增 `DisplayScreen._sync_boot_hint_with_layout()`，在存在可见业务组件时自动隐藏提示；仅当模板将所有组件都禁用时才显示提示文案。
- [x] 内置 WT 复古效果恢复：
  - `src/main.py` 不再在冻结版安全视觉分支中强制关闭 `bundled_wt_retro_effect`。
  - `src/utils/terminal_launcher.py` 保持安全默认（Acrylic/Pixel Shader 关闭）但允许写入 `retroTerminalEffect=true`。
- [x] 验证通过（2026-02-08）：
  - `venv\Scripts\python.exe -m py_compile src\ui\display.py src\main.py src\utils\terminal_launcher.py`
  - `venv\Scripts\python.exe scripts\validate_wt_bundle.py --with-smoke-run --mode focus --mode fullscreen --output-dir build\validation\wt_bundle_after_fix_smoke`
  - `build\validation\wt_bundle_after_fix\portable_settings_snapshot.json` 中 `experimental.retroTerminalEffect` 与 `retroTerminalEffect` 均为 `true`。

## 2026-02-08 打包产物更新
- [x] 执行干净打包：`powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1 -Clean -IncludeBundledWT`
- [x] 产物生成：
  - `dist\DecoScreenBeautifier.exe`
  - `dist\DecoScreenBeautifier_gui.exe`
  - `dist\vendor\windows_terminal\x64\*`（含 `.portable`）
- [x] 路由校验：`venv\Scripts\python.exe scripts\validate_wt_bundle.py --output-dir build\validation\wt_bundle_after_package`，结果为“继续”。

## 2026-02-08 内置 WT 无边框窗口拖动方案评估
- [x] 问题确认：当前默认 `terminal_integration.focus_mode=true` 会在启动时追加 `--focus`，隐藏标题栏/标签栏后无法直接鼠标拖动窗口。
- [x] 方案梳理：
  - 方案 A（推荐）：将 `focus_mode=false`，恢复标题栏拖动；可保留 `maximized=true` 维持近似无框观感。
  - 方案 B（折中）：保持 `focus_mode=true`，但自动写入一个 `toggleFocusMode` 快捷键（如 `Alt+Shift+F`），需要拖动时先切回可拖状态。
- [x] 方案 B 落地（默认无框）：
  - `src/config/manager.py` 新增 `bundled_wt_enable_focus_toggle_binding=true` 与 `focus_mode_toggle_key="alt+shift+f"` 默认项（保持 `focus_mode=true`）。
  - `src/utils/terminal_launcher.py` 在内置 WT profile 初始化时自动写入 `toggleFocusMode` 快捷键。
  - `src/utils/terminal_launcher.py` 新增运行时切换能力：通过发送快捷键触发 Focus Mode 开关（用于边框开/关切换）。
  - `src/ui/app.py` 新增全局动作 `action_toggle_wt_border`（绑定 `B` 键）。
  - `src/ui/display.py` 底部新增按钮 `Toggle Border (B)`，点击可切换边框。
  - `src/ui/styles.tcss` 新增 `#btn_toggle_border` 样式，固定在底部工具栏区域。
- [x] 验证通过：
  - `venv\\Scripts\\python.exe -m py_compile src\\config\\manager.py src\\utils\\terminal_launcher.py src\\ui\\app.py src\\ui\\display.py`
  - `venv\\Scripts\\python.exe scripts\\validate_wt_bundle.py --output-dir build\\validation\\wt_bundle_after_toggle_border`
  - `build\\validation\\wt_bundle_after_toggle_border\\portable_settings_snapshot.json` 中已包含 `actions -> toggleFocusMode -> alt+shift+f`。

## 2026-02-08 打包产物更新（含 Toggle Border）
- [x] 执行干净打包：`powershell -ExecutionPolicy Bypass -File scripts\\build_exe.ps1 -Clean -IncludeBundledWT`
- [x] 产物生成：
  - `dist\\DecoScreenBeautifier.exe`
  - `dist\\DecoScreenBeautifier_gui.exe`
  - `dist\\vendor\\windows_terminal\\x64\\*`（含 `.portable`）
- [x] 路由校验：`venv\\Scripts\\python.exe scripts\\validate_wt_bundle.py --output-dir build\\validation\\wt_bundle_after_package_toggle_border`，结果为“继续”。

## 2026-02-08 显示区标题栏/工具栏切换增强
- [x] 底部工具栏扩展为三个按钮：
  - `Toggle Border (B)`：切换 WT Focus/边框模式。
  - `Toggle Header (H)`：切换上方标题栏显示状态。
  - `Toggle Toolbar (M)`：切换下方工具栏显示状态。
- [x] 交互增强：当工具栏隐藏后，鼠标点击显示区任意位置可自动恢复工具栏。
- [x] 实现位置：
  - `src/ui/display.py`：新增按钮、快捷键绑定与显示状态切换逻辑。
  - `src/ui/styles.tcss`：新增 `#bottom_toolbar` 与 `.toolbar-btn` 样式。
- [x] 语法校验：`venv\\Scripts\\python.exe -m py_compile src\\ui\\display.py src\\ui\\app.py src\\config\\manager.py src\\utils\\terminal_launcher.py`

## 2026-02-08 打包产物更新（含 Header/Toolbar Toggle）
- [x] 执行干净打包：`powershell -ExecutionPolicy Bypass -File scripts\\build_exe.ps1 -Clean -IncludeBundledWT`
- [x] 产物生成：
  - `dist\\DecoScreenBeautifier.exe`
  - `dist\\DecoScreenBeautifier_gui.exe`
  - `dist\\vendor\\windows_terminal\\x64\\*`（含 `.portable`）
- [x] 路由校验：`venv\\Scripts\\python.exe scripts\\validate_wt_bundle.py --output-dir build\\validation\\wt_bundle_after_package_header_toolbar_toggle`，结果为“继续”。

## 2026-04-04 项目现状回顾与路线调整
- [x] 现状确认：`dist\\DecoScreenBeautifier.exe`（内置 Windows Terminal 宿主）已成为当前实际主入口，且用户本机双击运行效果稳定、观感满足预期。
- [x] 路线确认：`dist\\DecoScreenBeautifier_gui.exe`（方案 B）当前观感明显不理想，不再作为推荐使用的回退方案。
- [x] 收口完成（2026-04-04）：`DecoScreenBeautifier.spec` 已停止默认打包 `DecoScreenBeautifier_gui.exe`，收敛为以 WT 宿主为主的单主入口发布。
- [~] 文档收口（2026-04-04）：已更新 README、`docs/DecoTerminal_实用化补充.md`、`docs/WindowsTerminal_可选捆绑宿主_开发待办.md` 等关键说明；历史设计/验收文档中的 GUI 记录保留作为归档参考。

## 2026-04-05 商业化备忘
- [x] 新增商业化备忘文档：`docs/商业化思路与定价备忘.md`
- [x] 当前建议结论：短期不上 Steam 也完全可行；优先验证独立渠道售卖。
- [x] 当前建议定价：`39 元首发 / 49 元常规`，海外对应 `$5.99 / $7.99`。

## 2026-04-05 Textual 主界面增强
- [x] 主界面底部 Footer 新增 `Zoom - / Zoom +` 快捷项。
  - [x] 行为对齐 Windows Terminal 的 `Ctrl+- / Ctrl++` 缩放。
  - [x] 新增 `terminal_integration.zoom_in_key / zoom_out_key` 配置项，便于后续自定义宿主快捷键。
  - [x] 缩放入口已并回现有 Footer，不再额外占用一整排自定义工具栏。
  - [x] `Zoom +` 的宿主热键发送改为按当前 Windows 键盘布局解析，避免 `Shift+=` 这类美式键位硬编码导致放大失效。
  - [x] 修复 Footer 缩放项与宿主缩放热键互相递归触发的问题，避免点击 `Zoom +` 后重复提示并卡死。
  - [x] 修复 Footer 因空描述自动隐藏 `Zoom - / Zoom +` 的问题，现已稳定显示在左下角。
  - [x] 内置 WT 现会自动写入专用缩放热键（默认 `Ctrl+Shift+F7/F8`），不再依赖 `Ctrl+- / Ctrl++` 的字符键位解析，避免 `Zoom +` 在不同键盘布局下失效。
- [x] Textual 主显示页接入布局文件读取。
  - [x] 当前模板对应的 `layouts/<template_id>.json5` 会在主显示界面真实生效。
  - [x] 编辑器保存布局后，返回主界面会按新布局重新排布。
  - [x] 主显示网格尺寸现在会跟随布局文件里的 `grid_size` 动态刷新，不再被模板默认 CSS 的固定行列数撑出“幽灵空行”。
- [x] 图片组件支持布局级图片路径。
  - [x] 编辑器属性面板新增 `Image Path` 输入项。
  - [x] 图片路径支持绝对路径与常见相对路径解析。
- [x] 编辑器删除组件交互补强。
  - [x] 新增中部组件列表下方的 `Delete Selected` 按钮。
  - [x] 删除后自动选中下一个可编辑组件，减少重复操作。
- [x] 编辑器空白行/列收缩能力。
  - [x] 删除或调整组件后，完全空白的行默认自动移除。
  - [x] 删除或调整组件后，完全空白的列默认自动压缩，尽量减少“空着一格”的浪费。
  - [x] 新增 `Add Row / Remove Row`，允许用户显式保留或移除空白行。
- [x] 新增 `Redline 2077` 主题/模板。
  - [x] 新增 `edgerunner_block` 字符预设。
  - [x] 新增 `redline_2077` 样式预设与 `theme-redline-2077` 主题类。
- [x] 新增用户说明文档：`docs/自定义界面说明.md`

# 方案 B：GUI 自带渲染（不依赖外部终端）设计文档

本文档描述将 DecoScreenBeautifier 从“终端 TUI(Textual)”迁移到“GUI 自带渲染”的总体设计方案。
目标是让用户像运行普通软件一样双击启动，获得一致的无边框/副屏适配/复古特效体验，不再受 Windows Terminal / conhost / IDE 运行方式影响。

## 0. 开发待办（面向编程 Agent）

> 说明：本节将“需要开发的任务”改写为明确的待办条目（带方框），方便后续编程 agent 按步骤实现。

### 0.1 MVP（可运行 GUI 宿主）

- [x] 设计文档：本文件（将实现任务拆解为可执行待办）
- [ ] 依赖：在 venv 安装/锁定 PySide6（记录版本与安装方式）
- [ ] 入口：新增 `src/main_gui.py` 作为 GUI 默认入口（双击可运行）
- [ ] 配置：在 `src/config/manager.py` 增加 `gui_host` 默认项，并兼容旧配置
- [ ] 目录：新增 `src/gui_host/`（app/window/surface/scene/layout/input/errors）
- [ ] 目录：新增 `src/gui_components/`（base + 2~3 个 MVP 组件）
- [ ] 渲染：实现 `RenderGrid -> QPainter` 绘制（行段合并，减少 per-cell draw）
- [ ] 合成：实现 Scene 合成（layout -> subgrid -> main grid）并接入 `apply_retro_effects`
- [ ] 多屏：实现 `monitor=auto/primary/secondary/index` 与 `use_work_area` 行为
- [ ] 输入：实现 GUI 快捷键（`d/e/t/q`），至少 `q` 退出、其余可先占位
- [ ] 打包：更新 PyInstaller 产物，输出 GUI EXE（无控制台）+ legacy EXE（保留终端）
- [ ] 验收：按“10. 测试与验收”逐项通过（功能 + 性能）

### 0.2 V1（可用性增强）

- [ ] 模板：GUI 中支持选择/应用模板（复用 `src/core/presets.py` 模板数据）
- [ ] 设置：新增最小设置 UI（屏幕/置顶/效果开关/字体）
- [ ] 缩放：`global_scale` 在 GUI 渲染中生效（cell size/字符密度/布局）
- [ ] 持久化：窗口位置/尺寸/屏幕选择等在 `settings.json5` 持久化

### 0.3 V2（体验强化）

- [ ] 后处理：像素级 CRT shader（建议 Qt Quick / OpenGL 路线）
- [ ] 编辑器：迁移可视化编辑器到 GUI（拖拽/对齐/预览）

## 1. 背景与问题

当前版本以 Textual/Rich 为核心渲染框架，依赖外部终端宿主：

- 终端边框、标题栏、渲染方式受宿主控制（Windows Terminal / conhost 不同）。
- 用户启动方式不可控（从 WT、cmd、PowerShell、IDE 等启动），导致“无框/特效一致性”无法保证。
- 我们对窗口生命周期、DPI、多屏定位、置顶等能力控制有限。

因此需要一条“完全不依赖外部终端”的路线：提供自带窗口与渲染的 GUI 宿主。

## 2. 目标与非目标

### 2.1 目标（Must）

- 双击 EXE 启动，直接出现自绘窗口，不依赖用户终端。
- 主窗口支持：无边框、置顶可选、指定屏幕/工作区适配、记住位置与尺寸。
- 保留“字符网格 + 样式”渲染理念：统一字体/颜色/特效输出。
- 复用现有渲染模型与特效管线：
  - `src/core/renderer.py` 的 `RenderGrid`/`RenderCell`/`TextStyle`
  - `src/core/retro_effects.py` 的扫描线/辉光/噪点/畸变
- 配置继续使用 `settings.json5`（JSON5 + appdirs 路径），对老配置兼容。
- 出现异常时可回退：提供“传统终端模式(legacy)”作为开发/应急路径。

### 2.2 非目标（暂不做 / Won't）

- 不做“通用终端模拟器”（不需要兼容全量 VT 序列、ssh、shell 等）。
- 不追求一开始就 240FPS；优先稳定 30/60FPS 与低 CPU 占用。
- 不要求第一阶段完成完整可视化编辑器（可先做只读展示 + 基础快捷键）。

## 3. 技术选型（GUI 宿主）

GUI 自带渲染有两条实现分支：

### 3.1 选型建议：PySide6 / Qt 6（推荐）

理由：
- Python 侧复用现有核心逻辑成本最低（无需引入 JS 运行时）。
- Qt 对 Windows 多屏、DPI、无边框窗口、置顶等支持成熟。
- 渲染可从 QPainter 起步，后续可升级到 QOpenGLWidget / Qt Quick 做更强特效。
- 便于继续沿用 PyInstaller 打包流水线（现有已有 `DecoScreenBeautifier.spec`）。

代价：
- 引入 PySide6 体积会增大（但通常仍小于 Electron）。
- 需要处理字体加载与字符像素对齐，避免模糊。

### 3.2 备选：Electron（不作为本方案主线）

优点：
- UI 表达力强（CSS/WebGL 做 CRT 特效很方便）。
- 无边框窗口与动效实现简单。

缺点：
- 体积更大，工程拆分（Python 后端 + JS 前端通信）复杂度上升。
- 当前仓库缺少 Electron 源码工程化结构（`dist-electron` 仅是构建产物），需要重新搭建。

本设计文档以 PySide6/Qt 为主线。

## 4. 总体架构

### 4.1 组件分层

建议新增一条“GUI 渲染链路”，并保持与现有 Textual 链路并行一段时间：

- **Core（已存在，复用）**
  - `RenderGrid` / `TextStyle` / `render_rich_to_grid`
  - `RetroEffectConfig` / `apply_retro_effects`
  - 配置加载：`src/config/manager.py`
- **GUI Host（新增）**
  - 窗口/多屏管理（Qt）
  - 渲染表面（绘制字符网格 + 后处理）
  - 定时器驱动（帧循环、组件更新）
- **Scene/Layout（新增）**
  - 根据模板/布局把各“组件渲染结果”拼装到主网格
  - 统一应用全局特效、全局缩放
- **Data Providers（逐步抽离）**
  - CPU/内存/网络/时间/媒体等数据源，尽量与 UI 框架解耦

### 4.2 建议的代码结构（目录/模块）

建议新增目录（命名可调整）：

- [ ] 新增 `src/gui_host/app.py`：Qt Application 启动与全局配置加载
- [ ] 新增 `src/gui_host/window.py`：主窗口（无边框/置顶/多屏定位）
- [ ] 新增 `src/gui_host/surface.py`：渲染表面（接收 RenderGrid 并绘制）
- [ ] 新增 `src/gui_host/scene.py`：Scene 管理（组件、布局、合成、特效）
- [ ] 新增 `src/gui_host/layout.py`：布局计算（layout config -> grid region mapping）
- [ ] 新增 `src/gui_host/input.py`：快捷键与交互路由（d/e/t/q 等）
- [ ] 新增 `src/gui_host/errors.py`：错误提示与回退策略（MessageBox、日志）
- [ ] 新增 `src/gui_components/base.py`：GUI 组件接口（update/render）
- [ ] 新增 `src/gui_components/hardware.py`：MVP 硬件组件（CPU/内存）
- [ ] 新增 `src/gui_components/clock.py`：MVP 时钟组件（时间/日期）
- [ ] 新增 `src/gui_components/network.py`：MVP 网络组件（上/下行）
- [ ] （可选）新增 `src/utils/monitors.py`：复用 Windows 监视器/工作区枚举逻辑

策略：不需要一次性搬迁所有文件；先加 GUI Host 与少量组件，跑通 MVP，再逐步抽离旧组件。

### 4.3 运行时流程（简化）

1) 读取 `settings.json5`
2) 创建 Qt Application + 主窗口
3) 创建 Scene（加载模板/布局 + 初始化组件）
4) 启动渲染循环（QTimer）
5) 每帧：
   - 组件采样（按各自频率）
   - 组件渲染到子网格
   - Scene 合成主网格
   - 应用全局复古特效
   - 绘制到窗口

### 4.4 核心接口草案（便于实现对齐）

GUI 组件建议使用一个很薄的协议（不绑定具体 GUI 框架）：

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.renderer import RenderGrid


@dataclass(frozen=True)
class RenderContext:
    frame_index: int
    now_ts: float
    global_scale: float
    style_preset: dict
    visual_preset: dict


class GuiComponent(Protocol):
    id: str

    def update(self, now_ts: float) -> None:
        ...

    def render(self, width: int, height: int, ctx: RenderContext) -> RenderGrid:
        ...
```

Scene 负责：
- 调度 `update()`（可以按组件各自频率）
- 调用 `render()` 得到子网格
- 合成主网格 + 应用特效
- 把最终网格交给 `surface.py` 绘制

## 5. 渲染模型与管线

### 5.1 继续采用字符网格模型

现有模型：
- `RenderGrid(width, height, cells[y][x])`
- `RenderCell(char, style)`
- `TextStyle(fg, bg, bold, dim, blink, ...)`

优势：
- 组件与宿主解耦：组件只负责“画什么”（网格），宿主负责“怎么显示”（GUI 绘制）。
- 复古特效可直接在网格层做（已实现）。

### 5.2 GUI 绘制策略（MVP）

MVP 目标：在 Python + QPainter 下达到可用帧率。

建议绘制策略：
- 选择等宽字体，计算单元格像素大小（cell_w/cell_h）。
- 对每一行做“同样式连续字符”合并（run-length encoding）：
  - 相同 `TextStyle` 的连续单元格合并成一个字符串段
  - 调用一次 `drawText` 绘制一段，减少 per-cell 绘制开销
- 背景色：
  - 可选择先整屏填充背景，再仅对有 bg 的段落绘制矩形底色
  - 或者将 bg 作为“段落底色”绘制（矩形填充）

### 5.3 特效管线

MVP：复用现有网格特效：
- `scanlines`：周期性暗化/亮化行
- `glow`：对文本周围 halo 上色
- `noise`：按密度在背景或文本上叠加字符噪点
- `warp`：按概率做轻微错位

后续增强（可选）：
- 像素级后处理（模糊、色散、屏幕曲率、轻微抖动）
  - Qt Quick / OpenGL shader 更适合做这部分
  - 但可先保证“字符网格效果一致”，再迭代像素级真实 CRT

## 6. 布局与模板复用

### 6.1 MVP 布局：基于现有 layout 数据拼装

现有 `ConfigManager._get_default_layout()` 已给出网格布局描述：
- `grid_size`: rows/cols
- `components`: type + pos=[row, col, row_span, col_span]

GUI Scene 可直接复用该布局模型：
- 将窗口映射到“主字符网格”（例如 240x60）
- 按 layout 的 row/col 把主网格划分为区域
- 每个区域内渲染一个组件的子网格，再拷贝到主网格对应区域

### 6.2 组件渲染策略（迁移）

现状：组件基类 `src/components/base.py` 继承 Textual `Static`，与 Textual 生命周期耦合。

迁移建议（分阶段）：

阶段 1（最快落地）：
- 新增“GUI 组件接口”，不依赖 Textual：
  - `update(dt)`（可选）
  - `render(width, height) -> RenderGrid`
- 先实现 2~3 个核心组件（CPU/内存、时钟、网络）作为 GUI MVP
- 现有 Textual 组件保留不动（legacy 模式继续用）

阶段 2（复用 Rich 渲染能力）：
- GUI 组件内部可直接构造 Rich renderable（`rich.table.Table` / `rich.text.Text`）
- 通过 `render_rich_to_grid(renderable, width, height)` 转成 RenderGrid

阶段 3（逐步替换旧组件）：
- 将现有 Textual 组件的数据采集与 renderable 构造拆出来，形成纯 Python 组件
- 避免在 GUI 模式下依赖 Textual 的 timer / mount

## 7. 窗口与多屏行为

### 7.1 窗口模式

MVP 支持：
- borderless（无边框）
- always-on-top（置顶可选）
- click-through（可选，后续；副屏展示常用）
- maximize / fullscreen（可选）

### 7.2 多屏选择

建议与现有配置保持一致的语义（沿用 `deco_monitor` 的取值习惯）：
- `auto`：优先非主屏中面积最大的屏幕
- `primary` / `secondary` / index
- `use_work_area`：使用工作区避免任务栏

Qt 本身可枚举屏幕，但 Windows 的“工作区”与“任务栏”信息需要额外处理；
现有 `src/utils/deco_terminal.py` 已有 Windows API 屏幕与工作区枚举逻辑，可复用/抽象成 `utils/monitors.py`。

## 8. 配置设计（settings.json5）

建议新增独立配置段，避免继续混用 `terminal_integration`：

```json5
{
  "gui_host": {
    "enabled": true,
    "monitor": "auto",
    "use_work_area": true,
    "borderless": true,
    "always_on_top": false,
    "size_px": "",
    "pos_px": "",
    "fps": 60,
    "font_face": "Cascadia Mono",
    "font_size": 14,
    "cell_aspect": 1.0,
    "effects": { /* 复用 RetroEffectConfig */ }
  }
}
```

兼容策略：
- 如果 `gui_host.enabled` 不存在，默认关闭（保持旧行为）。
- 发布阶段可将 GUI 作为默认入口 EXE（用户无需配置）。
- `terminal_integration` 作为 legacy/调试功能保留一段时间，逐步标记为 deprecated。

## 9. 打包与发布

### 9.1 打包形态

- [ ] 输出 `DecoScreenBeautifier.exe`：GUI 默认入口（无控制台）
- [ ] 输出 `DecoScreenBeautifier_legacy_terminal.exe`：保留 Textual 终端入口（用于调试/兼容）

### 9.2 PyInstaller 注意点

- [ ] PySide6：验证 hooks 与 Qt 插件收集（PyInstaller 通常可自动处理，但需实际打包验证）
- [ ] 字体：将字体资源随包带入（建议 `assets/fonts`），启动时动态加载
- [ ] DPI：设置/声明 Windows DPI awareness，确保 Qt 与像素计算一致

### 9.3 启动入口建议

- [ ] 新增 `src/main_gui.py`：GUI 默认入口（最终发布 EXE 使用）
- [ ] 保留 `src/main.py`：现有 Textual 入口（开发/应急）
- [ ] 依赖检测：GUI 模式下复用/改写依赖检测逻辑（避免仅靠 stderr 提示）

## 10. 测试与验收

### 10.1 功能验收（MVP）

- [ ] 双击启动 GUI EXE：窗口无边框并可定位到副屏
- [ ] 组件刷新：CPU/内存/时钟/网络组件正常刷新
- [ ] 特效开关：`effects` 开启后有扫描线/辉光/噪点效果
- [ ] 退出清理：关闭窗口无资源泄漏、无僵尸进程

### 10.2 性能验收

- [ ] 性能目标：1080x480 / 1920x480 场景下 CPU 占用可控（阈值后续确定）
- [ ] 性能统计：通过 `performance_monitor` 或新增 GUI 性能统计（帧耗时/FPS/内存）验证

## 11. 里程碑拆解（待办）

### 11.1 MVP（可运行的 GUI 宿主）

- [ ] 新增 `src/gui_host/*`：Qt 主窗口 + 渲染表面 + Scene/布局
- [ ] 渲染实现：`RenderGrid -> QPainter`（行段合并 + 背景填充策略）
- [ ] 合成实现：layout -> subgrid -> main grid + 全局 effects 管线
- [ ] MVP 组件：clock/hardware/network（至少 2~3 个）
- [ ] 打包产物：GUI EXE（无控制台）+ legacy EXE（保留终端入口）
- [ ] 通过验收：完成“10.1/10.2”所有勾选项

### 11.2 V1（可用性增强）

- [ ] 模板：支持选择/应用模板（复用现有模板数据）
- [ ] 设置：最小设置界面（开关/屏幕/置顶/效果/字体）
- [ ] 缩放：`global_scale` 全面接入 GUI 渲染与布局

### 11.3 V2（体验强化）

- [ ] 后处理：像素级 CRT shader（色散/模糊/曲率/抖动等）
- [ ] 编辑器：迁移布局编辑器到 GUI（拖拽/对齐/预览）

## 12. 风险与对策

- 性能风险：Python + QPainter 在大网格下可能不足
  - 对策：行段合并、缓存、降低 FPS、后续迁移到 Qt Quick/OpenGL
- 字体模糊/对齐问题
  - 对策：固定 cell 尺寸、像素对齐、提供字体选择与渲染选项
- 组件迁移成本
  - 对策：先做少量核心组件，逐步抽离 Textual 依赖

---

附注：本方案 B 的核心价值是“宿主可控”，即使暂时牺牲部分 Textual 的现成布局能力，也能换来发布体验的一致性与稳定性。

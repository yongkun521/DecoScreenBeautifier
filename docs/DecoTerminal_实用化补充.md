# Deco-Terminal 实用化补充说明

本说明补充了性能监控、兼容性报告与打包脚本的使用方式，便于定位性能瓶颈或提交问题报告。

## 1. 性能监控 (performance_monitor)
配置位置：用户配置目录的 `settings.json5`。

Windows 默认路径示例：
`C:\Users\<用户名>\AppData\Local\DecoTeam\DecoScreenBeautifier\settings.json5`

配置示例：
```json5
{
    "performance_monitor": {
        "enabled": true,
        "sample_interval": 1.0,
        "log_path": "perf/perf.jsonl"
    }
}
```

说明：
- `enabled`: 是否开启性能采样。
- `sample_interval`: 采样间隔（秒）。建议 0.5 ~ 2.0。
- `log_path`: 日志路径。为空时默认写入 `data_dir/perf/perf.jsonl`。
  - 若填写相对路径，会自动拼接到应用数据目录（`data_dir`）下。
  - `data_dir` 默认位于 `C:\Users\<用户名>\AppData\Local\DecoTeam\DecoScreenBeautifier`。

日志格式：每行一个 JSON 对象，包含 `timestamp`、`elapsed`、`fps`、`cpu_percent`、`memory_mb`。

## 2. 兼容性报告
在项目根目录执行：

```bash
python scripts/compat_report.py
```

可选指定输出路径：

```bash
python scripts/compat_report.py path\\to\\compat_report.json
```

报告内容包含系统版本、Python 版本、DPI/缩放比例、以及屏幕列表信息，可用于问题反馈。

## 3. 打包脚本
入口说明：
- `DecoScreenBeautifier.exe`：终端宿主入口（Windows Terminal 路线，内置 WT 优先）。
- `DecoScreenBeautifier_gui.exe`：GUI 宿主入口（方案 B，自带渲染，不依赖终端）。

构建 EXE：

```powershell
.\\scripts\\build_exe.ps1
```

构建 EXE 并包含内置 Windows Terminal（增强包模式）：

```powershell
.\\scripts\\build_exe.ps1 -IncludeBundledWT
```

指定内置 WT 资产来源目录（目录下应包含 `WindowsTerminal.exe`）：

```powershell
.\\scripts\\build_exe.ps1 -IncludeBundledWT -BundledWTSource "vendor\\windows_terminal\\x64"
```

清理后构建：

```powershell
.\\scripts\\build_exe.ps1 -Clean
```

指定 Python 解释器：

```powershell
.\\scripts\\build_exe.ps1 -Python "C:\\Path\\To\\python.exe"
```

生成便携包（压缩）：

```powershell
.\\scripts\\build_portable.ps1
```

生成便携包并包含内置 Windows Terminal（增强包模式）：

```powershell
.\\scripts\\build_portable.ps1 -IncludeBundledWT
```

仅生成标准包（不含内置 WT，体积更小）：

```powershell
.\\scripts\\build_exe.ps1
.\\scripts\\build_portable.ps1
```

仅生成增强包（含内置 WT，开箱即用）：

```powershell
.\\scripts\\build_exe.ps1 -IncludeBundledWT
.\\scripts\\build_portable.ps1 -IncludeBundledWT
```

指定输入/输出：

```powershell
.\\scripts\\build_portable.ps1 -DistDir "dist\\DecoScreenBeautifier" -Output "dist\\DecoScreenBeautifier_portable.zip"
```

## 4. Windows Terminal（可选捆绑）验收脚本

在项目根目录执行：

```powershell
.\venv\Scripts\python.exe scripts/validate_wt_bundle.py
```

推荐同时验证 focus/fullscreen 两种副屏近似无框模式：

```powershell
.\venv\Scripts\python.exe scripts/validate_wt_bundle.py --with-smoke-run --mode focus --mode fullscreen
```

说明：
- 默认输出目录：`build/validation/wt_bundle/`
- 关键产物：
  - `wt_bundle_report.json`：汇总内置/系统 WT 可用性、回退路径、profile 初始化检查
  - `wt_bundle_smoke_focus_1080x480.txt` / `wt_bundle_smoke_focus_1920x480.txt`：focus 模式副屏场景启动烟测
  - `wt_bundle_smoke_fullscreen_1080x480.txt` / `wt_bundle_smoke_fullscreen_1920x480.txt`：fullscreen 模式副屏场景启动烟测
  - `portable_settings_snapshot.json`：便携 settings 快照（仅内置 WT 可用时生成）

## 5. Windows Terminal 增强包占位资源

- 默认像素着色器占位文件：`vendor/windows_terminal/shaders/deco_placeholder.hlsl`
- 当 `terminal_integration.bundled_wt_enable_pixel_shader=true` 时，启动器会把该路径写入 profile 的 `experimental.pixelShaderPath`。
- 生产发布时可替换为真实 CRT shader 文件，保持同路径即可无缝生效。

## 6. GUI 验收与性能基准（方案 B / 10.1 / 10.2）

在项目根目录执行：

```powershell
.\venv\Scripts\python.exe scripts/validate_gui_host.py --output-dir build/validation/gui_host
```

说明：
- 会自动生成运行时配置、启动 GUI、采样并退出。
- 产物目录默认在 `build/validation/gui_host/`，核心文件包括：
  - `report.json`：功能验收结果（PASS/FAIL + 各检查项）
  - `metrics.json`：退出时 GUI 指标快照（frame/component/window/effects）
  - `gui_perf.jsonl`：GUI 性能采样日志（fps/cpu/memory/frame_time）

性能基准（1080x480 + 1920x480）：

```powershell
.\venv\Scripts\python.exe scripts/benchmark_gui_host.py --output-dir build/validation/gui_host_perf --run-seconds 8
```

说明：
- 默认阈值为：平均 FPS >= 20，平均 CPU <= 85%。
- 输出 `benchmark_report.json`，包含每个分辨率场景的平均 FPS / CPU / 内存 / P95 帧耗时。
- 若环境缺少 Qt 运行时（如 `QtCore` DLL 加载失败），报告会标记 `qt_runtime_available=false`。

## 7. Qt 启动失败排查（`DLL load failed while importing QtCore`）

若双击 `DecoScreenBeautifier.exe` 弹出：`Qt runtime check failed: DLL load failed while importing QtCore`，请按以下顺序排查：

1) 确认安装并重启系统（必须重启一次）

```text
Microsoft Visual C++ Redistributable (2015-2022, x64)
https://aka.ms/vs/17/release/vc_redist.x64.exe
```

2) 使用最新打包产物（避免旧 EXE）

- 当前仓库默认产物：`dist/DecoScreenBeautifier.exe`
- 若你在其它目录有旧拷贝，请先删除旧版本后再测试。

3) 查看启动诊断日志

- 当 Qt 预检查失败时，程序会在项目根目录写入：`qt_runtime_error.log`
- 该文件包含：`sys._MEIPASS`、Qt DLL 搜索目录、PATH、完整 traceback。
- 请把该日志内容发给开发者，可快速定位是缺 DLL 还是版本冲突。

4) 推荐的临时绕过

- 先运行 `DecoScreenBeautifier_gui.exe` 验证是否仅终端宿主入口受影响。
- 若 GUI 可运行，通常是终端集成配置或 WT 资产路径问题。

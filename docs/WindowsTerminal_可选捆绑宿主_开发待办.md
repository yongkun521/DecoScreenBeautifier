# Windows Terminal 可选捆绑宿主：开发待办（2026-02-07）

> 决策结论：采用“Windows Terminal 作为可选捆绑宿主”方案，作为 Terminal 路线的主实现；GUI 宿主（方案 B）保持主入口与长期主线。

## 1. 目标与范围

### 1.1 总体目标
- [ ] 为没有高质量终端环境的用户提供“开箱即用”的复古终端显示体验。
- [ ] 不污染用户现有 Windows Terminal 配置（配置隔离）。
- [ ] 保留回退路径：内置 WT -> 系统 WT -> classic/GUI。

### 1.2 范围边界
- [x] 采用 WT 官方 Unpackaged（zip）+ Portable 模式思路。
- [ ] 不修改 Windows Terminal 源码，不做 WT 二次编译发行。
- [ ] 不承诺“真无边框壳”，以 `focus/fullscreen/maximized` 近似无框体验。
- [ ] `deco_terminal` 保持实验分支能力，不作为本阶段发布主路径。

## 2. 交付物清单

- [ ] `vendor/windows_terminal/`（或等价目录）打包资产与版本标识。
- [ ] 启动器“内置 WT 优先”逻辑与回退策略。
- [ ] 专用 WT 配置模板（含复古效果、字体、透明度、像素着色器占位）。
- [ ] 一键启动脚本（开发/打包场景均可用）。
- [ ] 文档：安装体积说明、兼容性说明、用户开关说明、故障排查说明。

## 3. 里程碑与待办

## M1：资产与目录约定（先落地）
- [x] 约定内置 WT 目录结构（x64 为主，预留 x86/arm64 扩展位）。
- [x] 明确版本文件（如 `wt_version.json`）用于后续升级对比。
- [x] 在构建脚本中增加“可选包含 WT 资产”参数（默认可关闭）。
- [x] 补齐第三方许可清单入口（至少引用 WT 仓库与许可证信息）。

## M2：启动链路改造（核心）
- [x] 启动器优先查找项目内置 `WindowsTerminal.exe`。
- [x] 内置缺失时回退系统 `wt.exe`（保持现有行为）。
- [x] 增加配置开关：
  - [x] `terminal_integration.prefer_bundled_wt`（默认 `true`）。
  - [x] `terminal_integration.bundled_wt_path`（默认空，自动推断）。
  - [x] `terminal_integration.use_wt_portable_mode`（默认 `true`）。
- [x] 明确 legacy 入口行为：不再重复拉起、失败弹窗可见、日志可追踪。

## M3：配置隔离与复古预设（体验）
- [x] 设计并落地专用 WT profile（例如 `DecoScreenBeautifier-CRT`）。
- [x] 默认启用复古关键项：
  - [x] `experimental.retroTerminalEffect`
  - [x] 可选 `experimental.pixelShaderPath`（提供默认占位 shader）
- [x] 内置模式下配置与状态目录写入应用目录（Portable 模式）。
- [x] 验证不影响用户既有 WT profiles / themes / keybindings。

## M4：发布与验收（可交付）
- [x] 打包产物分级：
  - [x] 标准包（不含 WT，体积小）
  - [x] 增强包（含 WT，开箱即用）
- [x] 增加启动自检：缺失 WT 资产时给出明确提示与回退说明。
- [x] 完成副屏场景体验验收（1080x480 / 1920x480，含 focus/fullscreen 对比）。
- [x] 形成“是否继续加码 WT 路线”的评审结论（继续/维持/收缩）。

## 4. 验收标准（DoD）

- [x] **可用性**：无系统 WT 的机器可直接通过内置 WT 启动。（已完成内置 `WindowsTerminal.exe` 实打包与启动链路验证）
- [x] **隔离性**：用户原有 WT `settings/profiles` 不被覆盖。（内置 WT 仅操作 Portable 目录）
- [ ] **稳定性**：连续启动 20 次，失败率为 0（同一环境）。
- [x] **可回退性**：内置 WT 缺失或异常时，自动退回系统 WT 或 classic。
- [x] **文档完整**：用户可按文档完成启用、切换、排障。

## 5. 风险与应对

- [ ] **体积上升**：增强包体积增加（约 +10~15MB 量级）
  - 应对：保留“标准包/增强包”双产物策略。
- [ ] **无边框能力有限**：WT 不是完全可控壳
  - 应对：将“真无边框”需求继续放在 GUI 宿主主线。
- [ ] **配置漂移**：WT 新版本配置字段可能变化
  - 应对：维护版本映射与最低可用配置模板。
- [ ] **发布合规**：第三方许可证与分发说明不足
  - 应对：在发布流程中加入许可证检查清单。

## 6. 开发顺序建议（两周节奏）

- [x] **第 1 周（能跑通）**：M1 + M2（内置优先 + 回退完整）。
- [x] **第 2 周（能发布）**：M3 + M4（复古预设 + 打包分级 + 验收文档）。

## 7. 与现有路线的关系

- [x] GUI 宿主（方案 B）继续作为默认入口与长期主线。
- [x] Windows Terminal 可选捆绑方案用于快速交付“终端复古观感”需求。
- [~] `deco_terminal` 维持实验性质，后续按价值评估是否继续投入。

## 8. 本文档对应任务入口

- [x] 代码实施入口：`src/utils/terminal_launcher.py`
- [x] 默认配置入口：`src/config/manager.py`
- [x] 集成说明文档：`docs/终端集成与无框方案.md`
- [x] 进度总览：`docs/TodoList.md`

## 9. M1 + M2 实施记录（2026-02-07）

- [x] 新增版本元信息：`vendor/windows_terminal/wt_version.json`
- [x] 新增许可证入口：`vendor/windows_terminal/licenses/README.md`
- [x] 构建脚本支持 `-IncludeBundledWT`：`scripts/build_exe.ps1`、`scripts/build_portable.ps1`
- [x] 启动器新增内置 WT 查找与可选 portable 标记：`src/utils/terminal_launcher.py`
- [x] 默认配置补齐三项 WT 相关开关：`src/config/manager.py`

## 10. M3 实施记录（2026-02-07）

- [x] 启动器在命中内置 WT 时自动初始化/更新专用 profile：`DecoScreenBeautifier-CRT`
- [x] profile 默认写入复古关键项：`experimental.retroTerminalEffect`
- [x] 增加可选像素着色器路径写入：`experimental.pixelShaderPath`（默认占位 shader：`vendor/windows_terminal/shaders/deco_placeholder.hlsl`）
- [x] Portable 模式下仅操作内置 WT 目录下 `settings/settings.json`，不写入系统 WT 用户配置目录
- [x] 默认配置补齐内置 WT profile 初始化参数：`src/config/manager.py`

## 11. M4 实施记录（2026-02-07）

- [x] 构建脚本支持“标准包/增强包”分级产物：`scripts/build_exe.ps1`、`scripts/build_portable.ps1`
- [x] 增加 WT 资产缺失时的启动自检与回退提示（含已检查路径与回退目标）：`src/utils/terminal_launcher.py`
- [x] 新增 WT 路线验收脚本：`scripts/validate_wt_bundle.py`
- [x] 完成副屏场景 smoke 验收（1080x480 / 1920x480，focus + fullscreen）：`build/validation/wt_bundle/wt_bundle_report.json`
- [x] 本轮评审结论：**继续**（内置 WT 资产实打包已完成，专用 profile 初始化与回退链路均验证通过）

## 12. PoC 实打包记录（2026-02-07）

- [x] 下载并落地内置 WT x64 资产：`vendor/windows_terminal/x64/WindowsTerminal.exe`
- [x] 增强包构建完成：`dist/DecoScreenBeautifier.exe`（终端宿主入口）+ `dist/DecoScreenBeautifier_gui.exe`（GUI 入口），均含 `dist/vendor/windows_terminal/x64`
- [x] 增强便携包构建完成：`build/DecoScreenBeautifier_portable_enhanced.zip`
- [x] PoC 验证完成：`build/validation/wt_bundle/wt_bundle_report.json` 显示 `bundled_wt.available=true`、`portable_profile.profile_found=true`、`route_assessment.recommendation=继续`

## 13. 入口纠偏记录（2026-02-07）

- [x] 修复打包入口语义：`DecoScreenBeautifier.exe` 统一为终端宿主入口（`src/main.py`），GUI 独立为 `DecoScreenBeautifier_gui.exe`（`src/main_gui.py`）
- [x] 修复冻结模式默认后端：当 `terminal_integration.force_bundled_wt_only=true`（默认）时，冻结版主入口强制走 `windows_terminal`（内置优先）
- [x] 进程级复核通过：启动 `dist/DecoScreenBeautifier.exe` 后检测到内置 `dist/vendor/windows_terminal/x64/WindowsTerminal.exe` 被拉起

## 14. 启动崩溃修复（2026-02-07）

- [x] 修复 `ModuleNotFoundError: No module named 'encodings'`：在 WT 拉起子进程前清理 PyInstaller 残留环境变量（`PYTHONHOME/PYTHONPATH/_PYI_*/PYI_*`）
- [x] 修复位置：`src/utils/terminal_launcher.py`（`_build_child_environment` + `subprocess.Popen(..., env=child_env)`）
- [x] 实测结果：内置 `WindowsTerminal.exe` 拉起后主程序可正常驻留，不再触发 embedded python interpreter 初始化失败

## 15. 灰屏与不可见错误提示修复（2026-02-08）

- [x] 修复 WT 宿主判定稳定性：`src/utils/terminal_launcher.py` 增强 `_in_windows_terminal`（新增 `DSB_WT_HOSTED` 哨兵变量 + 多级父进程链检测）以避免 onefile 场景误判导致的重复拉起。
- [x] 修复终端内“仅报错音效无可见提示”体验：`src/main.py` 在检测到终端宿主（`WT_SESSION/TERM_PROGRAM/DSB_WT_HOSTED`）时不再弹阻塞 MessageBox，改为 stderr 输出并持续写入 `legacy_terminal_error.log`。
- [x] 复测结果：增强包重打包通过（`scripts/build_exe.ps1 -IncludeBundledWT`），`scripts/validate_wt_bundle.py --with-smoke-run` 通过，评审结论维持“继续”。

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
构建 EXE：

```powershell
.\\scripts\\build_exe.ps1
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

指定输入/输出：

```powershell
.\\scripts\\build_portable.ps1 -DistDir "dist\\DecoScreenBeautifier" -Output "dist\\DecoScreenBeautifier_portable.zip"
```

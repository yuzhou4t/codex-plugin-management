---
name: storage-analyzer
description: 分析 macOS 或 Windows 的磁盘占用，定位大文件、缓存和残留，并在已有授权内定点清理。按需生成 HTML 报告；仅分析时保持只读，不默认启动删除服务。
---

# 存储分析与定点清理

按用户目标选择范围和交付形式。只问某个项目或目录时，从该位置的大小和已知大项开始；用户要整机分析时才运行完整扫描。不要把运行内存 RAM 问题自动转成磁盘清理。

## 分析

扫描保持只读，报告文件可写入任务输出目录。先核实系统和可用 Python，不假设 macOS 自带 Python。全盘扫描可用：

```bash
python3 scripts/scan.py > /tmp/storage_scan.json
```

按需读取 [macOS 布局](references/macos.md) 或 [Windows 布局](references/windows.md)。依据大小、归属、用途和再生能力区分可清理缓存、需选择的用户资料和不应直接删除的系统或共享组件。不可读目录说明遗漏，不把估算当作实测释放量。

问题能用短结论回答时直接回答。需要完整报告时，按 `scripts/build_report.py` 的 schema 准备分析数据并生成静态 HTML；大小字段用“约 14 GB”等可解析格式。可清理路径必须具体且已核实，不能仅凭名称把应用数据当缓存。

```bash
python3 scripts/build_report.py /tmp/storage_analysis.json /absolute/task/outputs/storage-report.html
```

## 清理

用户已经明确要求清理具体缓存或残留，且归属和影响清楚时直接按授权执行，无需逐项再问。泛泛的“腾空间”不授权删除未知文档、项目、聊天记录或离线资料；先分析，完成安全部分，只就这些资料的取舍询问。

需要网页交互清理且用户有此意图时，可启动：

```bash
python3 scripts/server.py /tmp/storage_analysis.json
```

该服务会提供真实删除能力；仅分析请求使用静态报告。保留服务原有的路径、token、Host 和点击确认保护，绿色项才允许直接删除，橙色项仅可移到废纸篓。授权由用户请求或实际点击提供，不再附加一轮聊天确认。

优先应用自身清理入口或可恢复的操作；移到废纸篓不等于空间已经释放。清理后检查目标、保留数据和实际空间变化。应用卸载按其安装方式处理，必要时使用 `uninstall-macos-tool`。

## 交付

报告主要占用、已完成操作、实际或估算的空间变化，以及仍需用户决定的具体项目。Windows 的回收站和扫描实现需要在当前机器验证，不沿用旧平台测试结论。

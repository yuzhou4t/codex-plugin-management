# 存储与 Git 定点检查表

## 安全命令

Windows：

```powershell
Get-PSDrive C,D
Get-ChildItem -LiteralPath <project> -Force
git -C <project> status --short
git -C <project> count-objects -vH
git -C <project> worktree list --porcelain
```

macOS / Linux：

```bash
df -h <project>
du -sh <project>/.data <project>/.tools <project>/artifacts 2>/dev/null
git -C <project> status --short
git -C <project> count-objects -vH
git -C <project> worktree list --porcelain
```

先列出顶层，再只统计已知大目录。优先使用 `rg` 查找构建、留存和 worktree 代码。

## 禁止模式

- `Get-ChildItem C:\ -Recurse`
- `Get-ChildItem D:\ -Recurse`
- `du /`、`find /` 或对主目录无界递归
- 未限定路径的重复哈希、压缩、复制或归档
- 在 `%LOCALAPPDATA%`、`~/.cache`、`/tmp` 中长期保存项目 worktree
- 以“临时”为名但没有退出清理的目录

只有用户明确要求整机存储分析，并接受性能影响时，才允许使用专用存储分析工具扫描更大范围。

## 架构与 Git 核对

- 根级和子级 `AGENTS.md` 是否一致；
- 当前 worktree 是否有用户修改；
- worktree 注册路径是否存在、是否在批准根目录；
- `.git` 大小是否真的异常；
- 大目录是 tracked、ignored 还是仓库外生成；
- 构建脚本是否复制共享依赖；
- 成功、失败、取消和重启后是否都能清理；
- 分支、tag、bundle、manifest 和活动安装版本是否能对应。

## 留存上限模板

| 数据类别 | 至少一种限制 |
| --- | --- |
| 原始/派生内容 | 有限天数 |
| 审计元数据 | 单条字节 + 总行数 |
| 日志 | 分片字节 + 总字节 + 天数 |
| 备份 | daily/weekly/monthly 最大代数 |
| worktree | 最大数量 + 干净自动清理 |
| 发布候选 | 最大数量，通常 2 |
| 展开构件/staging | 最大数量，通常 2 |
| SDK、模型、依赖 | 单一共享副本，不复制进候选 |

## 删除前核验

记录：

- 项目根和当前 HEAD；
- 活动版本与回滚版本；
- 每个目标的绝对路径、所属根、用途和大小；
- 是否为 Git worktree；
- 删除方式是否可恢复；
- 清理前可用空间。

删除后检查：

- 保留项仍存在；
- `git worktree list --porcelain` 无 stale/prunable；
- 存储预检通过；
- 项目服务或基础测试正常；
- 清理后的可用空间已记录。

# Skill 清单

核对日期：2026-08-13。当前仓库管理或明确排除 35 个用户级 Skill；Codex 的 `.system` 目录、空目录和插件缓存不计入统计。

## 跨平台自动安装（23）

| Skill | 来源 / 定位 |
| --- | --- |
| `ai-paper-scout` | 自维护；AI 论文检索与初筛 |
| `aihot` | 本地衍生版；当前 AI HOT 资讯查询 |
| `apply-personal-app-design-system` | 自维护；TTS、AI Recording 与后续个人软件的白蓝设计系统 |
| `discuss-confirm-write-obsidian` | 自维护；Obsidian 写入确认协议 |
| `git-finish` | 自维护；Git 任务收尾 |
| `github-precedent-scout` | 自维护；GitHub 开源先例侦察 |
| `gsap-core` | GSAP 官方快照 |
| `gsap-frameworks` | GSAP 官方快照 |
| `gsap-performance` | GSAP 官方快照 |
| `gsap-plugins` | GSAP 官方快照 |
| `gsap-react` | GSAP 官方快照 |
| `gsap-scrolltrigger` | GSAP 官方快照 |
| `gsap-timeline` | GSAP 官方快照 |
| `gsap-utils` | GSAP 官方快照 |
| `hv-analysis` | 本地衍生版；横纵分析工作流 |
| `ima-skill` | 已安装的 IMA OpenAPI Skill 快照 |
| `ltci-public-data-engineering` | 自维护；长护险公共数据工程 |
| `paper-terminology-translation-explanation` | 自维护；论文术语翻译与解释 |
| `project-docs-sync` | 自维护；项目文档同步与交接 |
| `project-orientation` | 自维护；打开、理解和安全启动项目 |
| `stabilize-local-agent-project` | 自维护；阻止无界扫描、Git/worktree 失控和磁盘留存膨胀 |
| `storage-analyzer` | Khazix 上游快照；macOS / Windows 存储分析 |
| `sync-skill-to-github` | 自维护；安全审查并将新建或下载的 Skill 同步到 GitHub |

## 仅由 macOS 自动安装（9）

这些 Skill 值得备份和同步，但目前依赖 `/Users/yuzhou4tc/...` 项目路径或 macOS 专属行为，所以 Windows 安装脚本不会自动部署。

| Skill | 依赖原因 |
| --- | --- |
| `ai-charging-station-daily` | 绑定本机 `AI充电站` 项目路径 |
| `architecture-weaver` | 绑定本机 Obsidian / HypoWeaver 路径 |
| `hft-article-production` | 依赖本机 HFT 工作流和配套 Skill |
| `hft-write` | 依赖本机 HFT 基准材料路径 |
| `journal-watch-paper-workflow` | 绑定本机 journal workshop 项目路径 |
| `obsidian-study-vault-workflow` | 绑定本机 Obsidian 仓库路径 |
| `paper-reading-10-step` | 绑定本机 Obsidian 阅读库路径 |
| `science-workshop-journal-tracking` | 绑定本机 journal workshop 项目路径 |
| `uninstall-macos-tool` | macOS 专属卸载流程 |

## 不进入仓库（3）

| Skill | 排除原因 |
| --- | --- |
| `debug-codex-lark-relay` | 飞书提醒 / relay 基础设施，按用户要求保持本机私有 |
| `ima-skill.backup-20260801-155403` | 过期备份，避免与当前 `ima-skill` 重复和误加载 |
| `hatch-pet` | Codex 当前系统托管的 curated Skill，不在私有仓库重复固定旧副本 |

## 自动安装规则

- macOS：安装 `skills/` 与 `skills-macos/`，共 32 个 Skill。
- Windows：只安装 `skills/`，共 23 个 Skill。
- 两个平台都会安装 `marketplace/` 中固定的 4 个插件。
- 安装脚本不会删除不属于本仓库的其他 Skill 或插件。

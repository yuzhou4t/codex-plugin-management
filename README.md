# Codex Skill 与插件管理

这个仓库用于在多台电脑之间同步自维护的 Codex Skill，以及经过固定版本整理的第三方 Skill / 插件快照。当前支持 macOS 和 Windows。

当前管理 37 个实际 Skill：34 个纳入同步，3 个明确排除。纳入同步的 34 个中，25 个可跨平台自动安装，9 个依赖本机项目路径或 macOS 能力。完整清单见 [`SKILL_INVENTORY.md`](SKILL_INVENTORY.md)。

## 仓库内容

- `skills/`：25 个跨平台 Skill。macOS 与 Windows 安装脚本都会安装。
- `skills-macos/`：9 个依赖 macOS 或这台 Mac 项目路径的 Skill。只由 macOS 安装脚本安装。
- `marketplace/`：名为 `plugin-management` 的本地 marketplace，当前包含 Build Web Apps、Test Android Apps、Zotero、HyperFrames 和 Token Usage Inspector。
- `profiles/`：经过脱敏的全局 Agent 工作规则和 Codex 偏好模板；不会覆盖机器上的完整配置。
- `skills/personal-frontend-builder/`：前端构建与提示词整理 Skill，Codex 和 AntiGravity 共用同一份源文件。
- `manifests/`：插件、外部 Skill 来源和经同步 Skill 的可审计清单。
- `archive/`：不再主动安装的历史 Skill 和插件。安装脚本不会处理这里的内容。
- `THIRD_PARTY_NOTICES.md`：第三方 Skill / 插件的来源、版本和许可证说明。

飞书提醒、Hook、后台 relay、账号配置和机器私有文件不属于这个仓库。

## macOS 安装

要求：已安装 ChatGPT/Codex，且 `codex` 命令可用，或使用 ChatGPT.app 自带的 Codex CLI。

```bash
git clone https://github.com/yuzhou4t/codex-plugin-management.git
cd codex-plugin-management
./scripts/install-macos.sh
```

如果 Codex CLI 位于其他位置：

```bash
PLUGIN_MANAGER_CODEX_BIN="/path/to/codex" ./scripts/install-macos.sh
```

## Windows 安装

要求：已安装 ChatGPT/Codex，并能在 PowerShell 中运行 `codex`。如果 CLI 不在 `PATH` 中，可以通过 `PLUGIN_MANAGER_CODEX_BIN` 指定 `codex.exe`。

```powershell
git clone https://github.com/yuzhou4t/codex-plugin-management.git
cd codex-plugin-management
powershell -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1
```

Windows 默认安装 `skills/` 中的 25 个跨平台 Skill，不安装 `skills-macos/`。后者仍保存在仓库中，迁移对应项目并修改其中的绝对路径后可以手动安装。

自定义 Codex CLI 路径：

```powershell
$env:PLUGIN_MANAGER_CODEX_BIN = "C:\path\to\codex.exe"
.\scripts\install-windows.ps1
```

## Matt Pocock Skills 官方版本

Matt Pocock Skills 直接从作者的 GitHub marketplace 安装，使用原版内容，不维护本地定制副本：

```bash
codex plugin marketplace add mattpocock/skills
codex plugin add mattpocock-skills@mattpocock
```

2026-10-14 已切换到官方主分支 `49dd158d1076134a641b33efb035946536778336`（上游版本号仍为 `1.3.1`），移除此前的本地包和旧 curated 安装；4 个技能中的中文命名与标题定制已撤销。官方说明见 [mattpocock/skills](https://github.com/mattpocock/skills)。

## AntiGravity 前端 Skill 互通

本机 AntiGravity 通过 `~/.gemini/config/skills/` 中的链接直接读取仓库源文件：自维护的 `personal-frontend-builder`，以及 Build Web Apps 插件的 `frontend-app-builder`。前者也供 Codex 使用；后者在 Codex 中由插件提供。修改仓库源文件后，AntiGravity 无需再维护另一份副本。GSAP 动效专题则链接到这台 Mac 已安装的 Codex `gsap` Skill，仅在项目使用 GSAP 时启用。

在另一台 Mac 克隆仓库并安装 Codex Skill 后，于仓库根目录执行以下命令建立 AntiGravity 链接（目标位置已有文件时命令会停止，不会覆盖）：

```bash
mkdir -p "$HOME/.gemini/config/skills"
ln -s "$PWD/skills/personal-frontend-builder" "$HOME/.gemini/config/skills/personal-frontend-builder"
ln -s "$PWD/marketplace/plugins/build-web-apps/skills/frontend-app-builder" "$HOME/.gemini/config/skills/frontend-app-builder"
```

这台 Mac 还把已安装的 Codex `gsap` Skill 链接给 AntiGravity；它依赖本机路径，不在上面的跨设备命令中。不要复制 Figma、Canva、Vercel 等依赖其插件工具的 Skill 当作通用指令。Mac 安装脚本会把新安装的 `personal-frontend-builder` 链接到仓库，重跑时保留链接；Windows 安装脚本仍复制 Skill 文件。

## 更新

在任意电脑上拉取仓库后重新运行对应安装脚本：

```bash
git pull --ff-only
```

脚本只会安装或更新本仓库管理的 Skill 和插件，不会删除其他 marketplace、插件或 Skill。它不会同步 API Key、账号配置或项目数据；这些应在每台设备上单独配置。

## 可移植配置检查

`profiles/global-AGENTS.md` 保存跨 Agent 通用的工作规则，`profiles/codex-portable.toml` 只保存无密钥、无路径的 Codex 偏好。它们是供人工审阅和合并的模板，不会覆盖现有的 `~/.codex/AGENTS.md` 或 `config.toml`。

拉取仓库后可以运行只读检查：

```bash
python3 scripts/doctor.py
```

检查器只比较 Skill、插件和模板状态，不输出配置值，也不会修改本机。使用 `--strict` 可以让缺项返回非零状态；使用 `--skip-plugins` 可以避免调用 Codex CLI。

## Skill 自动同步到 GitHub

同步范围以可复用的通用 Skill 为主。本机专用、个人教学或绑定私有项目与数据的 Skill 默认仅保留在本机，不要求上传，也不以本机安装目录与仓库完全一致为目标。已有 `skills-macos/` 条目按现有清单保留；后续新增或更新仍需单独判断是否适合上传。

`sync-skill-to-github` 用于在新建或修改自维护 Skill 后完成敏感信息扫描、复制、校验、定点提交和推送。飞书、Agently 等第三方 Skill 不复制到本仓库，只把官方 well-known 或 GitHub 下载链接登记到 `manifests/external-skills.json`，让新 Agent 直接从上游安装。凭据、运行状态及未确认的本机路径会阻止上传。

## Token 使用量查询

marketplace 中的 `token-usage-inspector` 插件读取 Codex 本机现存及归档的 `rollout-*.jsonl`：新版日志使用原生 `token_usage_record`，旧版日志从累计 `token_count` 快照计算增量并排除子任务继承回放。它既能查看单个任务的轮次和调用，也能按项目、全部历史任务、日期、模型、任务和来源汇总，支持 CSV/JSON 导出与实时刷新；默认不显示提示词，也不会上传会话日志。

Windows 上使用 `--timezone Asia/Shanghai` 等显式 IANA 时区前，需为运行脚本的同一 Python 环境安装时区数据；在仓库根目录执行：

```powershell
python -m pip install -r marketplace/plugins/token-usage-inspector/skills/token-usage-inspector/scripts/requirements.txt
```

## 安全边界

- 不提交 API Key、访问令牌、飞书目标 ID、账号配置或本机缓存。
- 飞书提醒、Hook、后台 relay 及其测试文件通过 `.gitignore` 保持为本机私有内容。
- `marketplace/` 中的第三方内容是固定快照；更新前应核对上游版本、许可证和变更。
- `skills-macos/` 中可能含这台 Mac 的绝对项目路径，不应在 Windows 上直接自动安装。
- `archive/` 仅用于历史恢复，不会自动部署。

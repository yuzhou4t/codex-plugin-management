# Codex Skill 与插件管理

这个私有仓库用于在多台电脑之间同步自维护的 Codex Skill，以及经过固定版本整理的第三方 Skill / 插件快照。当前支持 macOS 和 Windows。

当前管理 33 个实际 Skill：30 个纳入同步，3 个明确排除。纳入同步的 30 个中，21 个可跨平台自动安装，9 个依赖本机项目路径或 macOS 能力。完整清单见 [`SKILL_INVENTORY.md`](SKILL_INVENTORY.md)。

## 仓库内容

- `skills/`：21 个跨平台 Skill。macOS 与 Windows 安装脚本都会安装。
- `skills-macos/`：9 个依赖 macOS 或这台 Mac 项目路径的 Skill。只由 macOS 安装脚本安装。
- `marketplace/`：名为 `plugin-management` 的本地 marketplace，当前包含 Build Web Apps、Test Android Apps、Zotero 和 HyperFrames。
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

Windows 默认安装 `skills/` 中的 21 个跨平台 Skill，不安装 `skills-macos/`。后者仍保存在仓库中，迁移对应项目并修改其中的绝对路径后可以手动安装。

自定义 Codex CLI 路径：

```powershell
$env:PLUGIN_MANAGER_CODEX_BIN = "C:\path\to\codex.exe"
.\scripts\install-windows.ps1
```

## 更新

在任意电脑上拉取仓库后重新运行对应安装脚本：

```bash
git pull --ff-only
```

脚本只会安装或更新本仓库管理的 Skill 和插件，不会删除其他 marketplace、插件或 Skill。它不会同步 API Key、账号配置或项目数据；这些应在每台设备上单独配置。

## 安全边界

- 不提交 API Key、访问令牌、飞书目标 ID、账号配置或本机缓存。
- 飞书提醒、Hook、后台 relay 及其测试文件通过 `.gitignore` 保持为本机私有内容。
- `marketplace/` 中的第三方内容是固定快照；更新前应核对上游版本、许可证和变更。
- `skills-macos/` 中可能含这台 Mac 的绝对项目路径，不应在 Windows 上直接自动安装。
- `archive/` 仅用于历史恢复，不会自动部署。

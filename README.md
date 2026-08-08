# Codex Skill 与插件管理

这个仓库用于在多台电脑之间同步自维护的 Codex Skill，以及经过固定版本整理的第三方插件快照。当前支持 macOS 和 Windows。

## 仓库内容

- `skills/`：自维护 Skill。安装脚本会把每个包含 `SKILL.md` 的目录同步到用户级 Codex Skill 目录。
- `marketplace/`：名为 `plugin-management` 的本地 marketplace，当前包含 Build Web Apps、Test Android Apps、Zotero 和 HyperFrames。
- `archive/`：不再主动安装的历史 Skill 和插件。安装脚本不会处理这里的内容。
- `THIRD_PARTY_NOTICES.md`：第三方插件的来源、版本和许可证说明。

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

自定义 Codex CLI 路径：

```powershell
$env:PLUGIN_MANAGER_CODEX_BIN = "C:\path\to\codex.exe"
.\scripts\install-windows.ps1
```

## 更新

在任意电脑上拉取仓库后重新运行对应安装脚本：

```bash
git pull
```

脚本只会安装或更新本仓库管理的 Skill 和插件，不会删除其他 marketplace、插件或 Skill。

## 安全边界

- 不提交 API Key、访问令牌、飞书目标 ID、账号配置或本机缓存。
- `marketplace/` 中的第三方内容是固定快照；更新前应核对上游版本、许可证和变更。
- `archive/` 仅用于历史恢复，不会自动部署。

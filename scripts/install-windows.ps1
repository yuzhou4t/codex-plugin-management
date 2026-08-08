$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$MarketplaceDir = Join-Path $RepoRoot "marketplace"
$SkillsSourceDir = Join-Path $RepoRoot "skills"
$CodexSkillsDir = Join-Path $env:USERPROFILE ".codex\skills"
$Plugins = @("build-web-apps", "test-android-apps", "zotero", "hyperframes")

function Find-CodexCli {
    if ($env:PLUGIN_MANAGER_CODEX_BIN) {
        return $env:PLUGIN_MANAGER_CODEX_BIN
    }

    $command = Get-Command codex -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\ChatGPT\resources\codex.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\ChatGPT\Resources\codex.exe"),
        (Join-Path $env:ProgramFiles "ChatGPT\resources\codex.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }

    throw "Codex CLI not found. Install Codex, add codex to PATH, or set PLUGIN_MANAGER_CODEX_BIN."
}

$CodexCli = Find-CodexCli
if (-not (Test-Path -LiteralPath $CodexCli -PathType Leaf)) {
    throw "Codex CLI does not exist: $CodexCli"
}

New-Item -ItemType Directory -Path $CodexSkillsDir -Force | Out-Null
Get-ChildItem -LiteralPath $SkillsSourceDir -Directory | ForEach-Object {
    $skillFile = Join-Path $_.FullName "SKILL.md"
    if (Test-Path -LiteralPath $skillFile -PathType Leaf) {
        $targetDir = Join-Path $CodexSkillsDir $_.Name
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        Copy-Item -Path (Join-Path $_.FullName "*") -Destination $targetDir -Recurse -Force
        Write-Host "Installed Skill: $($_.Name)"
    }
}

& $CodexCli plugin marketplace add $MarketplaceDir --json
if ($LASTEXITCODE -ne 0) {
    throw "Failed to add the plugin-management marketplace."
}

foreach ($plugin in $Plugins) {
    & $CodexCli plugin add "$plugin@plugin-management" --json
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install plugin: $plugin"
    }
}

Write-Host "Codex Skills and plugins installed from $RepoRoot"

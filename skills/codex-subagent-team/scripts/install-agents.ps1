[CmdletBinding()]
param(
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" })
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SkillDir = Split-Path -Parent $PSScriptRoot
$SourceDir = Join-Path $SkillDir "assets\agents"
$TargetDir = Join-Path $CodexHome "agents"

if (-not (Test-Path -LiteralPath $SourceDir -PathType Container)) {
    throw "Agent profile source directory is missing: $SourceDir"
}

$Profiles = @(Get-ChildItem -LiteralPath $SourceDir -File -Filter "*.toml" | Sort-Object Name)
if ($Profiles.Count -ne 4) {
    throw "Expected 4 managed Subagent profiles, found $($Profiles.Count)"
}

New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
foreach ($Profile in $Profiles) {
    $TargetPath = Join-Path $TargetDir $Profile.Name
    $Changed = $true
    if (Test-Path -LiteralPath $TargetPath -PathType Leaf) {
        $SourceHash = (Get-FileHash -LiteralPath $Profile.FullName -Algorithm SHA256).Hash
        $TargetHash = (Get-FileHash -LiteralPath $TargetPath -Algorithm SHA256).Hash
        $Changed = $SourceHash -ne $TargetHash
    }

    if ($Changed) {
        Copy-Item -LiteralPath $Profile.FullName -Destination $TargetPath -Force
        Write-Host "Installed Subagent: $($Profile.BaseName)"
    }
    else {
        Write-Host "Unchanged Subagent: $($Profile.BaseName)"
    }

    $InstalledHash = (Get-FileHash -LiteralPath $TargetPath -Algorithm SHA256).Hash
    $ExpectedHash = (Get-FileHash -LiteralPath $Profile.FullName -Algorithm SHA256).Hash
    if ($InstalledHash -ne $ExpectedHash) {
        throw "Subagent verification failed: $($Profile.Name)"
    }
}

Write-Host "Installed $($Profiles.Count) managed Subagents in $TargetDir"

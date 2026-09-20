[CmdletBinding()]
param(
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" })
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SkillDir = Split-Path -Parent $PSScriptRoot
$SourceDir = Join-Path $SkillDir "assets\agents"
$TargetDir = Join-Path $CodexHome "agents"
$ConfigPath = Join-Path $CodexHome "config.toml"
$BeginMarker = "# BEGIN codex-subagent-team managed roles"
$EndMarker = "# END codex-subagent-team managed roles"

if (-not (Test-Path -LiteralPath $SourceDir -PathType Container)) {
    throw "Agent profile source directory is missing: $SourceDir"
}

$Profiles = @(Get-ChildItem -LiteralPath $SourceDir -File -Filter "*.toml" | Sort-Object Name)
if ($Profiles.Count -ne 4) {
    throw "Expected 4 managed Subagent profiles, found $($Profiles.Count)"
}

$ConfigText = if (Test-Path -LiteralPath $ConfigPath -PathType Leaf) {
    [IO.File]::ReadAllText($ConfigPath)
} else { "" }
$BeginCount = ([regex]::Matches($ConfigText, "(?m)^$([regex]::Escape($BeginMarker))$")).Count
$EndCount = ([regex]::Matches($ConfigText, "(?m)^$([regex]::Escape($EndMarker))$")).Count
if ($BeginCount -ne $EndCount -or $BeginCount -gt 1) {
    throw "Managed Subagent config markers are incomplete or duplicated: $ConfigPath"
}
$ManagedPattern = "(?ms)^$([regex]::Escape($BeginMarker))\r?\n.*?^$([regex]::Escape($EndMarker))(?:\r?\n)?"
$UnmanagedConfig = if ($BeginCount -eq 1) { [regex]::Replace($ConfigText, $ManagedPattern, "") } else { $ConfigText }
if ($UnmanagedConfig -match '(?m)^\s*\[agents\.(sol_executor|terra_executor|terra_reviewer|luna_patcher)\]\s*(?:#.*)?$') {
    throw "A managed Subagent role already exists outside the managed block: $ConfigPath"
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

$ManagedBlockLines = [Collections.Generic.List[string]]::new()
$ManagedBlockLines.Add($BeginMarker)
foreach ($Profile in $Profiles) {
    $TargetPath = Join-Path $TargetDir $Profile.Name
    $EscapedTarget = $TargetPath.Replace('\', '\\').Replace('"', '\"')
    $ManagedBlockLines.Add("[agents.$($Profile.BaseName)]")
    $ManagedBlockLines.Add("config_file = `"$EscapedTarget`"")
    $ManagedBlockLines.Add("")
}
$ManagedBlockLines.Add($EndMarker)
$ConfigPrefix = $UnmanagedConfig.TrimEnd([char[]]"`r`n")
$NewConfig = if ([string]::IsNullOrEmpty($ConfigPrefix)) {
    ($ManagedBlockLines -join "`n") + "`n"
} else {
    $ConfigPrefix + "`n`n" + ($ManagedBlockLines -join "`n") + "`n"
}
$ConfigTemp = "$ConfigPath.codex-subagent-team.tmp"
try {
    [IO.File]::WriteAllText($ConfigTemp, $NewConfig, [Text.UTF8Encoding]::new($false))
    if (Test-Path -LiteralPath $ConfigPath -PathType Leaf) {
        [IO.File]::Replace($ConfigTemp, $ConfigPath, $null)
    } else {
        Move-Item -LiteralPath $ConfigTemp -Destination $ConfigPath
    }
} finally {
    if (Test-Path -LiteralPath $ConfigTemp) { Remove-Item -LiteralPath $ConfigTemp -Force }
}

Write-Host "Installed $($Profiles.Count) managed Subagents in $TargetDir and registered them in $ConfigPath"

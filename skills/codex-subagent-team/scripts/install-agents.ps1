[CmdletBinding()]
param(
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }),
    [string]$PythonExecutable = $(if (Get-Command python3 -ErrorAction SilentlyContinue) { (Get-Command python3).Source } elseif (Get-Command python -ErrorAction SilentlyContinue) { (Get-Command python).Source } else { "" })
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($PythonExecutable)) {
    throw "Python 3.11 or newer is required to validate Codex config.toml safely."
}

$Installer = Join-Path $PSScriptRoot "install_agents.py"
& $PythonExecutable $Installer --codex-home $CodexHome
if ($LASTEXITCODE -ne 0) {
    throw "Managed Subagent installation failed with exit code $LASTEXITCODE."
}

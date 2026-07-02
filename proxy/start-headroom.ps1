# MewVault Headroom Proxy — Windows startup script
# Usage: & .\start-headroom.ps1
# Requires: pip install "headroom-ai[proxy,mcp]"
# After starting, launch Claude Code with:
#   $env:ANTHROPIC_BASE_URL="http://localhost:8787"; claude

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VaultRoot = Split-Path -Parent $ScriptDir
$SecretsFile = Join-Path $VaultRoot "secrets\workspace.env"

if (-not (Get-Command headroom -ErrorAction SilentlyContinue)) {
    Write-Error "headroom not found. Run: pip install 'headroom-ai[proxy,mcp]'"
    exit 1
}

if (Test-Path $SecretsFile) {
    Get-Content $SecretsFile | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]*)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

Write-Host "Starting Headroom compression proxy on http://localhost:8787 ..."
Write-Host "  Then launch Claude Code with:"
Write-Host "  `$env:ANTHROPIC_BASE_URL='http://localhost:8787'; claude"
Write-Host ""

headroom proxy `
  --port 8787 `
  --protect-tool-results "Bash,Read,Edit,Write,MultiEdit" `
  --no-telemetry

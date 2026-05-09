# MewVault LiteLLM Proxy — Windows startup script
# Usage: & .\start-proxy.ps1
# Requires: pip install litellm[proxy]

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = Join-Path $ScriptDir "litellm-config.yaml"

if (-not (Test-Path $ConfigFile)) {
    Write-Error "litellm-config.yaml not found at $ConfigFile"
    exit 1
}

if (-not (Get-Command litellm -ErrorAction SilentlyContinue)) {
    Write-Error "litellm not found. Run: pip install 'litellm[proxy]'"
    exit 1
}

Write-Host "Starting MewVault LiteLLM proxy on http://localhost:4000 ..."
litellm --config $ConfigFile

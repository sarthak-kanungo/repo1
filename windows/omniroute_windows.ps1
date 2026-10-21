# OmniRoute on Windows
# Installs Node.js (if needed) and OmniRoute, starts the server and opens the dashboard.
#
# Run (PowerShell):
#   powershell -ExecutionPolicy Bypass -File .\omniroute_windows.ps1
# Also add OmniRoute to Claude Desktop as an MCP server:
#   powershell -ExecutionPolicy Bypass -File .\omniroute_windows.ps1 -ClaudeDesktop -ApiKey "<your OmniRoute API key>"

param(
    [switch]$ClaudeDesktop,
    [string]$ApiKey = "",
    [int]$Port = 20128
)

$ErrorActionPreference = "Stop"

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}

function Get-NodeVersion {
    try { return [version]((node -v).TrimStart("v")) } catch { return $null }
}

# 1. Node.js: OmniRoute needs 22.22.2+ or 24+
Step "Checking Node.js"
$node = Get-NodeVersion
$nodeOk = $node -and (($node.Major -eq 22 -and $node -ge [version]"22.22.2") -or $node.Major -ge 24)

if (-not $nodeOk) {
    if ($node) { Write-Host "Node $node is too old." } else { Write-Host "Node.js not found." }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "winget is not available. Install Node.js 24 LTS from https://nodejs.org and run this script again." -ForegroundColor Red
        exit 1
    }
    Write-Host "Installing Node.js LTS with winget..."
    winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements
    Refresh-Path
    $node = Get-NodeVersion
    if (-not $node) {
        Write-Host "Node.js installed, but this window can't see it yet. Close PowerShell, open a new one and run the script again." -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "Node $(node -v), npm $(npm -v)"

# 2. OmniRoute
Step "Installing OmniRoute (takes a few minutes)"
npm install -g omniroute --loglevel=error
if ($LASTEXITCODE -ne 0) { Write-Host "npm install failed." -ForegroundColor Red; exit 1 }
Refresh-Path
omniroute --version

# 3. Start the server in its own window (close that window to stop it)
Step "Starting OmniRoute"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "title OmniRoute && omniroute serve"

$url = "http://localhost:$Port"
$up = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 | Out-Null
        $up = $true; break
    } catch {
        # 401/redirect still means the server answered
        if ($_.Exception.Response) { $up = $true; break }
        Start-Sleep -Seconds 2
    }
}
if (-not $up) {
    Write-Host "Server did not answer on $url. Check the 'OmniRoute' window for errors." -ForegroundColor Red
    exit 1
}
Write-Host "OmniRoute is running." -ForegroundColor Green
Write-Host "  Dashboard: $url"
Write-Host "  API base:  $url/v1"
Start-Process $url

# Dashboard password lives in INITIAL_PASSWORD in OmniRoute's .env
$envFile = Join-Path $env:USERPROFILE ".omniroute\.env"
if (Test-Path $envFile) {
    Write-Host "  Login password: INITIAL_PASSWORD in $envFile (change it after logging in)"
}
Write-Host "  API key: Dashboard -> Endpoints"

# 4. Optional: register OmniRoute as an MCP server in Claude Desktop
if ($ClaudeDesktop) {
    Step "Adding OmniRoute to Claude Desktop"
    if (-not $ApiKey) {
        $ApiKey = Read-Host "Paste your OmniRoute API key (Dashboard -> Endpoints)"
    }
    $cfgDir = Join-Path $env:APPDATA "Claude"
    $cfgPath = Join-Path $cfgDir "claude_desktop_config.json"
    New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null

    if (Test-Path $cfgPath) {
        Copy-Item $cfgPath "$cfgPath.bak" -Force
        $raw = Get-Content $cfgPath -Raw
        $cfg = if ($raw.Trim()) { $raw | ConvertFrom-Json } else { [pscustomobject]@{} }
    } else {
        $cfg = [pscustomobject]@{}
    }
    if (-not $cfg.PSObject.Properties["mcpServers"]) {
        $cfg | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{})
    }

    $server = [pscustomobject]@{
        command = "npx"
        args    = @("-y", "mcp-remote", "$url/api/mcp/stream", "--header", 'Authorization:${OMNIROUTE_AUTH}')
        env     = [pscustomobject]@{ OMNIROUTE_AUTH = "Bearer $ApiKey" }
    }
    $cfg.mcpServers | Add-Member -NotePropertyName omniroute -NotePropertyValue $server -Force

    # Write UTF-8 without BOM so Claude Desktop can parse it
    $json = $cfg | ConvertTo-Json -Depth 20
    [IO.File]::WriteAllText($cfgPath, $json, (New-Object Text.UTF8Encoding $false))
    Write-Host "Updated $cfgPath (backup: $cfgPath.bak)" -ForegroundColor Green
    Write-Host "Quit Claude Desktop completely (tray icon -> Quit) and open it again."
}

Write-Host "`nDone. To stop OmniRoute, close the 'OmniRoute' window or run: omniroute stop"

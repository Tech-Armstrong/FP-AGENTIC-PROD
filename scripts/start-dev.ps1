# Start the full local stack: LangGraph agent (:8000), Airtable API (:8001), Next.js (:3000).
# Usage:  .\scripts\start-dev.ps1
#         .\scripts\start-dev.ps1 -SkipInstall

param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

if (-not (Test-Path ".env")) {
    Write-Warning ".env not found. Copy .env.example to .env and add your API keys."
}

$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$venvPip = Join-Path $RepoRoot ".venv\Scripts\pip.exe"

if (-not $SkipInstall) {
    if (-not (Test-Path $venvPython)) {
        Write-Step "Creating Python virtual environment (.venv)"
        python -m venv .venv
    }

    Write-Step "Installing Python dependencies (backend + agent)"
    & $venvPip install -r requirements.txt
    & $venvPip install -r agent\requirements.txt

    if (-not (Test-Path "node_modules")) {
        Write-Step "Installing npm dependencies"
        npm install
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment missing at .venv. Run without -SkipInstall first."
}

$processes = @()

if (-not (Get-Command pwsh -ErrorAction SilentlyContinue) -and -not (Get-Command powershell -ErrorAction SilentlyContinue)) {
    throw "PowerShell (pwsh or powershell) is required to start service windows."
}

function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command
    )
    $shell = if (Get-Command pwsh -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell" }
    $argList = @(
        "-NoExit",
        "-Command",
        "`$Host.UI.RawUI.WindowTitle = '$Title'; Set-Location '$WorkingDirectory'; $Command"
    )
    return Start-Process -FilePath $shell -ArgumentList $argList -PassThru -WorkingDirectory $RepoRoot
}

Write-Step "Starting LangGraph agent on http://localhost:8000"
$processes += Start-ServiceWindow -Title "Agent :8000" -WorkingDirectory (Join-Path $RepoRoot "agent") -Command "& '$venvPython' main.py"

Write-Step "Starting Airtable API on http://localhost:8001"
$processes += Start-ServiceWindow -Title "Backend :8001" -WorkingDirectory $RepoRoot -Command "& '$venvPython' backend\airtable_main.py"

Write-Step "Starting Next.js on http://localhost:3000"
$processes += Start-ServiceWindow -Title "Next.js :3000" -WorkingDirectory $RepoRoot -Command "npm run dev"

Write-Host ""
Write-Host "All services are starting in separate terminal windows." -ForegroundColor Green
Write-Host "  App:     http://localhost:3000"
Write-Host "  Agent:   http://localhost:8000/copilotkit/health"
Write-Host "  Backend: http://localhost:8001/health"
Write-Host ""
Write-Host "Press Enter here to stop all services and close their windows."
Read-Host | Out-Null

Write-Step "Stopping services"
foreach ($proc in $processes) {
    if ($proc -and -not $proc.HasExited) {
        & taskkill /PID $proc.Id /T /F 2>$null | Out-Null
    }
}

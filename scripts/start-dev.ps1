# Start the full local stack: OCR service (:8010), LangGraph agent (:8000),
# Airtable API (:8001), Next.js (:3000).
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

function Get-SystemPython {
    $resolved = node (Join-Path $PSScriptRoot "resolvePython.mjs")
    if ($LASTEXITCODE -ne 0) {
        throw $resolved
    }
    return $resolved.Trim()
}

function Test-VenvPythonVersion {
    if (-not (Test-Path $venvPython)) {
        return
    }
    & $venvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $version = & $venvPython --version 2>&1
        throw ".venv uses $version but Python 3.10+ is required. Remove-Item -Recurse -Force .venv and re-run."
    }
}

function Ensure-Venv {
    $systemPython = Get-SystemPython
    if (-not (Test-Path $venvPython)) {
        Write-Step "Creating Python virtual environment (.venv) with $(& $systemPython --version 2>&1)"
        if ($systemPython -match " ") {
            $parts = $systemPython -split " ", 2
            & $parts[0] $parts[1] -m venv .venv
        } else {
            & $systemPython -m venv .venv
        }
    } else {
        Test-VenvPythonVersion
    }
    $pipCheck = & $venvPython -m pip --version 2>$null
    if (-not $pipCheck) {
        Write-Step "Bootstrapping pip in .venv (incomplete venv detected)"
        & $venvPython -m ensurepip --upgrade
    }
}

if (-not $SkipInstall) {
    Ensure-Venv

    Write-Step "Upgrading pip in .venv"
    & $venvPython -m pip install --upgrade pip

    Write-Step "Installing Python dependencies (backend-airtable + agent + OCR service)"
    & $venvPython -m pip install -r requirements.txt

    if (-not (Test-Path "node_modules")) {
        Write-Step "Installing npm dependencies"
        npm install
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment missing at .venv. Run without -SkipInstall first."
}

Test-VenvPythonVersion

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

Write-Step "Starting OCR policy service on http://localhost:8010"
$processes += Start-ServiceWindow -Title "OCR :8010" -WorkingDirectory (Join-Path $RepoRoot "ocr-service") -Command "& '$venvPython' main.py"

Write-Step "Starting LangGraph agent on http://localhost:8000"
$processes += Start-ServiceWindow -Title "Agent :8000" -WorkingDirectory (Join-Path $RepoRoot "agent") -Command "& '$venvPython' main.py"

Write-Step "Starting Airtable API on http://localhost:8001"
$processes += Start-ServiceWindow -Title "Backend :8001" -WorkingDirectory (Join-Path $RepoRoot "backend-airtable") -Command "& '$venvPython' main.py"

Write-Step "Starting Next.js on http://localhost:3000"
$processes += Start-ServiceWindow -Title "Next.js :3000" -WorkingDirectory $RepoRoot -Command "npm run dev"

Write-Host ""
Write-Host "All services are starting in separate terminal windows." -ForegroundColor Green
Write-Host "  App:     http://localhost:3000"
Write-Host "  OCR:     http://localhost:8010/health"
Write-Host "  Agent:   http://localhost:8000/copilotkit/health"
Write-Host "  Backend: http://localhost:8001/health"
Write-Host ""
Write-Host "Chat policy uploads need OCR_SERVICE_URL=http://localhost:8010 in .env"
Write-Host "(and Azure DI keys in ocr-service/.env for real PDF summarization)."
Write-Host ""
Write-Host "Press Enter here to stop all services and close their windows."
Read-Host | Out-Null

Write-Step "Stopping services"
foreach ($proc in $processes) {
    if ($proc -and -not $proc.HasExited) {
        & taskkill /PID $proc.Id /T /F 2>$null | Out-Null
    }
}

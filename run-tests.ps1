param(
    [switch]$NoInstall
)

Write-Host "Running tests with coverage..." -ForegroundColor Cyan

if (-not $NoInstall) {
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
    }
    if (Test-Path "requirements-dev.txt") {
        pip install -r requirements-dev.txt
    }
}

pytest

if (Test-Path "coverage.xml") {
    Write-Host "Coverage report generated at coverage.xml" -ForegroundColor Green
}
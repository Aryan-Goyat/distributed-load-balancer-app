# Setup git hooks for Windows PowerShell
Write-Host "Configuring git hooks directory..." -ForegroundColor Cyan
git config core.hooksPath .githooks
Write-Host "Git hooks enabled! Pre-push test verification is now active." -ForegroundColor Green

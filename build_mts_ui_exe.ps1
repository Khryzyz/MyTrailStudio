$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "Building My Trail Studio UI executable..."

python -m pip show pyinstaller *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..."
    python -m pip install pyinstaller
}

$pyInstallerArgs = @(
    "--noconfirm",
    "--windowed",
    "--name", "MyTrailStudio",
    "--add-data", "scripts;scripts",
    "--add-data", "resources\assets;resources\assets",
    "--add-data", "resources\font;resources\font",
    "--hidden-import", "PySide6.QtSvg"
)

$iconPath = Join-Path $Root "resources\assets\iso.ico"
if (Test-Path $iconPath) {
    $pyInstallerArgs += @("--icon", $iconPath)
}

$pyInstallerArgs += "ui_app\__main__.py"

python -m PyInstaller @pyInstallerArgs

Write-Host ""
Write-Host "Executable generated at:"
Write-Host "$Root\dist\MyTrailStudio\MyTrailStudio.exe"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

$InputDir = Join-Path $Root "input"
$OutputDir = Join-Path $Root "output"
$ScriptsDir = Join-Path $Root "scripts"
$ResourcesDir = Join-Path $Root "resources"
$TempDir = Join-Path $Root "temp"
$ConfigPath = Join-Path $InputDir "config.json"

Write-Host ""
Write-Host "====================================="
Write-Host " DJI / GPX Overlay Pipeline"
Write-Host "====================================="
Write-Host ""

Write-Host "Ruta del proyecto: $Root"
Write-Host "Config: $ConfigPath"
Write-Host ""

$requiredFolders = @(
    $InputDir,
    $OutputDir,
    "$OutputDir\frames",
    "$OutputDir\previews",
    "$OutputDir\final",
    "$OutputDir\data",
    $ScriptsDir,
    $ResourcesDir,
    "$ResourcesDir\font",
    $TempDir
)

foreach ($folder in $requiredFolders) {
    if (!(Test-Path $folder)) {
        Write-Host "FALTA carpeta: $folder" -ForegroundColor Red
        exit 1
    }
}

if (!(Test-Path $ConfigPath)) {
    Write-Host "FALTA config.json en input" -ForegroundColor Red
    exit 1
}

Write-Host "Carpetas OK" -ForegroundColor Green

try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python OK: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python no encontrado" -ForegroundColor Red
    exit 1
}

try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "FFmpeg OK: $ffmpegVersion" -ForegroundColor Green
} catch {
    Write-Host "FFmpeg no encontrado" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Ejecutando validacion tecnica..."
Write-Host ""

$validator = Join-Path $ScriptsDir "pipeline_validate.py"

python $validator --root $Root @args

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "La validacion fallo." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Validacion completada correctamente." -ForegroundColor Green

$manifestPath = Join-Path $OutputDir "data\manifest.json"
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

if ($manifest.config.output.preview.add -eq $true) {
    Write-Host "Modo preview activado."
    $previewScript = Join-Path $ScriptsDir "pipeline_preview.py"
    python $previewScript --root $Root

    if ($LASTEXITCODE -ne 0) {
        Write-Host "La generacion del preview fallo." -ForegroundColor Red
        exit $LASTEXITCODE
    }
} else {
    Write-Host "Modo render final activado."
    $renderScript = Join-Path $ScriptsDir "pipeline_render.py"
    python $renderScript --root $Root

    if ($LASTEXITCODE -ne 0) {
        Write-Host "La generacion del render final fallo." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}



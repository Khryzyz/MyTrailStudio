$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

$InputDir = Join-Path $Root "input"
$OutputDir = Join-Path $Root "output"
$ScriptsDir = Join-Path $Root "scripts"
$ResourcesDir = Join-Path $Root "resources"
$TempDir = Join-Path $Root "temp"
$ConfigPath = Join-Path $InputDir "pipeline_config.json"
$CleanupMode = $args -contains "--cleanup"
$ValidateOnlyMode = $args -contains "--validate-only"
$ResumeMode = $args -contains "--resume"
$PipelineArgs = @($args | Where-Object { $_ -ne "--resume" })

if ($ResumeMode) {
    $PipelineArgs += @("--output.resume", "true")
}

Write-Host ""
Write-Host "====================================="
Write-Host " My Trail Studio Pipeline"
Write-Host "====================================="
Write-Host ""

Write-Host "Project path: $Root"
Write-Host "Config: $ConfigPath"
Write-Host ""

if ($CleanupMode) {
    $cleanupScript = Join-Path $ScriptsDir "cleanup_pipeline.py"

    if (!(Test-Path $cleanupScript)) {
        Write-Host "Missing cleanup script: $cleanupScript" -ForegroundColor Red
        exit 1
    }

    try {
        $pythonVersion = python --version 2>&1
        Write-Host "Python OK: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "Python not found" -ForegroundColor Red
        exit 1
    }

    python $cleanupScript --root $Root --mode manual

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Cleanup failed." -ForegroundColor Red
        exit $LASTEXITCODE
    }

    Write-Host "Cleanup completed successfully." -ForegroundColor Green
    exit 0
}

$requiredFolders = @(
    $InputDir,
    $ScriptsDir,
    $ResourcesDir,
    "$ResourcesDir\font"
)

foreach ($folder in $requiredFolders) {
    if (!(Test-Path $folder)) {
        Write-Host "Missing folder: $folder" -ForegroundColor Red
        exit 1
    }
}

$generatedFolders = @(
    $OutputDir,
    "$OutputDir\frames",
    "$OutputDir\previews",
    "$OutputDir\final",
    "$OutputDir\data",
    $TempDir
)

foreach ($folder in $generatedFolders) {
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
        Write-Host "Folder created: $folder"
    }
}

if (!(Test-Path $ConfigPath)) {
    Write-Host "Missing pipeline_config.json in input" -ForegroundColor Red
    exit 1
}

Write-Host "Folders OK" -ForegroundColor Green

try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python OK: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found" -ForegroundColor Red
    exit 1
}

try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "FFmpeg OK: $ffmpegVersion" -ForegroundColor Green
} catch {
    Write-Host "FFmpeg not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Running technical validation..."
Write-Host ""

$validator = Join-Path $ScriptsDir "validate_pipeline.py"

python $validator --root $Root @PipelineArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Validation failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Validation completed successfully." -ForegroundColor Green

if ($ValidateOnlyMode) {
    Write-Host "validate-only mode completed. No preview or final render generated." -ForegroundColor Green
    exit 0
}

$manifestPath = python -c "import os, sys; root=sys.argv[1]; sys.path.insert(0, os.path.join(root, 'scripts')); from pipeline_config import load_config, parse_overrides; from pipeline_utils import resolve_path; config=load_config(os.path.join(root, 'input', 'pipeline_config.json')); config=parse_overrides(sys.argv[2:], config); print(os.path.join(resolve_path(root, config['output']['dir']), 'data', 'manifest.json'))" $Root @PipelineArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "Could not resolve manifest path." -ForegroundColor Red
    exit $LASTEXITCODE
}

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json

if ($manifest.config.output.preview.add -eq $true) {
    Write-Host "Preview mode enabled."
    $previewScript = Join-Path $ScriptsDir "render_preview.py"
    python $previewScript --root $Root --manifest $manifestPath

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Preview generation failed." -ForegroundColor Red
        exit $LASTEXITCODE
    }
} else {
    Write-Host "Final render mode enabled."
    $renderScript = Join-Path $ScriptsDir "render_final.py"
    python $renderScript --root $Root --manifest $manifestPath

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Final render generation failed." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}





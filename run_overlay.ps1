$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Pipeline = Join-Path $ScriptDir "run_mts_overlay_pipeline.ps1"

if (!(Test-Path $Pipeline)) {
    Write-Host "Missing main pipeline: $Pipeline" -ForegroundColor Red
    exit 1
}

& $Pipeline @args
exit $LASTEXITCODE



param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Resolution = "1080p",
    [int]$Fps = 30,
    [double]$OutputSpeed = 3.5,
    [int]$PreviewSeconds = 10,
    [string]$ClosingMessage = "Ruta Finalizada",
    [int]$ClosingSeconds = 3,
    [switch]$RunFinalRender
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Run-Step {
    param(
        [string]$Title,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "====================================="
    Write-Host $Title
    Write-Host "====================================="
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo el paso: $Title"
    }
}

Run-Step "1. Resumen inicial" {
    python -m ui_core.cli project-summary --project $ProjectId
}

Run-Step "2. Configurar exportacion final" {
    python -m ui_core.cli set-export `
        --project $ProjectId `
        --resolution $Resolution `
        --fps $Fps `
        --output-speed $OutputSpeed `
        --remove-audio `
        --single-final-video `
        --transitions `
        --closing `
        --closing-message $ClosingMessage `
        --closing-seconds $ClosingSeconds
}

Run-Step "3. Validar motor" {
    python -m ui_core.cli engine-validate --project $ProjectId
}

Run-Step "4. Generar preview" {
    python -m ui_core.cli engine-preview --project $ProjectId --seconds $PreviewSeconds
}

Run-Step "5. Revisar preview en resumen" {
    python -m ui_core.cli project-summary --project $ProjectId
}

if ($RunFinalRender) {
    Run-Step "6. Render final" {
        python -m ui_core.cli engine-render-final --project $ProjectId --confirm "RENDER_FINAL"
    }
} else {
    Write-Host ""
    Write-Host "====================================="
    Write-Host "6. Render final omitido"
    Write-Host "====================================="
    Write-Host "Ejecuta este script con -RunFinalRender para incluir el render final."
}

Run-Step "7. Revisar carpeta final" {
    $summaryJson = python -m ui_core.cli inspect-project --project $ProjectId | ConvertFrom-Json
    $finalDir = Join-Path $summaryJson.export.output_dir "final"
    Write-Host "Carpeta final: $finalDir"
    if (Test-Path $finalDir) {
        Get-ChildItem $finalDir -File | Select-Object Name, Length, LastWriteTime
    } else {
        Write-Host "No existe carpeta final todavia."
    }
}

Run-Step "8. Validacion y resumen final" {
    python -m ui_core.cli validate-project --project $ProjectId
    python -m ui_core.cli project-summary --project $ProjectId
}

Write-Host ""
Write-Host "Prueba integral completada."

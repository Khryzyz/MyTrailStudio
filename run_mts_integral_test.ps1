param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Resolution = "1080p",
    [int]$Fps = 30,
    [double]$OutputSpeed = 3.5,
    [string]$ExportPreset = "",
    [int]$PreviewSeconds = 10,
    [string]$ClosingMessage = "Route Completed",
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
        throw "Step failed: $Title"
    }
}

Run-Step "1. Initial summary" {
    .\mts.ps1 project-summary --project $ProjectId
}

if ($ExportPreset) {
    Run-Step "2. Apply export preset" {
        .\mts.ps1 apply-export-preset --project $ProjectId --preset $ExportPreset
    }
} else {
    Run-Step "2. Configure final export" {
        .\mts.ps1 set-export `
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
}

Run-Step "3. Validate engine" {
    .\mts.ps1 engine-validate --project $ProjectId --quiet
}

Run-Step "4. Generate preview" {
    .\mts.ps1 engine-preview --project $ProjectId --seconds $PreviewSeconds --quiet
}

Run-Step "5. Check preview in summary" {
    .\mts.ps1 project-summary --project $ProjectId
}

if ($RunFinalRender) {
    Run-Step "6. Final render" {
        .\mts.ps1 engine-render-final --project $ProjectId --confirm "RENDER_FINAL" --quiet
    }
} else {
    Write-Host ""
    Write-Host "====================================="
    Write-Host "6. Final render skipped"
    Write-Host "====================================="
    Write-Host "Run this script with -RunFinalRender to include the final render."
}

Run-Step "7. Check final folder" {
    $summaryJson = .\mts.ps1 inspect-project --project $ProjectId | ConvertFrom-Json
    $finalDir = Join-Path $summaryJson.export.output_dir "final"
    Write-Host "Final folder: $finalDir"
    if (Test-Path $finalDir) {
        Get-ChildItem $finalDir -File | Select-Object Name, Length, LastWriteTime
    } else {
        Write-Host "Final folder does not exist yet."
    }
}

Run-Step "8. Final validation and summary" {
    .\mts.ps1 validate-project --project $ProjectId
    .\mts.ps1 project-summary --project $ProjectId
}

Write-Host ""
Write-Host "Integral test completed."

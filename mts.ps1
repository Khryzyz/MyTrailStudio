$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

python -m ui_core.cli @args
exit $LASTEXITCODE

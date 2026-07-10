@echo off
setlocal

set "APP_ROOT=%~dp0"
cd /d "%APP_ROOT%"

python -m ui_app %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo My Trail Studio could not start.
    echo Exit code: %EXIT_CODE%
    echo.
    echo If PySide6 is missing, run:
    echo python -m pip install -r requirements-ui.txt
    echo.
    pause
)

exit /b %EXIT_CODE%

@echo off
setlocal

REM --- Configuration ---
set PYTHON_EXECUTABLE=python
set PROJECT_ROOT=%~dp0

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM --- Run the app ---
set PYTHONPATH=%PROJECT_ROOT%

echo.
echo Starting scrAPE Terminal GUI Wizard...
echo.

%PYTHON_EXECUTABLE% -m src.cli.cli_wizard %*
pause

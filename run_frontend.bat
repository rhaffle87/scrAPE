@echo off
setlocal

REM --- Configuration ---
set PYTHON_EXECUTABLE=python
set REQUIREMENTS_FILE=frontend\requirements.txt
set PROJECT_ROOT=%~dp0

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM --- Check if requirements are installed ---
if exist "%REQUIREMENTS_FILE%" (
    echo Checking for dependencies...
    python -m pip show flask >nul 2>&1
    if errorlevel 1 (
        echo Installing dependencies from %REQUIREMENTS_FILE%...
        python -m pip install -r %REQUIREMENTS_FILE%
    ) else (
        echo Dependencies are already installed.
    )
) else (
    echo Warning: %REQUIREMENTS_FILE% not found.
)

REM --- Run the app ---
set PYTHONPATH=%PROJECT_ROOT%

echo.
echo Starting frontend...
python -m frontend.app

pause

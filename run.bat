@echo off
setlocal enableextensions enabledelayedexpansion

set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"
set PYTHONPATH=%PROJECT_ROOT%

REM If arguments were passed, forward directly to CLI main.py
if not "%~1"=="" (
    python -m src.cli.main %*
    exit /b %ERRORLEVEL%
)

:MENU
cls
echo ========================================================================
echo                  scrAPE — UNIFIED MASTER LAUNCHER                      
echo ========================================================================
echo.
echo   [1] Launch WebUI Dashboard ^& System Tray Cockpit (FastAPI + HTMX)
echo   [2] Launch Interactive CLI Scrape Wizard
echo   [3] Interactive Domain Login (--login)
echo   [4] Enable Windows Boot Autostart
echo   [5] Install Package ^& Register Global 'scrape' Command
echo   [6] Launch Continuous Watchdog Agent (monitor_agent.py)
echo   [7] Launch Automated Release Wizard (src/cli/release.py)
echo   [0] Exit
echo.
echo ========================================================================
set /p CHOICE="Select option [0-7]: "

if "%CHOICE%"=="1" (
    echo.
    echo Starting WebUI Dashboard on http://localhost:10001 ...
    python -m frontend.app
    pause
    goto MENU
)

if "%CHOICE%"=="2" (
    echo.
    echo Starting Interactive CLI Wizard...
    python -m src.cli.cli_wizard
    pause
    goto MENU
)

if "%CHOICE%"=="3" (
    echo.
    set /p LOGIN_DOMAIN="Enter domain to login (e.g. example.com): "
    if not "!LOGIN_DOMAIN!"=="" (
        python -m src.cli.main --login !LOGIN_DOMAIN!
    )
    pause
    goto MENU
)

if "%CHOICE%"=="4" (
    echo.
    echo Enabling Windows Boot Autostart...
    set SHORTCUT_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\scrAPE_Dashboard.lnk
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('!SHORTCUT_PATH!'); $s.TargetPath = '%PROJECT_ROOT%run.bat'; $s.WorkingDirectory = '%PROJECT_ROOT%'; $s.Description = 'scrAPE WebUI Command Center & Tray Launcher'; $s.Save()"
    if exist "!SHORTCUT_PATH!" (
        echo SUCCESS: Autostart shortcut created at !SHORTCUT_PATH!
    ) else (
        echo ERROR: Failed to create shortcut.
    )
    pause
    goto MENU
)

if "%CHOICE%"=="5" (
    echo.
    echo Installing package in editable mode...
    pip install -e .
    echo.
    echo Global 'scrape' command registered.
    pause
    goto MENU
)

if "%CHOICE%"=="6" (
    echo.
    set /p WATCHDOG_KW="Enter keyword to monitor: "
    set /p WATCHDOG_SEED="Enter seed file path (optional, press Enter to skip): "
    set /p WATCHDOG_INT="Enter check interval in seconds [default: 60]: "
    if "!WATCHDOG_INT!"=="" set WATCHDOG_INT=60

    if not "!WATCHDOG_KW!"=="" (
        if not "!WATCHDOG_SEED!"=="" (
            python -m src.cli.monitor_agent --keyword "!WATCHDOG_KW!" --seed-file "!WATCHDOG_SEED!" --interval !WATCHDOG_INT! --use-state-cache
        ) else (
            python -m src.cli.monitor_agent --keyword "!WATCHDOG_KW!" --interval !WATCHDOG_INT! --use-state-cache
        )
    ) else (
        echo Keyword is required to launch Watchdog Agent.
    )
    pause
    goto MENU
)

if "%CHOICE%"=="7" (
    echo.
    python -m src.cli.release
    pause
    goto MENU
)

if "%CHOICE%"=="0" (
    exit /b 0
)

goto MENU

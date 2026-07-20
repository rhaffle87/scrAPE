@echo off
setlocal

REM --- Configuration ---
set PYTHON_EXECUTABLE=python
set PROJECT_ROOT=%~dp0
set AGENT_SCRIPT="%PROJECT_ROOT%src\cli\monitor_agent.py"

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM --- Run the agent ---
set PYTHONPATH=%PROJECT_ROOT%

echo.
echo Starting Continuous Watchdog Agent...
echo.

%PYTHON_EXECUTABLE% %AGENT_SCRIPT% %*
pause

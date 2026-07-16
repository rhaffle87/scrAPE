@echo off
rem Start script for scrAPE Continuous Watchdog Agent
python "%~dp0src\cli\monitor_agent.py" %*
pause

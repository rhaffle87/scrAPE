@echo off
set PYTHONPATH=%~dp0
python -m frontend.app %*
pause

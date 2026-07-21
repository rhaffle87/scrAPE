@echo off
echo ========================================
echo   Installing scrAPE CLI globally...
echo ========================================
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python package installation failed.
    pause
    exit /b %ERRORLEVEL%
)
echo.
echo ✅ scrAPE registered! You can now type 'scrape' from any terminal.
echo.
pause

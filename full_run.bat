@echo off
setlocal enabledelayedexpansion

REM ========================================================
REM scrAPE v0.29.0 — Master QA & Batch Diagnostic Suite
REM ========================================================

set "MODE=smoke"
set "TARGET_ARG=%~1"
set "SEEDS_PATTERN=seeds\*.txt"

if /i "%TARGET_ARG%"=="--deep" (
    set "MODE=deep"
    set "TARGET_ARG="
) else if /i "%TARGET_ARG%"=="-d" (
    set "MODE=deep"
    set "TARGET_ARG="
) else if /i "%TARGET_ARG%"=="--smoke" (
    set "MODE=smoke"
    set "TARGET_ARG="
) else if /i "%TARGET_ARG%"=="-s" (
    set "MODE=smoke"
    set "TARGET_ARG="
) else if not "%TARGET_ARG%"=="" (
    if exist "seeds\%TARGET_ARG%" (
        set "SEEDS_PATTERN=seeds\%TARGET_ARG%"
    ) else if exist "%TARGET_ARG%" (
        set "SEEDS_PATTERN=%TARGET_ARG%"
    )
    if /i "%~2"=="--deep" set "MODE=deep"
    if /i "%~2"=="-d" set "MODE=deep"
)

echo ========================================================
echo  scrAPE v0.29.0 BATCH DIAGNOSTIC SUITE
echo  Execution Mode : [%MODE%]
echo  Target Seeds   : [%SEEDS_PATTERN%]
echo ========================================================

if "%MODE%"=="deep" (
    set "PAGE_LIMIT=5000"
    set "MAX_RESULTS=0"
    set "CRAWL_DEPTH=3"
    set "WORKERS=8"
    set "DL_WORKERS=12"
    set "DL_SPEED_LIMIT=0"
) else (
    set "PAGE_LIMIT=15"
    set "MAX_RESULTS=10"
    set "CRAWL_DEPTH=2"
    set "WORKERS=4"
    set "DL_WORKERS=8"
    set "DL_SPEED_LIMIT=0"
)

for %%F in (%SEEDS_PATTERN%) do (
    set "filename=%%~nF"
    set "filepath=%%F"
    
    echo.
    echo ========================================================
    echo [RUN] QA DIAGNOSTIC RUN: !filename! (%MODE% mode)
    echo ========================================================
    
    python src\cli\main.py --keyword "!filename!" --seed-file "!filepath!" ^
        --max-results !MAX_RESULTS! ^
        --page-limit !PAGE_LIMIT! ^
        --crawl-depth !CRAWL_DEPTH! ^
        --workers !WORKERS! ^
        --dl-workers !DL_WORKERS! ^
        --dl-speed-limit !DL_SPEED_LIMIT! ^
        --use-state-cache ^
        --download-media ^
        --enable-governor ^
        --strict-domain ^
        --tag-dataset ^
        --auto-crop ^
        --aesthetic-score 4.0 ^
        --export-db ^
        --export-rag ^
        --export-parquet ^
        --enable-cas ^
        --enable-self-healing ^
        --output both ^
        --headless

    echo [INFO] Completed !filename!. Reaping orphaned workers...
    python -c "import psutil; [p.terminate() for p in psutil.process_iter(['name', 'cmdline']) if p.info.get('name') in ('chrome.exe', 'chromedriver.exe', 'camoufox.exe') and any('scoped_dir' in str(c) or 'headless' in str(c) for c in (p.info.get('cmdline') or []))]" 2>nul
)

echo.
echo ========================================================
echo [DONE] FULL BATCH SUITE COMPLETE. Check output\ for yields.
echo ========================================================


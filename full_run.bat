@echo off
setlocal enabledelayedexpansion


for %%F in (seeds\*.txt) do (
    set "filename=%%~nF"
    set "filepath=%%F"
    
    echo.
    echo ========================================================
    echo [RUN] QA DIAGNOSTIC RUN: !filename!
    echo ========================================================
    
    python src\cli\main.py --keyword "!filename!" --seed-file "!filepath!" ^
        --max-results 0 ^
        --page-limit 0 ^
        --crawl-depth 0 ^
        --workers 8 ^
        --dl-workers 12 ^
        --dl-speed-limit 600 ^
        --use-state-cache ^
        --download-media ^
        --enable-governor ^
        --strict-domain ^
        --tag-dataset ^
        --auto-crop ^
        --aesthetic-score 4.0 ^
        --export-db ^
        --export-rag ^
        --output both ^
        --headless
)

echo.
echo ========================================================
echo [DONE] FULL TEST SUITE COMPLETE. Check output\rejected\ for false positives.
echo ========================================================

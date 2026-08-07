@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo [!] Wiping cache for clean diagnostic run...
echo ========================================================
python src\cli\main.py --clear-cache

for %%F in (seeds\*.txt) do (
    set "filename=%%~nF"
    set "filepath=%%F"
    
    echo.
    echo ========================================================
    echo [RUN] QA DIAGNOSTIC RUN: !filename!
    echo ========================================================
    
    python src\cli\main.py --keyword "!filename!" --seed-file "!filepath!" ^
        --max-results 1000 ^
        --page-limit 500 ^
        --crawl-depth 3 ^
        --workers 8 ^
        --dl-workers 10 ^
        --dl-speed-limit 500 ^
        --rate-limit 4.0 ^
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
        --headless ^
        --save-rejected all
)

echo.
echo ========================================================
echo [DONE] FULL TEST SUITE COMPLETE. Check output\rejected\ for false positives.
echo ========================================================

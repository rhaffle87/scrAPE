#!/usr/bin/env bash
# ========================================================
# scrAPE v0.30.0 — Master QA & Batch Diagnostic Suite (POSIX)
# ========================================================

set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"

MODE="smoke"
TARGET_ARG="$1"
SEEDS_PATTERN="seeds/*.txt"

if [ "$TARGET_ARG" == "--deep" ] || [ "$TARGET_ARG" == "-d" ]; then
    MODE="deep"
    TARGET_ARG=""
elif [ "$TARGET_ARG" == "--smoke" ] || [ "$TARGET_ARG" == "-s" ]; then
    MODE="smoke"
    TARGET_ARG=""
elif [ -n "$TARGET_ARG" ]; then
    if [ -f "seeds/$TARGET_ARG" ]; then
        SEEDS_PATTERN="seeds/$TARGET_ARG"
    elif [ -f "$TARGET_ARG" ]; then
        SEEDS_PATTERN="$TARGET_ARG"
    fi
    if [ "$2" == "--deep" ] || [ "$2" == "-d" ]; then
        MODE="deep"
    fi
fi

echo "========================================================"
echo " scrAPE v0.30.0 BATCH DIAGNOSTIC SUITE"
echo " Execution Mode : [$MODE]"
echo " Target Seeds   : [$SEEDS_PATTERN]"
echo "========================================================"

if [ "$MODE" == "deep" ]; then
    PAGE_LIMIT=5000
    MAX_RESULTS=0
    CRAWL_DEPTH=3
    WORKERS=8
    DL_WORKERS=12
    DL_SPEED_LIMIT=0
else
    PAGE_LIMIT=15
    MAX_RESULTS=10
    CRAWL_DEPTH=2
    WORKERS=4
    DL_WORKERS=8
    DL_SPEED_LIMIT=0
fi

for filepath in $SEEDS_PATTERN; do
    [ -e "$filepath" ] || continue
    filename="$(basename "$filepath" .txt)"

    echo ""
    echo "========================================================"
    echo "[RUN] QA DIAGNOSTIC RUN: $filename ($MODE mode)"
    echo "========================================================"

    python3 src/cli/main.py --keyword "$filename" --seed-file "$filepath" \
        --max-results "$MAX_RESULTS" \
        --page-limit "$PAGE_LIMIT" \
        --crawl-depth "$CRAWL_DEPTH" \
        --workers "$WORKERS" \
        --dl-workers "$DL_WORKERS" \
        --dl-speed-limit "$DL_SPEED_LIMIT" \
        --use-state-cache \
        --download-media \
        --enable-governor \
        --strict-domain \
        --tag-dataset \
        --auto-crop \
        --aesthetic-score 4.0 \
        --export-db \
        --export-rag \
        --export-parquet \
        --enable-cas \
        --enable-self-healing \
        --output both \
        --headless || true

    echo "[INFO] Completed $filename. Reaping orphaned workers..."
    python3 -c "import psutil; [p.terminate() for p in psutil.process_iter(['name', 'cmdline']) if p.info.get('name') in ('chromium', 'chrome', 'chromedriver', 'camoufox') and any('scoped_dir' in str(c) or 'headless' in str(c) for c in (p.info.get('cmdline') or []))]" 2>/dev/null || true
done

echo ""
echo "========================================================"
echo "[DONE] FULL BATCH SUITE COMPLETE. Check output/ for yields."
echo "========================================================"

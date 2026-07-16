# Operational Scenarios — scrAPE

## 1. Broad Search (No Seed File)

```bash
python src/cli/main.py --keyword example_subject --seed seed.txt --page-limit 50
```

Uses the literal `seed.txt` with `example.com` URLs. Good for quick tests.

## 2. Targeted Seed Manifest

```bash
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --entity-token "Entity Name" --entity-token "keyword" ^
  --max-results 30 --page-limit 50 --crawl-depth 2 ^
  --download-media --workers 8 --dl-workers 6
```

Focused crawl using curated domain profiles. High precision via entity tokens.

## 3. Production Sweep (Full Run)

```bash
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --max-results 100 --workers 16 --dl-workers 8 ^
  --page-limit 200 --crawl-depth 3 --download-media --yes
```

Maximum throughput. Multi-subject runs should use separate terminals or a shell script.

## 4. Stealth / Minimal Footprint

```bash
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --workers 2 --dl-workers 1 --crawl-depth 1 ^
  --page-limit 20 --max-results 10
```

Low concurrency, shallow crawl. Minimal impact on target servers.

## 5. Uncapped Mirror Run

```bash
python src/cli/main.py --keyword deep_archive_subject --seed seeds/deep_archive_subject.txt ^
  --max-results 9999 --page-limit 5000 --crawl-depth 3 ^
  --workers 8 --dl-workers 4 --download-media --yes
```

Maximum collection for deep-archive subjects. Requires sufficient disk space. Use `--page-limit` to bound discovery.

## 6. Background Watchdog

```bash
# Terminal 1 — Run the scrape
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --max-results 50 --workers 8 --dl-workers 4 ^
  --page-limit 100 --crawl-depth 2 --download-media --yes

# Terminal 2 — Monitor output growth
dir /s output/example_subject/runs/
```

Use `tail` (or equivalent) on the log file for live progress. Run ID is printed at start and stored in `manifest.json`.

## 7. Validate Seed Only (Dry Run)

```bash
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt --dry-run
```

Parses and validates the seed manifest without crawling. Useful for debugging annotation syntax.

## 8. Quick Re-Run with Custom Slug

```bash
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --run-id "retry-01" --keyword-slug "subject-v2" ^
  --workers 8 --dl-workers 6 --page-limit 100 --download-media --yes
```

Multiple runs for the same subject are stored under separate run IDs inside `runs/`.

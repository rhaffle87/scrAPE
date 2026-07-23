# Operational Scenarios & Playbook — scrAPE

> Practical CLI command blueprints and workflow scenarios for common scraper operations.

---

## Scenario 1: Targeted Seed Manifest Run (Standard Flow)

Run a focused extraction using curated domain profiles and entity tokens for maximum precision:

```bash
python src/cli/main.py --keyword apple --seed seeds/apple.txt ^
  --entity-token "Apple Inc" --entity-token "iPhone" ^
  --max-results 50 --page-limit 100 --crawl-depth 2 ^
  --workers 8 --dl-workers 6 --download-media
```

---

## Scenario 2: High-Performance Production Sweep

Maximum throughput run using elevated worker limits:

```bash
python src/cli/main.py --keyword apple --seed seeds/apple.txt ^
  --max-results 200 --workers 16 --dl-workers 12 ^
  --page-limit 300 --crawl-depth 3 --download-media
```

> *Tip: Keep `--workers` $\le 16$ and `--dl-workers` $\le 24$ to avoid hardware bottlenecks.*

---

## Scenario 3: Stealth & Low-Impact Crawl

Low-concurrency, shallow crawl designed for polite scraping or fragile targets:

```bash
python src/cli/main.py --keyword apple --seed seeds/apple.txt ^
  --workers 2 --dl-workers 2 --crawl-depth 1 ^
  --page-limit 20 --max-results 15 --download-media
```

---

## Scenario 4: Auth-Walled Domain Extraction

Extract media from domains requiring user login:

```bash
# Step 1: Launch interactive login browser to authenticate and save session cookies
python src/cli/main.py --login protected-site.com

# Step 2: Run crawl using saved session cookies
python src/cli/main.py --keyword apple --seed seeds/apple.txt --download-media
```

Or inject existing cookies from a Netscape file:

```bash
python src/cli/main.py --inject-cookies cookies.txt --domain protected-site.com
```

---

## Scenario 5: Dry-Run Manifest Validation

Parse and validate seed syntax without making HTTP requests or downloading files:

```bash
python src/cli/main.py --keyword apple --seed seeds/apple.txt --dry-run
```

---

## Scenario 6: Continuous Watchdog Agent Mode

Run continuous monitoring loops (`monitor_agent.py`) using persistent SQLite WAL caching to process target domains on a set interval:

```bash
python src/cli/monitor_agent.py --keyword apple --seed seeds/apple.txt --interval 3600
```

---

## Scenario 7: WebUI Command Center & System Tray

Launch the web dashboard:

```bash
.\run_frontend.bat
```

Access `http://localhost:10001` to view live hardware telemetry, switch context-aware stats, manage files, and toggle Instant Unlimited Mode.

---

## Scenario 8: Downstream AI Dataset & RAG Preparation

Launch the interactive CLI wizard (`python src/cli/cli_wizard.py`):

- **Option 4 (Create Structured AI Dataset)**: Export files into *Consolidated Flat*, *Domain-Grouped*, or *Media-Type Grouped* folders.
- **Option 5 (Enterprise LLM RAG Ingestion)**: Export page metadata into *Consolidated Markdown*, *Chunked Page `.md` Files*, or *JSONL Embeddings*.

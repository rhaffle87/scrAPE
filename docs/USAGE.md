# Usage — scrAPE CLI

## Synopsis

```bash
python src/cli/main.py --keyword <keyword> --seed <path> [options]
```

## Arguments

 | Argument | Type | Default | Description |
 | --- | --- | --- | --- |
 | `--keyword` | `str` | **required** | Search keyword / subject name |
 | `--seed` | `str` | `seed.txt` | Path to seed manifest file |
 | `--max-results` | `int` | `50` | Max images+videos per run |
 | `--output-dir` | `str` | `./output` | Root output directory |
 | `--workers` | `int` | `8` | Page fetch concurrency |
 | `--dl-workers` | `int` | `6` | Download concurrency |
 | `--page-limit` | `int` | `100` | Max pages to crawl |
 | `--crawl-depth` | `int` | `2` | BFS max depth |
 | `--download-media` | flag | `False` | Enable actual file download |
 | `--ignore-robots` | flag | `False` | Skip robots.txt checks |
 | `--entity-token` | `str[]` | `[]` | Additional entity tokens (repeatable) |
 | `--dry-run` | flag | `False` | Parse seed + validate, no crawl |
 | `--run-id` | `str` | auto | Override run ID |
 | `--keyword-slug` | `str` | auto | Override output dir slug |
 | `--login` | `str` | None | Interactive headful login for a domain |
 | `--inject-cookies` | `str` | None | Import JSON or Netscape cookies.txt file |
 | `--domain` | `str` | None | Domain to associate with injected cookies |

## Seed Manifest

Domain profiles are defined in `.txt` seed files. See [README.md](../README.md#seed-manifest-format) for full annotation syntax.

```bash
# Basic run
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt

# Targeted with extra tokens
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --entity-token "Entity Name" --entity-token "topic"

# Production sweep (high concurrency, no confirmations)
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --max-results 100 --workers 16 --dl-workers 8 ^
  --page-limit 200 --crawl-depth 3 --download-media

# Validate seed manifest only
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt --dry-run

# Stealth mode (single worker, polite speed)
python src/cli/main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --workers 1 --page-limit 20 --crawl-depth 1

# Interactive login to capture session cookies for a protected domain
python src/cli/main.py --login example.com

# Inject existing cookies from a file
python src/cli/main.py --inject-cookies cookies.json --domain example.com
```

## Output Structure

```text
output/{keyword_slug}/runs/{run_id}/
├── manifest.json            # Full scrape result
└── media/                   # (if --download-media)
    ├── images/
    │   └── {filename}.{ext}
    └── videos/
        └── {filename}.{ext}
```

### manifest.json fields

 | Field | Description |
 | --- | --- |
 | `keyword` | Search keyword |
 | `run_id` | Unique run identifier |
 | `duration_seconds` | Total wall-clock time |
 | `run_metadata` | CLI flags used (workers, page_limit, etc.) |
 | `page_count` | Total pages scanned |
 | `scanned_pages` | List of page URLs visited |
 | `page_reports` | Per-page scan diagnostics |
 | `images` / `videos` | Kept asset items |
 | `rejected_items` | Rejected items with reason + score |
 | `domain_stats` | Per-domain stats (pages scanned, kept, rejected) |
 | `errors` | Per-domain error counts |

## Dry Run

```bash
python src/cli/main.py --keyword test --seed seed.txt --dry-run
```

Parses the seed file and prints the domain profiles without crawling.

## Interactive GUI Wizard & AI Pipeline Tools

```bash
python src/cli/cli_wizard.py
```

The interactive terminal GUI acts as a **high-efficiency fuel pump for AI**. It guides users through configuring and running crawls, mapping entire websites with systematic BFS and Crawl4AI, and converting messy pages into clean, structured data for LLM ingestions.

In addition to launching crawls, the wizard provides built-in utilities for downstream AI ingestion:

1. **General/Broad Search Scraping** — Launches automated searches and deep recursive crawling.
2. **Specified/Targeted Scraping** — Runs targeted crawls against strict seed manifests.
3. **Continuous Watchdog Agent** — Polls target sites on a set scheduler to monitor changes.
4. **Create Structured AI Dataset** — Groups and exports files from any completed run into a consolidated folder with custom layouts (Consolidated Flat, Domain-Grouped, or Media-Type Grouped).
5. **Enterprise LLM RAG Ingestion** — Extracts page titles, alt texts, image contexts, and URLs from scraped results, outputting clean formats ready for ingestion (Single Consolidated Markdown, Chunked Page Markdown documents, or JSONL Embeddings formats).

## Local Web GUI

```bash
.\run_frontend.bat
```
*(Alternatively, you can run `python -m frontend.app`)*

The Local Web GUI provides a fully decoupled, HTMX-powered dynamic dashboard hosted locally. It allows you to:
1. **View the Dashboard & Context-Aware Telemetry:** Access global aggregated statistics on the **Command Center** view, or switch to per-subject scoped totals (`SUBJ.RUNS`, `ASSET.IMG`, `ASSET.VID`, `TARGETS.SCAN`) with global comparison sub-lines (`/ N total`) when viewing a subject in the **Media Vault**.
2. **Interactive File Management:** Physically open the containing OS folder or securely delete files directly from the gallery UI without refreshing.
3. **Trigger & Monitor Scrapes:** Programmatically trigger background scrapes directly from the UI, stream the live terminal output to the browser, and monitor real-time hardware telemetry (CPU, RAM, Disk space) via auto-polling HTMX widgets.
4. **Hardware Safety Threshold Warnings:** Dynamic client-side validator (`validateSafetyThresholds()`) alerts users if concurrency parameters exceed safe hardware limits (>16 scrapers, >24 download workers).
5. **Interactive Help Tooltips & Modes:** Hover over any `[?]` help badge for parameter documentation, or toggle between Custom Configuration and Instant Unlimited Mode.
6. **Process Abort:** Use the `[ABORT]` button to forcefully kill lingering scraper processes if they hang or if you want to stop early.
7. **System Tray Integration:** Runs in the background with a custom high-contrast taskbar icon (`launcher.py`) providing quick status checks and tray menu controls.

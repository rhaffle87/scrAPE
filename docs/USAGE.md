# Usage Guide — scrAPE

> Comprehensive reference for the scrAPE CLI engine, Interactive Terminal Wizard, and Decoupled WebUI Dashboard.

---

## 1. Synopsis

```bash
python src/cli/main.py --keyword <keyword> --seed <path> [options]
```

Or run via global binary wrapper:

```bash
scrape
```

---

## 2. CLI Arguments Reference

| Argument | Type | Default | Description |
|---|---|---|---|
| `--keyword` | `str` | **required** | Primary search keyword / subject name |
| `--seed` | `str` | `seed.txt` | Path to seed manifest file |
| `--max-results` | `int` | `50` | Maximum kept images and videos per run |
| `--output-dir` | `str` | `./output` | Root directory for output runs and media |
| `--workers` | `int` | `8` | Number of concurrent page fetching crawler threads |
| `--dl-workers` | `int` | `6` | Number of concurrent media downloading threads |
| `--page-limit` | `int` | `100` | Hard cap on total pages scanned across all domains |
| `--crawl-depth` | `int` | `2` | Maximum BFS link graph traversal depth |
| `--download-media` | flag | `False` | Enables downloading files to disk (default dry metadata only) |
| `--ignore-robots` | flag | `False` | Bypasses `robots.txt` disallow checks |
| `--entity-token` | `str[]` | `[]` | Additional subject keywords/synonyms (repeatable) |
| `--dry-run` | flag | `False` | Parses and validates seed manifest without crawling |
| `--validate-seed` | flag | `False` | Validates seed manifest syntax and prints domain profiles |
| `--run-id` | `str` | auto | Custom run identifier directory name |
| `--keyword-slug` | `str` | auto | Custom output directory slug |
| `--login` | `str` | `None` | Opens headful browser to log into a protected domain and save cookies |
| `--inject-cookies` | `str` | `None` | Imports JSON or Netscape `cookies.txt` file |
| `--domain` | `str` | `None` | Target domain to associate with injected cookies |
| `--proxy-list` | `str` | `None` | Path to proxy file (`ip:port` or `http://user:pass@host:port`) |

---

## 3. Common Execution Commands

### Basic Extraction Run
```bash
python src/cli/main.py --keyword apple --seed seeds/apple.txt --download-media
```

### High-Precision Multi-Token Run
```bash
python src/cli/main.py --keyword apple --seed seeds/apple.txt ^
  --entity-token "Apple Inc" --entity-token "iPhone" --entity-token "MacBook" ^
  --download-media
```

### High-Performance Sweep
```bash
python src/cli/main.py --keyword apple --seed seeds/apple.txt ^
  --max-results 200 --workers 16 --dl-workers 12 ^
  --page-limit 300 --crawl-depth 3 --download-media
```

### Stealth Crawl (Polite Speed)
```bash
python src/cli/main.py --keyword apple --seed seeds/apple.txt ^
  --workers 2 --dl-workers 2 --page-limit 20 --crawl-depth 1 --download-media
```

### Cookie Injection & Session Authentication
```bash
# Capture session cookies via interactive login browser
python src/cli/main.py --login protected-site.com

# Inject existing Netscape cookies.txt
python src/cli/main.py --inject-cookies cookies.txt --domain protected-site.com
```

---

## 4. Interactive Terminal Wizard & AI Fuel Tools

Launch the interactive CLI wizard:

```bash
python src/cli/cli_wizard.py
```

The terminal wizard provides guided menus for scraping, continuous watchdog scheduling, and downstream AI dataset preparation:

1. **Broad Search Scraping** — Performs automated search queries and recursive crawling.
2. **Targeted Manifest Scraping** — Runs structured crawls against selected seed manifests.
3. **Continuous Watchdog Agent** — Launches long-running monitoring loops (`monitor_agent.py`) using persistent SQLite WAL caching to process target sites on a set schedule.
4. **Create Structured AI Dataset** — Packages completed run output into consolidated structures:
   - *Consolidated Flat*: All files copied into one folder with domain prefixes.
   - *Domain-Grouped*: Subdirectories per origin domain.
   - *Media-Type Grouped*: Separate `/images` and `/videos` directories.
5. **Enterprise LLM RAG Ingestion** — Extracts page titles, alt texts, image contexts, and URLs into clean formats ready for vector indexing:
   - *Single Consolidated Markdown Document*
   - *Chunked Page-Level `.md` Files* (ideal for RAG document splitters)
   - *JSONL Embeddings Format*

---

## 5. Local WebUI Command Center

Launch the WebUI server:

```bash
.\run_frontend.bat
```

Open `http://localhost:10001` in your browser.

### Key WebUI Features

- **Command Center Dashboard**: Configure parameters, select preset profile slots (Slot 1–5), toggle Instant Unlimited mode, and view live OS telemetry (CPU, RAM, Disk).
- **Option C Context-Aware Statistics**: Telemetry cards display global totals on the Command Center and automatically switch to subject-scoped counts when viewing a subject in the Media Vault (including a `/ N total` global comparison sub-line).
- **Media Vault Gallery**: Browse downloaded assets grouped recursively by domain. Directly delete unwanted files or open their containing folder on disk via HTMX.
- **Hardware Safety Threshold Warnings**: Client-side validator alerts users if worker settings exceed safe bounds (>16 scrapers, >24 download threads).
- **Live Resizable Terminal Console**: Real-time progress streaming with severity color-coding and progress bar formatting.
- **System Tray Management**: Runs as a background taskbar tray application (`launcher.py`) with status indicator menu options.

---

## 6. Output Directory Structure & Manifest Schema

```text
output/{keyword_slug}/runs/{run_id}/
├── manifest.json            # Complete scrape execution result
├── run_summary.json         # Structured post-run observability report
├── domain_report.json       # Per-domain crawl counts
└── media/                   # Downloaded media (if --download-media enabled)
    ├── images/
    │   └── {domain}/
    │       └── {filename}.{ext}
    └── videos/
        └── {domain}/
            └── {filename}.{ext}
```

### `manifest.json` Core Schema

| Field | Type | Description |
|---|---|---|
| `keyword` | `str` | Search keyword used for extraction |
| `run_id` | `str` | Unique run identifier timestamp |
| `duration_seconds` | `float` | Total execution wall-clock time |
| `run_metadata` | `dict` | Execution flags (`workers`, `dl_workers`, `page_limit`, `crawl_depth`) |
| `page_count` | `int` | Total web pages scanned |
| `images` | `list[dict]` | Kept image items with metadata, score, and disk paths |
| `videos` | `list[dict]` | Kept video items with resolution hints and disk paths |
| `rejected_items` | `list[dict]` | Items filtered out with score and rejection reasons |
| `domain_stats` | `dict` | Per-domain stats (pages scanned, kept, rejected, error counts) |

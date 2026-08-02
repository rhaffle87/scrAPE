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
| `--keyword` | `str` | `None` | Keyword query to search for. |
| `--login` | `str` | `None` | Interactive headful login for the specified domain to save session cookies. |
| `--inject-cookies` | `str` | `None` | Import a JSON or Netscape `cookies.txt` file. |
| `--domain` | `str` | `None` | Domain to associate with the injected cookies. |
| `--max-results` | `int` | `50` (or dynamic) | Maximum number of media items per type to keep. Use 0 for unlimited. |
| `--output` | `{json,csv,both}` | `json` | Output format. |
| `--export-db` | flag | `False` | Export scraped results to a SQLite database (`results.db`). |
| `--download-media` | flag | `False` | Download discovered media into the output directory. |
| `--seed-url` | `str[]` | `[]` | Seed page URL to scrape directly. Repeat for multiple URLs. |
| `--seed-file` | `str` | `None` | Text file containing one seed URL per line. |
| `--seed-domain` | `str[]` | `[]` | Additional domain roots to treat as in-scope for strict-domain mode. |
| `--allow-domain` | `str[]` | `[]` | Restrict scraping to these domains. Repeat for multiple domains. |
| `--block-domain` | `str[]` | `[]` | Skip these domains. Repeat for multiple domains. |
| `--entity-token` | `str[]` | `[]` | Extra name/entity token to boost relevance scoring. Repeat as needed. |
| `--skip-search` | flag | `False` | Disable keyword search and only scrape provided seed URLs. |
| `--page-limit` | `int` | `100` | Maximum number of pages to visit during the crawl. Use 0 for unlimited. |
| `--crawl-depth` | `int` | `2` | Maximum depth for recursive link traversal. Use 0 for unlimited. |
| `--strict-domain` | flag | `False` | Keep crawl candidates inside the seed domain set. |
| `--site-tree-only` | flag | `False` | Keep discovered links within the same seed path subtree. |
| `--domain-delay` | `str[]` | `[]` | Override the per-domain request rate (e.g. `example.com=3.0`). |
| `--proxy` | `str` | `None` | A single HTTP/SOCKS proxy URL to use for all requests. |
| `--proxy-list` | `str` | `None` | A text file containing one proxy URL per line for rotation. |
| `--captcha-provider` | `str` | `None` | Provider for solving captchas (`capsolver`, `2captcha`, `anticaptcha`). |
| `--captcha-key` | `str` | `None` | API key for the selected captcha provider. |
| `--max-captcha-spend` | `float`| `None` | Maximum per-run budget for captcha solving (USD). |
| `--workers` | `int` | `6` | Number of pages to fetch concurrently. |
| `--dl-workers` | `int` | `16` | Number of media files to download concurrently. |
| `--enable-governor` | flag | `False` | Enable dynamic system CPU/RAM load governor to scale worker threads dynamically. |
| `--dl-speed-limit` | `float`| `0.0` | Maximum total media download bandwidth limit in KB/s (0 = unlimited). |
| `--rate-limit` | `float`| `0.0` | Maximum global page request rate limit in req/sec (0.0 = unlimited). |
| `--force-search` | flag | `False` | Force DuckDuckGo keyword search even when a seed file is present. |
| `--clear-cache` | flag | `False` | Wipe the entire cache directory before starting the crawl. |
| `--ignore-robots` | flag | `False` | Bypass `robots.txt` rules and fetch all URLs. |
| `--use-state-cache` | flag | `False` | Use a persistent SQLite state cache to prevent re-crawling URLs across runs. |
| `--headless` | flag | `False` | Force the browser to run in headless mode. |
| `--stealth-headful` | flag | `False` | Run stealth browser fallbacks in headful mode (visible browser). |
| `--validate-seed` | `str` | `None` | Validate the syntax and annotations of the specified seed file, then exit. |
| `--aesthetic-score` | `float`| `None` | Minimum aesthetic quality score threshold (1.0-10.0) for downloaded images. |
| `--auto-crop` | flag | `False` | Automatically generate smart face/body-centered cropped images for LoRA training. |

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

### Docker Execution
```bash
# Build the container (PUPPETEER_SKIP_DOWNLOAD=true is automatically handled in the Dockerfile)
docker build -t scrape-engine .

# Run the interactive Command Center
docker run -p 10001:10001 scrape-engine

# Run a CLI sweep via Docker
docker run -v ${PWD}/output:/app/output scrape-engine python src/cli/main.py --keyword apple --seed seeds/apple.txt --download-media
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

## 5. Master Launcher & Dashboard Startup

```powershell
# Unified Interactive Master Launcher (Menu: WebUI, Wizard, Auth Login, Autostart, Global Install)
.\run.bat

# Continuous Watchdog Monitoring Agent
.\run_monitor.bat --keyword "<subject>" --use-state-cache
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

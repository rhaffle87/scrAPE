# Usage Guide — scrAPE
> Comprehensive reference for the scrAPE CLI engine, Interactive Terminal Wizard, and Decoupled WebUI Dashboard.

---

## 1. Synopsis

The core entry point for scrAPE is the Python CLI engine. You can invoke it directly or via the global binary wrapper:

```bash
# Direct Python invocation
python src/cli/main.py --keyword <keyword> --seed <path> [options]

# Global binary wrapper (if installed via pip install -e .)
scrape --keyword <keyword> --seed <path> [options]
```

---

## 2. Standardized Operating Profiles (Examples First)

Depending on your objective, use these pre-tuned profiles designed to maximize throughput while preventing IP bans and system lag:

### Profile 1: Tactical WebUI Command Center (Interactive)
Best for interactive crawling, live visualization, and instant RAG exports.
- **Launch**: `.\run.bat` (Select Option 1) or `python frontend/app.py`
- **URL**: `http://localhost:10001`

### Profile 2: High-Throughput Production CLI Run
Maximum speed and efficiency for large-scale scrapes.
```bash
python src/cli/main.py --keyword "architecture" --seed seeds/architecture.txt \
  --max-results 200 --workers 12 --dl-workers 16 \
  --page-limit 200 --crawl-depth 2 --download-media \
  --enable-governor --use-state-cache --headless \
  --rate-limit 2.0 --dl-speed-limit 5000
```

### Profile 3: Continuous Watchdog Agent (Always-On)
Long-running background monitoring loop with adaptive backoff.
```bash
.\run_monitor.bat --keyword "architecture" --use-state-cache
```

### Profile 4: Automated AI Dataset Curation (ML Workflow)
Automated pipeline for tagging, cropping, and exporting data for LLM/RAG ingestion.
```bash
python src/cli/main.py --keyword "concept art" --seed seeds/art.txt \
  --download-media --tag-dataset --auto-crop --export-rag \
  --aesthetic-score 5.5 --use-state-cache
```

### Profile 5: Cookie Injection & Session Authentication
Capture or inject session cookies for WAF bypass.
```bash
# Capture session cookies via interactive login browser
python src/cli/main.py --login protected-site.com

# Inject existing Netscape cookies.txt
python src/cli/main.py --inject-cookies cookies.txt --domain protected-site.com
```

---

## 3. CLI Arguments Reference

### Core Arguments
| Argument | Type | Default | Description |
|---|---|---|---|
| `--keyword` | `str` | `None` | Keyword query to search for. |
| `--seed-file` | `str` | `None` | Text file containing one seed URL per line (e.g. `seeds/subject.txt`). |
| `--seed-url` | `str[]` | `[]` | Seed page URL to scrape directly. Repeat for multiple URLs. |

### Limits & Scope
| Argument | Type | Default | Description |
|---|---|---|---|
| `--max-results` | `int` | `50` | Maximum media items per type to keep (0 = unlimited). |
| `--page-limit` | `int` | `100` | Maximum pages to visit during the crawl (0 = unlimited). |
| `--crawl-depth` | `int` | `2` | Maximum depth for recursive link traversal (0 = unlimited). |
| `--strict-domain` | flag | `False` | Keep crawl candidates inside the seed domain set. |
| `--site-tree-only` | flag | `False` | Keep discovered links within the same seed path subtree. |
| `--allow-domain` | `str[]` | `[]` | Restrict scraping to these domains. |
| `--block-domain` | `str[]` | `[]` | Skip these domains. |

### Concurrency & Throttling
| Argument | Type | Default | Description |
|---|---|---|---|
| `--workers` | `int` | `6` | Number of pages to fetch concurrently. |
| `--dl-workers` | `int` | `16` | Number of media files to download concurrently. |
| `--enable-governor` | flag | `False` | Enable dynamic system CPU/RAM load governor to scale worker threads. |
| `--dl-speed-limit` | `float`| `0.0` | Max total media download bandwidth limit in KB/s (0 = unlimited). |
| `--rate-limit` | `float`| `0.0` | Max global page request rate limit in req/sec (0.0 = unlimited). |
| `--domain-delay` | `str[]` | `[]` | Override the per-domain request rate (e.g. `example.com=3.0`). |

### ML, AI & Export Options
| Argument | Type | Default | Description |
|---|---|---|---|
| `--download-media` | flag | `False` | Download discovered media into the output directory. |
| `--output` | `enum` | `json` | Output format (`json`, `csv`, `both`). |
| `--export-db` | flag | `False` | Export scraped results to a SQLite database (`results.db`). |
| `--export-rag` | flag | `False` | Export chunked text embeddings (`rag_payload.jsonl`). |
| `--tag-dataset` | flag | `False` | Auto-generate AI caption/tag sidecar `.txt` files for images. |
| `--auto-crop` | flag | `False` | Generate smart cropped images for LoRA training. |
| `--aesthetic-score`| `float`| `None` | Minimum aesthetic quality score threshold (1.0-10.0). |

### Stealth, Proxy & CAPTCHA
| Argument | Type | Default | Description |
|---|---|---|---|
| `--headless` | flag | `False` | Force the browser to run in headless mode. |
| `--stealth-headful`| flag | `False` | Run stealth browser fallbacks in headful mode (visible browser). |
| `--proxy` | `str` | `None` | A single HTTP/SOCKS proxy URL. |
| `--proxy-list` | `str` | `None` | A text file containing one proxy URL per line for rotation. |
| `--captcha-provider`| `str` | `None` | CAPTCHA provider (`capsolver`, `2captcha`, `anticaptcha`). |
| `--captcha-key` | `str` | `None` | API key for the selected captcha provider. |

### State & Cache
| Argument | Type | Default | Description |
|---|---|---|---|
| `--use-state-cache`| flag | `False` | Use persistent SQLite WAL cache to prevent re-crawling URLs. |
| `--clear-cache` | flag | `False` | Wipe the entire cache directory before starting the crawl. |

---

## 4. Output Directory Structure & Manifest Schema

All runs are organized cleanly into the `output/` directory:

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

---

## 5. Docker Execution

```bash
# Build the container (PUPPETEER_SKIP_DOWNLOAD=true is automatically handled in the Dockerfile)
docker build -t scrape-engine .

# Run the interactive Command Center WebUI
docker run -p 10001:10001 scrape-engine

# Run a CLI sweep via Docker (mounting output to host)
docker run -v ${PWD}/output:/app/output scrape-engine python src/cli/main.py --keyword apple --seed seeds/apple.txt --download-media
```

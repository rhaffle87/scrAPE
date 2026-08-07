# scrAPE — Scraper for Archival & Production Extraction
> Autonomous media extraction and stealth crawl engine engineered for high-throughput asset discovery and resilient WAF bypass.

scrAPE is an autonomous media extraction & stealth crawl engine that runs locally on your machine. Built for domain crawling, high-throughput asset discovery, WAF bypass, and AI dataset curation, it handles complex single-page applications (SPAs), Cloudflare Turnstile protections, and high-concurrency downloads with real-time hardware telemetry.

## Key Features

- **Dynamic Tactical WebUI**: Decoupled FastAPI + HTMX dashboard featuring an interactive HTML5 Canvas crawl network tree, live OS telemetry (CPU, RAM, Disk), process controls, and dual speed limiters.
- **8-Tier WAF Escalation & Stealth**: Defeats Cloudflare Turnstile, reCAPTCHA v2/v3, and auth walls using an 8-tier fallback pipeline (Local Cookies → Crawl4AI → Crawlee Cheerio → DrissionPage → Crawlee Puppeteer → Helium → undetected-chromedriver → Camoufox → FlareSolverr).
- **Universal Captcha Auto-Solving**: Automated token injection via CapSolver, 2Captcha, or AntiCaptcha.
- **HardwareLoadGovernor**: Dynamic system RAM & CPU monitoring that overrides the pipeline's concurrency factor (scales 1x to 3x) and forces garbage collection under load.
- **Dual Speed Limiters**: Token-bucket rate-limiting on outgoing page requests (`RPS`) and network bandwidth throttling on media asset downloads (`KBPS`).
- **Resumable HTTP Range Downloads**: Persistent SQLite queue paired with HTTP 206 Partial Content byte resumption and Pillow image sanitization.
- **AI Dataset Auto-Tagging & Quality Export**: Hybrid vision model auto-tagger (Ollama) with WD14 Booru classification, Kohya dataset exporter, and 64-bit perceptual `dHash` near-duplicate filtering.
- **Pluggable Notification Architecture**: Multi-channel webhook notifier supporting Telegram Bot alerts, Discord rich embeds, Slack, and generic webhooks.

## Tech Stack

- **Language**: Python 3.10+ (CLI & Core Engine), Node.js 18+ (Crawlee Bridge)
- **Framework**: FastAPI (Backend API)
- **Frontend**: HTMX with HTML5 Canvas (No heavy SPA frameworks)
- **Database**: Persistent SQLite (WAL mode)
- **Extraction Tools**: Crawl4AI, DrissionPage, undetected-chromedriver, Helium, Camoufox, yt-dlp, BeautifulSoup4
- **Node.js Bridge**: Express.js, Crawlee, Puppeteer, puppeteer-extra-plugin-stealth
- **Deployment/Solving**: Docker (FlareSolverr native binding on port 8191)

## Prerequisites

- **Python 3.10+** (Python 3.12/3.13 fully supported)
- **Node.js 18+** and `npm` (Required for the `crawlee_bridge` stealth tiers)
- **Git**
- **Docker** (Optional, but highly recommended for FlareSolverr background auto-start)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/scraper.git
cd scraper
```

### 2. Install Python Dependencies

Create and activate a virtual environment (recommended):

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

Install requirements:

```bash
pip install -r requirements.txt
```

### 3. Install Node.js Dependencies

Navigate to the bridge directory and install the required Crawlee/Puppeteer stealth packages:

```bash
cd crawlee_bridge
npm install
cd ..
```

*Note: If you run the unified master launcher (`run.bat` / `run.sh`), it will attempt to detect and install missing Node.js dependencies automatically.*

### 4. Environment Setup

Copy the example environment file:

```bash
cp .env.example .env
```

Configure the essential variables in `.env`:

| Variable | Description | Example |
|----------|-------------|---------|
| `WEBUI_HOST` | Host address for the dashboard | `0.0.0.0` |
| `WEBUI_PORT` | Port for the dashboard | `10001` |
| `TELEGRAM_BOT_TOKEN` | (Optional) Alerts for completion/WAF issues | `123456:ABC-DEF1234...` |
| `CAPSOLVER_API_KEY` | (Optional) Third-party Captcha solving | `CAP-...` |
| `DOWNLOAD_RATE_LIMIT_RPS` | Hard cap on download requests per second | `5.0` |

### 5. Start the Application

**Using the Unified Master Launcher (Recommended):**

```powershell
# Windows
.\run.bat

# macOS / Linux
./run.sh
```
This opens an interactive menu to start the WebUI, run the CLI Wizard, or execute the continuous Watchdog monitoring agent.

**Running the Dashboard Manually:**

```bash
# Starts the FastAPI/HTMX Command Center on http://localhost:10001
.\run_frontend.bat  # Or python frontend/app.py
```

**Running a Direct CLI Scrape:**

```bash
python src/cli/main.py --keyword "architecture" --seed-file seeds/architecture.txt --download-media --workers 8 --dl-workers 12
```

## Architecture

### Directory Structure

```text
scrape-dashboard/
├── crawlee_bridge/      # Node.js Express Server for Puppeteer/Cheerio stealth
├── frontend/            # FastAPI + HTMX WebUI
│   ├── app.py           # Core FastAPI application
│   ├── routers/         # Decoupled API routes (dashboard, dataset, seeds, watchdog)
│   └── templates/       # HTMX Brutalist templates
├── src/                 # Python Source Core
│   ├── cli/             # Entry points, interactive launcher, wizard
│   ├── core/            # BFS Engine, Managers, Filtering, Pipeline orchestration
│   ├── scraper/         # Base and Specialized extractors (google_images, video_scraper)
│   ├── plugins/         # Extractor plugins (yt-dlp, Reddit, Civitai, Booru)
│   ├── network/         # 8-tier WAF Pipeline, HttpClient, Proxy Manager
│   ├── storage/         # Range-resumable FileDownloader, SQLite WAL StateCache
│   ├── ml/              # AI Auto-tagger, Aesthetic Scorer, Vector Hashing
│   └── monitoring/      # HardwareLoadGovernor, Telemetry, Structured Logging
├── data/                # Configuration Registries (domain_config, normalisation)
├── docs/                # Technical documentation
└── seeds/               # Per-subject manifest target files
```

### Request Lifecycle (WAF Pipeline)

1. URL is discovered and enqueued by the BFS Crawler (`src/core/managers.py`).
2. `HttpClient` (`src/network/http_client.py`) attempts to fetch the URL using standard TLS parameters and local harvested cookies.
3. If an auth wall (302 redirect), HTTP 403, or HTTP 429 is encountered, the request hits the **Stealth Pipeline**.
4. The pipeline iterates through configured engines (Crawl4AI → Crawlee → DrissionPage → Camoufox → FlareSolverr) based on the domain's historical success memory.
5. If a CAPTCHA is detected (Turnstile, reCAPTCHA), the `CaptchaStrategy` delegates to CapSolver/2Captcha.
6. Once bypassed, the HTML is passed back to the `ScrapingEngine` for CSS selection and asset extraction.

## Environment Variables

### Core Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `WEBUI_HOST` | Bound host IP for FastAPI | `0.0.0.0` |
| `WEBUI_PORT` | Bound port for FastAPI | `10001` |
| `MAX_CONCURRENT_PER_HOST`| Max concurrent connections to a single domain | `4` |
| `PROXY_MAX_BANDWIDTH_MB` | Circuit breaker for proxy bandwidth | `500.0` |
| `DOWNLOAD_RATE_LIMIT_RPS`| Overall download requests per second throttle | `5.0` |

### Notification & Captcha Integration (Optional)

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token for Telegram Bot integration |
| `TELEGRAM_CHAT_ID` | Your personal or group Chat ID |
| `HARVEST_NOTIFY_THRESHOLD`| Send an alert every N items downloaded |
| `DISCORD_WEBHOOK_URL`| Discord webhook for rich embedded alerts |
| `CAPSOLVER_API_KEY` | Key for automated CAPTCHA bypassing |

## Available Scripts

| Command | Description |
|---------|-------------|
| `.\run.bat` | Unified interactive master menu (Windows) |
| `./run.sh` | Unified interactive master menu (POSIX) |
| `scrape` | Global CLI execution (if installed via `pip install -e .`) |
| `python src/cli/main.py --help` | View all scraping arguments and thresholds |
| `python src/cli/cli_wizard.py` | Step-by-step interactive configuration wizard |
| `python src/cli/monitor_agent.py`| Launch the continuous background Watchdog daemon |

## Testing

scrAPE uses `pytest` for unit and integration testing. Tests include network fallback simulation, database transaction integrity, and UI state verification.

### Running Tests

```bash
# Run the complete test suite
pytest tests/ -v

# Run specific functional areas
pytest tests/test_stealth_circuit_breaker.py -v
pytest tests/test_download_retries.py -v
```

All test scripts are maintained exclusively inside the `tests/` directory. Temporary diagnostic or scratch scripts should be kept in `scratch/`.

## Deployment

scrAPE is primarily designed to run locally or on a dedicated VPS/bare-metal server, due to its heavy reliance on headful browsers (for Turnstile bypass) and extensive disk I/O.

### Docker (FlareSolverr Integration)

The scraper seamlessly integrates with FlareSolverr to handle Cloudflare IUAM.

1. The scraper attempts to bind to `http://127.0.0.1:8191/v1`.
2. If unreachable, the internal `FlareSolverrMonitor` executes a background Docker auto-start:
   ```bash
   docker start flaresolverr
   ```
3. Ensure you have pulled the FlareSolverr image:
   ```bash
   docker pull ghcr.io/flaresolverr/flaresolverr:latest
   ```

*(See the `docker-compose.yml` file for multi-container orchestration of the entire stack).*

### Hardware Load Governor

If you deploy to a memory-constrained environment (e.g., a VPS with <4GB RAM), the `HardwareLoadGovernor` will automatically:
- Detect system load and throttle the `ThreadPoolExecutor` worker count dynamically (down to 1x scaling).
- Force Python garbage collection (`gc.collect()`) when RAM utilization spikes.
- Restrict heavy stealth tiers (like Puppeteer and Camoufox) if resources are exhausted.

## Troubleshooting

### Playwright/Chromium Fails to Launch

**Error:** `Executable doesn't exist at C:\Users\...` or `BrowserType.launch: Failed to launch`
**Solution:** You need to install the Playwright browsers.
```bash
playwright install chromium
```

### Crawlee Bridge Fails / Node.js Errors

**Error:** `Failed to connect to Crawlee bridge at http://localhost:3000`
**Solution:** The Node.js dependencies are missing or the bridge crashed.
1. Navigate to `crawlee_bridge/`.
2. Delete `node_modules` and run `npm install`.
3. Check `crawlee_bridge.log` in the root directory for specific Express.js crash traces.

### 429 Too Many Requests / Fast-Fail Cutoffs

**Error:** Domains are instantly cutting off or failing downloads.
**Solution:**
1. Check `run_summary.json` for rejection reasons.
2. If a CDN is aggressively blocking you, lower `--dl-workers` (e.g., `4`), or define `# Rate-limit: 0.5 req/s` in your seed manifest for that specific domain.
3. Ensure your stealth tiers are active and you have a valid Captcha API key configured.

## License

Distributed under the **MIT License**. See `LICENSE` for more information.

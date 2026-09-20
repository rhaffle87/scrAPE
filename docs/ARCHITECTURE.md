# Architecture Guide — scrAPE
> Technical reference covering system design, module organization, multi-tier fallback pipeline, concurrency model, and storage architecture.

---

## 1. System Data Flow

```mermaid
flowchart TD
    SM["Seed Manifest<br/>(seeds/*.txt)"]
    P["SeedManifest Parser<br/>.from_file() → DomainProfile[]"]
    EO["EngineOptions<br/>(keyword, entity_tokens,<br/>domain_profiles, max_results,<br/>page_limit, crawl_depth)"]
    SE["ScrapingEngine<br/>.run()"]

    BF["BFS Page Discovery<br/>(StateCache & Deduplication)"]
    SPE["Specialized Extractors<br/>(yt-dlp for heavy SPAs)"]
    AS["Asset Relevance Scoring<br/>& Quality Filters (filters.py)"]
    DLP["Download Pipeline<br/>(ThreadPool, Range Resumption, Pillow)"]

    SR["ScrapeResult<br/>→ results.json<br/>→ run_summary.json<br/>→ media files"]
    FD["FastAPI/HTMX Dashboard<br/>(frontend/app.py)"]

    SM --> P --> EO --> SE
    SE --> BF & SPE & AS & DLP
    BF --> SR
    SPE --> SR
    AS --> SR
    DLP --> SR
    SR --> FD
    FD -- Triggers Background Scrapes --> SE
```

---

## 2. Module Layout

```text
scrape-dashboard/
├── pyproject.toml               — Standard packaging setup & `scrape` entry point
├── run.bat / run.sh             — Unified Master Launcher (WebUI, Wizard, Auth, Autostart, Install)
├── run_monitor.bat / .sh        — Continuous Watchdog Agent launcher
├── docker-compose.yml           — Multi-container orchestration (Scraper + FlareSolverr)
├── requirements.txt             — Python dependencies
├── README.md                    — Primary documentation portal
│
├── crawlee_bridge/              — Node.js Express Bridge Server
│   ├── index.mjs                — Crawlee Cheerio & Puppeteer stealth servers
│   └── package.json             — got-scraping & puppeteer-extra-plugin-stealth
│
├── frontend/                    — Decoupled FastAPI + HTMX WebUI
│   ├── app.py                   — Lightweight FastAPI bootstrap, security headers, router mounting
│   ├── state.py                 — Shared state (task_state, log_buffer, process lock, broadcaster)
│   ├── static/                  — SVG logo, favicon, and CSS assets
│   ├── templates/               — HTMX dashboard templates (index.html, gallery.html)
│   └── routers/                 — Modular APIRouter packages:
│       ├── auth.py              — Basic auth & version verification
│       ├── dataset.py           — Dataset tagging, aesthetic scoring, cropping, LoRA/RAG export
│       ├── domain_config.py     — Domain configuration matrix CRUD
│       ├── gallery.py           — Media gallery browsing, pagination, deletion
│       ├── jobs.py              — Scraping execution, subprocess streaming & process controls
│       ├── notifications.py     — Notification channels and test ping endpoints
│       ├── seeds.py             — Seed Studio CRUD, validation, discovery, and linting
│       ├── settings.py          — System settings management and secret masking
│       ├── subject_profiles.py  — Subject profiles CRUD
│       ├── telemetry.py         — SSE streaming, system telemetry, engine metrics
│       ├── url_rules.py         — URL normalization rules CRUD
│       └── watchdog.py          — Continuous monitoring agent status & controls
│
├── src/                         — Python Source Core
│   ├── cli/                     — Primary CLI, interactive wizards, watchdog loop, seed studio
│   ├── config/                  — Canonical path anchoring (PROJECT_ROOT, DATA_DIR, PROFILES_DIR)
│   ├── core/                    — ScrapingEngine main orchestration, BFS crawling, parsing
│   ├── scraper/                 — Base Scraper classes, fallback logic
│   ├── plugins/                 — Platform-specific extractors (Booru, Civitai, Reddit, yt-dlp)
│   ├── captcha/                 — Universal CAPTCHA strategy providers
│   ├── ml/                      — AI tagging, cropping, LoRA exporting, Ollama vision
│   ├── monitoring/              — Hardware governor, structured telemetry
│   ├── network/                 — Tiered HTTP client, stealth pipeline, rate limiting
│   ├── notifications/           — Pluggable notification pipeline
│   └── storage/                 — SQLite WAL state caching, chunked downloading
│
├── tests/                       — Domain-Structured Automated Test Suite (458 Tests)
│   ├── conftest.py              — Global pytest fixtures, project_root resolution, network isolation
│   ├── mock_target_server.py    — Local ephemeral HTTP mock server for offline integration tests
│   ├── cli/                     — CLI launcher, wizards, preflight, release automation
│   ├── core/                    — Engine BFS, models, filters, budgets, jitter, circuit breakers
│   ├── frontend/                — WebUI endpoints, HTMX controls, SSE logs, telemetry streaming
│   ├── integration/             — E2E stealth pipelines, Seed Studio manifests, mock server flows
│   ├── ml/                      — Ollama vision, WD14 tagger, aesthetic scorer, smart cropper, RAG
│   ├── network/                 — HTTP client, TLS impersonation, proxies, CAPTCHA, browser pools
│   ├── notifications/           — Telegram bot, Discord, Slack, SMTP, Webhooks
│   ├── plugins/                 — Specialized extractors (Civitai, Booru, Instagram, Twitter, yt-dlp)
│   └── storage/                 — Downloader, chunked resumption, speed limiter, database backends
│
├── data/                        — JSON Configurations & Registries
│   ├── domain_config.json       — Rate limits, referer overrides, stealth_required, etc.
│   ├── url_normalisation_rules.json — Canonicalisation regex rules
│   └── blacklist.json           — Dynamic circuit breaker blacklist
│
├── seeds/                       — Per-subject seed manifest files (`.txt`)
└── docs/                        — Technical Documentation Portal
```

---

## 3. Core Engine Components

### 3.1 ScrapingEngine & Modular Managers (`src/core/`)

The core architecture is decoupled across specialized modules:

- **`CrawlOrchestrator`** (`src/core/orchestrator.py`): Manages the BFS queue, link extraction, page fetching thread pool, latency-aware dynamic concurrency adjustments, and per-domain rate limiting.
- **`MediaProcessor`** (`src/core/media_processor.py`): Evaluates discovered media links against `filters.py`, performs origin URL upscaling predictions, and enqueues qualified assets for download.
- **`DomainRulesManager`** (`src/core/domain_rules.py`): Aggregates domain profiles parsed from `SeedManifest` with dynamic settings from `data/domain_config.json`.

### 3.2 8-Tier WAF & Challenge Escalation Pipeline (`src/network/stealth/`)

When encountering 403, 401, or 429 responses, `HttpClient` automatically escalates through an 8-tier fallback chain governed by a **60-second execution deadline** and host memory caching.

```mermaid
flowchart LR
    T0["Tier 0<br/>httpx + Cookies"] --> T1["Tier 1<br/>Crawl4AI"]
    T1 --> T2["Tier 2<br/>Crawlee Cheerio"]
    T2 --> T3["Tier 3<br/>DrissionPage"]
    T3 --> T4["Tier 4<br/>Crawlee Puppeteer"]
    T4 --> T5["Tier 5<br/>Helium"]
    T5 --> T6["Tier 6<br/>Undetected Chromedriver"]
    T6 --> T7["Tier 7<br/>Camoufox"]
    T7 --> T8["Tier 8<br/>FlareSolverr"]
```

#### WAF Engine Overrides & Host Memory
- **Seed Manifest Annotations**: `# engine: <name>` forces a specific fallback engine to run first.
- **Host Engine Memory**: Successful solver choices are automatically cached per host and prioritized on subsequent requests.
- **Universal Captcha Strategy**: Delegates CAPTCHA solving to configured providers (`CapSolver`, `2Captcha`, `AntiCaptcha`) and caches tokens.
- **Camoufox Fingerprint Tuning**: Matches host OS platform, enables humanized cursor/scrolling, and escalates to visible headful mode for 20s if Turnstile challenge is detected on a GUI system.

#### FlareSolverr Service Integration
- Binds natively to `http://127.0.0.1:8191/v1`. Executes background Docker auto-start (`docker start flaresolverr`) if unreachable.
- Reuses domain-keyed browser sessions and enriches downstream CDN streaming media requests with session cookies.

#### Failure Models & Circuit Breakers (Fast-Fail)
To prevent infinite hanging on dead/blocked domains:
- **Consecutive Error Cutoff**: If a host triggers **3 consecutive request errors** (e.g., timeouts, strict WAF blocks), the domain is marked as failed. Remaining queued items for that domain are skipped instantly.
- **Auth Wall Redirect Cutoff**: Redirects to authentication paths (`/login`, `/signin`) trigger immediate domain cutoff.
- **Cloudflare Fast-Fail Pre-Registration**: Domains annotated with `# cloudflare: true` skip browser fallback loops instantly on 403/429.

- **Auth Wall Redirect Cutoff**: Redirects to authentication paths (`/login`, `/signin`) trigger immediate domain cutoff.
- **Cloudflare Fast-Fail Pre-Registration**: Domains annotated with `# cloudflare: true` skip browser fallback loops instantly on 403/429.

### 3.3 Dual Governor: AIMD & Hardware Load Coordination (`src/core/governor.py`, `src/monitoring/hardware_governor.py`)

The engine couples host-level network health with host-level hardware resource constraints:
- **AIMD Dynamic Concurrency Auto-Tuning**:
  - **Additive Increase**: Increases host concurrency window additively ($+1.0$) upon successful requests with healthy latency ($\le 1.5$s), scaling up to `--workers`.
  - **Multiplicative Decrease**: Throttles host window multiplicatively ($\times 0.5$) upon 429 rate limits, network errors, or severe latency spikes ($> 3.0$s), down to `min_concurrency=1`.
- **Hardware Load Governor Modulation**:
  - Real-time CPU % and available RAM % polling via `psutil`.
  - **High Load** (CPU $\ge 85.0\%$, RAM Avail $\le 15.0\%$): Throttles worker multiplier to 0.50x.
  - **Critical Load** (CPU $\ge 95.0\%$, RAM Avail $\le 5.0\%$): Throttles worker multiplier to 0.25x and triggers proactive `gc.collect()`.
- **Effective Concurrency**: Computed as `max(1, int(aimd_window * hw_scale_factor))`.

### 3.4 Ultra-Resilient Network & Stealth Core (`src/network/proxy_manager.py`, `src/network/http_client.py`)

- **Sticky TLS Impersonation Profiles**: Retains domain-consistent TLS fingerprints (`chrome120`, `chrome124`, `chrome131`, `safari17_0`, `safari18_0`, `firefox133`, `edge124`) using `curl_cffi` to bypass JA3/JA4 anomaly detection, rotating dynamically on challenge escalation.
- **Dynamic Proxy Health Scoring & Tiered Quarantine Ring**:
  - Exponential Moving Average (EMA) latency tracking ($\alpha = 0.2$).
  - Dynamic health scores $S \in [0.0, 1.0]$ factoring latency, success rate, and consecutive errors.
  - Tiered quarantine backoff with exponential penalty ($300 \times 2^{\min(4, \text{failures}-3)}$ seconds) and single-probe recovery states before reinstatement.
- **Domain Reputation Tracking**: Dynamically computes reputation $R \in [0.1, 1.0]$ to scale base request delays and rate limiter jitter.

### 3.5 Next-Gen Media Extraction Pipeline (`src/core/media_processor.py`, `src/core/microdata.py`, `src/storage/downloader/manager.py`)

- **Multi-Source Candidate Extraction**: Parses primary images alongside alternative resolutions from `srcset`, zoom attributes (`data-zoom-image`, `data-highres`, `data-original`), and parent link hrefs.
- **Schema.org JSON-LD Microdata**: Extracts structured media objects (`ImageObject`, `VideoObject`, `Product`, `Article`, `Recipe`, `@graph`) and auto-populates fallback candidate sets.
- **Automated Fallback Candidate Traversal**: When a primary candidate yields HTTP 404, 403, 410, or network failure, the downloader automatically walks candidate fallbacks without dropping the scrape record.
- **Parallel Multi-Chunk Range Downloader**: Assets exceeding 20 MB with `Accept-Ranges: bytes` support are split into concurrent byte-range worker streams and reassembled in-place.
- **Smart Pagination Detection**: Detects `<link rel="next">`, `<a rel="next">`, structured pagination elements, and query/path stepping patterns (`?page=N`, `/page/N/`).

### 3.6 High-Throughput State & Storage Core (`src/storage/bloom_filter.py`, `src/storage/state_cache.py`)

- **Zero-Dependency Bitmask Bloom Filter**: Pure Python bitmask implementation using 64-bit integer bitwise operations and Murmur-inspired multi-hash mixing for $O(1)$ in-memory L1 cache rejection before hitting SQLite disk queries.
- **Write-Staging Buffer & Batch Transactions**: URL markers are staged in memory and flushed via multi-row chunked `executemany` transactions upon reaching buffer thresholds or timeouts, reducing SQLite write lock contention.
- **Persistent SQLite WAL State Cache**: Uses `PRAGMA journal_mode=WAL;` and `PRAGMA synchronous=NORMAL;`. Auto-syncs Bloom filter state across manual purges and TTL cleanups.


---

## 4. Security & Static Analysis (CodeQL & Semgrep)

The project employs strict structural mitigations against vulnerabilities like Path Injection (`py/path-injection`), avoiding manual `# codeql` suppressions:
1. **Untainted Root Generation**: Dynamically rebuilds the base drive (`os.path.splitdrive`).
2. **Absolute Normalization**: Forces input paths through `os.path.abspath(os.path.normpath())`.
3. **Prefix Boundary Enforcement**: Checks bounds via `.startswith(safe_root)`.

---

## 5. Docker Architecture

When deploying in containerized environments:
- Enforces `PUPPETEER_SKIP_DOWNLOAD=true` to prevent redundant Chromium downloads during build.
- Configures `PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium` to bind system Chromium directly to Node.js Crawlee operations without browser version conflicts.
- Runs under non-root `USER appuser` with permissions pre-configured for `data`, `seeds`, `logs`, and `output`.

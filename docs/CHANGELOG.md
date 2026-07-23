# Changelog

## [0.17.1] — 2026-07-22

### Added & Changed (0.17.1)

- **Vector Branding & System Tray Integration** (`frontend/templates/index.html`, `src/cli/launcher.py`): Integrated custom vector SVG branding across the web dashboard and CLI wizard headers. Added inline SVG data URI favicon `<head>` loading for zero-static-file dependencies, and engineered a hand-drawn, high-contrast PIL system tray icon (`create_icon_image()`, RGBA 64×64) tuned for 16px/24px Windows taskbar readability.
- **Context-Aware Dashboard Telemetry** (`frontend/app.py`, `frontend/templates/index.html`): Upgraded top stat cards (`SUBJ.RUNS`, `ASSET.IMG`, `ASSET.VID`, `TARGETS.SCAN`) to dynamically switch between global cumulative totals on the Command Center and per-subject scoped totals on the Media Vault view (with a `/ N total` global comparison sub-line). Fixed disk-based media counting to scan actual files across `output/<subject>/runs/*/` instead of relying on missing `results.json` keys. Added `/htmx/subject-stats` endpoint.
- **Tactical Sidebar & Navigation Overhaul**: Redesigned the left sidebar header with a centered 72×72px glowing vector logo, clean `scrAPE` text, and `v0.17.0` version badge. Re-aligned the Subjects Vault list to left-aligned cards with custom 6×6px indicator dots (`box-shadow` active glow). Upgraded the `COMMAND CENTER` button with a 4-square grid dashboard SVG icon, active state orange tint (`rgba(255, 85, 0, 0.08)`), and high-tech typography.
- **Form Tooltips & Hardware Concurrency Warning**: Re-organized scrape configuration fields by moving verbose parameter descriptions into interactive `[?]` hover tooltips. Integrated a dynamic client-side validator (`validateSafetyThresholds()`) that alerts users when specifying concurrency settings above safe hardware limits (>16 scrapers, >24 download threads).
- **CLI & Environment Compatibility Patches**: Replaced legacy `os.system` calls across CLI modules with `subprocess.run(..., shell=True)` for Python 3.12/3.13 deprecation compliance. Added Pillow version fallback checks for system tray icon resampling (`Image.Resampling.LANCZOS` / `Image.LANCZOS` with Pyright static type-checker compliance). Replaced ASCII banners with clean text headers in `cli_wizard.py` and `README.md`.

## [0.17.0] — 2026-07-21

### Added & Changed (0.17.0)

- **Interactive Brutalist WebUI & CLI Flags Integration** (`frontend/templates/index.html`, `frontend/app.py`): Rebuilt the layout dashboard with strict high-contrast brutalist aesthetics (zero border-radius, heavy dropshadows, grain textures, Oswald/JetBrains Mono fonts, and neon orange/green highlighting). Mapped all 20+ advanced scraper options (concurrency, proxy details, subtrees, force flags, state cache exclusions, cache wipe controls) into front-end fieldsets.
- **Dynamic Help Tooltips**: Placed inline `[?]` help indicators with CSS-only hovered popup labels over all legend boxes, subsection titles, and config inputs.
- **Sidebar & Media Gallery Routing Fixes**: Standardized sidebar items to trigger JS `selectSubject()` routes and set `hx-trigger="load"` on the gallery grid dynamically. Fixes loading bugs so that clicked subjects display their images/videos immediately. Patched glob paths to load domain-grouped folder structures recursively (`*/images/**/*.*`).
- **Live Terminal & Telemetry Formatting**: Enabled vertical resizability on the log console. Cleans output lines by splitting on carriage returns (`\r`) to isolate tqdm download progress logs. Colors vertical borders of log lines based on severity log levels (`log-info`, `log-warning`, `log-error`, `log-debug`).
- **Playwright Automated Testing Suite** (`tests/test_frontend_ux.py`): Built a comprehensive E2E, modular, and flow testing suite to verify styling configurations, tooltips content, active metrics polling, and run-form thread initiations.
- **Standard Python Packaging (`pyproject.toml`)**: Added standard build configuration to compile the workspace and register the global `scrape` console script entry point.
- **One-Click Windows Installer (`install.bat`)**: Added a global installer script that compiles the package in editable mode (`pip install -e .`) and registers `scrape` on the user's terminal path.
- **Self-Bootstrapping CLI Launcher (`src/cli/launcher.py`)**: Added checks at launcher startup to automatically execute `npm install` for `crawlee_bridge` and `playwright install chromium` if system dependencies are not detected. Swapped broken webui imports with the new FastAPI instance (`frontend.app:app`) and added a 9Router-style status message for background tray operations.
- **Instant Unlimited Run Preset Toggle** (`frontend/templates/index.html`): Added a Brutalist mode selector bar at the top of the form (`[ CUSTOM CONFIGURATION ]` vs `[ INSTANT UNLIMITED RUN ]`). Selecting "unlimited" automatically hides all 20+ advanced configuration options/fieldsets (hiding the visual noise) and populates the background inputs with high-performance, unlimited crawler thresholds for quick, hassle-free executions.

## [0.16.0] — 2026-07-21

### Added & Changed (0.16.0)

- **Resumable Media Downloads (Range Retries)** (`src/storage/file_downloader.py`): Integrated HTTP `Range` request support (`bytes=X-`) for chunk-based downloads. If a download is interrupted, it checks for existing `.tmp` files and requests the remainder (HTTP 206 Partial Content). Handles standard HTTP 200 responses by truncating and re-downloading, and unlinks corrupted/invalid chunks on HTTP 416 (Range Not Satisfiable).
- **Post-Download Integrity Verification**: Moved SHA-256 hash calculation from streaming chunk iteration in memory to post-download disk-based reading. This guarantees correct file integrity validation across multiple resume iterations.
- **WAF & Auth Wall Cutoff Circuit Breakers** (`src/core/managers.py`, `src/utils/http_client.py`): Prevents thread hangs and wasted resources on protected domains by halting crawling on a domain after 3 consecutive worker errors or upon redirection to authentication routes (`/login`, `/signin`, `/signup`, `/auth`).
- **Low-Resolution Path Pre-Filtering** (`src/core/filters.py`): Optimized link extraction by running `has_low_res_path_pattern` pre-filtering (checking for `/320x180/` screenshots and similar patterns) directly inside `is_thumbnail_url()`, avoiding scheduling and downloading low-resolution frame screenshots.
- **Testing Suite Expansion** (`tests/test_resumable_downloads.py`): Created dedicated unit tests verifying append (206), overwrite (200), and invalid range retry (416) behaviors. Expanded test suite coverage to 100 tests.

## [0.15.0] — 2026-07-19

### Added & Changed (0.15.0)

- **Dynamic HTMX Frontend Integration** (`frontend/app.py`, `frontend/templates/`): Transformed the static output gallery into a fully live, HTMX-powered command center. Features include real-time OS hardware telemetry (CPU, RAM, Disk) via auto-polling, dynamic abort controls to forcibly kill scraping threads, and native file management (delete local files or open them in Windows Explorer) directly from the WebUI.
- **Frontend Codebase Reorganization** (`frontend/`): Decoupled all WebUI routing, HTML templates, and interface logic from the core `src/cli/` backend engine into a pristine, top-level `frontend/` directory. Added a robust `run_frontend.bat` shortcut to rapidly launch the dashboard.
- **Core Engine Decoupling** (`src/core/managers.py`): Extracted `DomainRulesManager`, `MediaProcessor`, and `CrawlOrchestrator` from `engine.py` into a dedicated `managers.py` module to improve separation of concerns, reduce file complexity, and fix circular import issues.

## [0.14.0] — 2026-07-17

### Added & Changed (0.14.0)

- **SQLite WAL Concurrency Optimization** (`src/storage/state_cache.py`): Upgraded the `StateCache` SQLite connection to use Write-Ahead Logging (`PRAGMA journal_mode=WAL;`). This eliminates disk I/O lock contention during massive multi-threaded crawls, significantly increasing concurrency throughput.
- **Secure Local Session Storage** (`src/utils/session.py`): Hardened harvested cookie storage by enforcing strict Unix file permissions (`0o600` for files, `0o700` for the `data/sessions` directory), securing authenticated sessions against local privilege escalation or unauthorized read access.
- **Network Isolation & Path Sanitization** (`crawlee_bridge/index.mjs`, `src/cli/webui.py`): Explicitly bound the Node.js `crawlee_bridge` proxy to `127.0.0.1` to prevent exposure on local networks. Added strict path validation in the FastAPI web UI to prevent directory traversal attacks when loading seed files.

## [0.13.0] — 2026-07-17

### Added (0.13.0)

- **Crawlee Node.js Bridge Integration** (`crawlee_bridge/index.mjs`, `src/utils/crawlee_client.py`): Integrated Apify's Crawlee via a local Express bridge server to drastically improve TLS fingerprint spoofing and stealth extraction capabilities. Added two new robust fallback tiers: `Crawlee Cheerio` (fast static TLS spoofing via `got-scraping`) and `Crawlee Puppeteer` (heavy JS-rendering with stealth plugins).
- **Expanded 7-Tier WAF Fallback Pipeline** (`src/utils/http_client.py`): Redesigned the `HttpClient` fallback system into a comprehensive 7-tier escalation chain (`Local Cookies` -> `Crawlee Cheerio` -> `Crawl4AI` -> `DrissionPage` -> `Crawlee Puppeteer` -> `Helium` -> `undetected-chromedriver`) to systematically defeat WAFs, Cloudflare Turnstile, and heavy browser fingerprinting.
- **Robust Empty-Page Cloudflare Detection**: Patched a critical issue where empty HTML bodies returned from 403 Cloudflare challenges were incorrectly evaluated as successful responses, ensuring the scraper always falls through to heavier browser tiers when encountering aggressive anti-bot protections.

## [0.12.0] — 2026-07-17

### Added (0.12.0)

- **Dynamic Plugin Architecture** (`src/scraper/specialized.py`, `src/plugins/`): Refactored the core `SpecializedExtractor` into a scalable, class-based dynamic plugin architecture. Custom platform extraction logic (e.g., YouTube, Reddit) is now seamlessly loaded at runtime from independent plugin files in `src/plugins`, vastly improving maintainability and isolation.
- **Aggressive Image Sanitization** (`src/storage/file_downloader.py`, `requirements.txt`): Integrated `Pillow` into the media downloader pipeline. All downloaded images are now intercepted in memory, parsed, and entirely re-encoded. This process automatically drops embedded EXIF metadata (GPS, device data) and explicitly guards against malicious polyglot file payloads by verifying legitimate image structure before writing to disk.
- **Frontend Aesthetic Redesign** (`src/frontend_builder/builder.py`): Evolved the dashboard UI towards a bespoke "Primal Computation / Evolutionary Brutalism" design language. Overhauled the generated `index.html` to leverage strict monochrome contrast, heavy brutalist UI components, and wide typography.
- **Interactive Authentication CLI** (`src/cli/auth.py`, `src/cli/main.py`): Added `--login <DOMAIN>` for launching a headful `undetected_chromedriver` browser to manually log into protected sites and save session cookies. Added `--inject-cookies <FILE> --domain <DOMAIN>` to import session cookies from JSON or Netscape `cookies.txt` formats directly into the SessionManager.

## [0.11.0] — 2026-07-17

### Changed & Fixed (0.11.0)

- **Architectural Reorganization** (`src/cli/`, `src/config/`): Moved primary entry points (`main.py`, `cli_wizard.py`, `monitor_agent.py`) and configuration constants into dedicated packages within `src/` to formalize the project layout as a proper Python package.
- **Dynamic Path Resolution**: Refactored module imports and `sys.path` injections across CLI scripts to use robust absolute paths derived from `__file__`, resolving module loading errors during subprocess execution.
- **Test Suite Hardening**: Fixed infinite test hangs in `tests/test_advanced_features.py` by scoping `time.monotonic` mocks to avoid blocking `concurrent.futures.wait`. Also patched unmocked live network requests that caused rate-limiting and hanging during testing.
- **Import Hygiene & Code Cleanup**: Resolved `E402` and `F841` linting errors across the codebase via `ruff`, removed duplicate methods in `ScrapingEngine`, and achieved a 100% pass rate for the 91-item test suite.
- **Shell Wrapper Updates**: Updated `run.bat`, `run.sh`, `run_monitor.bat`, and `run_monitor.sh` to target the new entry points in `src/cli/`.

## [0.10.0] — 2026-07-16

### Added (0.10.0)

- **Continuous Watchdog Agent** (`monitor_agent.py`, `state_cache.py`): Added a long-running watchdog mode for continuous scheduled monitoring. Introduced an SQLite-backed `StateCache` to persist processed URLs across runs, preventing redundant downloads and bandwidth waste.
- **Undetected-Chromedriver (UC) Tier-3 Fallback** (`http_client.py`): Upgraded the stealth pipeline. When Cloudflare Turnstile blocks `Crawl4AI` and `DrissionPage`, the client now falls back to a fully randomized `undetected-chromedriver` instance. Includes robust process lifecycle management to avoid zombie Chrome instances.
- **Specialized Social Media Extractors** (`specialized.py`, `engine.py`): Bypassed heavy headless browser rendering for complex SPAs (YouTube, TikTok, Reddit) by routing them directly to `yt-dlp` and API extractors. Vastly increases extraction speed and success rates on media platforms.
- **Resolution Upscaling & Fallback** (`filters.py`, `file_downloader.py`): Implemented heuristic resolution upscaling (`transform_to_highres`) to automatically strip thumbnail parameters (e.g. WordPress, Twitter small tags) and predict the full-size origin URL. The downloader attempts the high-res link first and transparently falls back to the original scraped URL on a 404 error.
- **Static Dashboard Generator** (`builder.py`, `cli_wizard.py`): Created a zero-dependency HTML/JS/CSS static site builder. It runs automatically at the end of scraping operations, generating a sleek, responsive visual gallery and monitoring dashboard in `output/index.html`.
- **GitHub Pages Auto-Deployment** (`gh-pages.yml`): Added a GitHub Actions workflow to automatically publish the `output/` directory as a GitHub Pages site upon push to `main`.

## [0.9.0] — 2026-07-15

### Added (0.9.0)

- **Decoupled Concurrency Scaling** (`engine.py`, `http_client.py`): Re-engineered the adaptive concurrency scaler to throttle workers based on per-thread pure network latency (excluding rate-limiter delays). This isolates domain-specific latency so that slow/throttled hosts do not globally degrade crawlers on fast domains.
- **Parallelized Media Downloads** (`file_downloader.py`, `engine.py`): Decoupled download rate-limiting from crawling rate-limiters. Media files hosted on CDN domains bypass rate-limit locks entirely. Non-CDN assets utilize independent, fast (5 req/s) per-domain downloader rate-limiters, permitting parallel media fetches across downloader threads.
- **Robots.txt Cooldown Immunity** (`robots.py`): Modified the Robots Checker to report a successful `robots.txt` parse back to the domain's HTTP cooldown state, preventing transient robots.txt blocks from building up failure counts that trigger domain-wide cooldowns.
- **Startup WAF Pre-registration** (`engine.py`): Automated registration of target domains annotated as Cloudflare-blocked at startup, forcing immediate fail-fast behavior on Turnstile-protected targets to prevent fallback timeout hangs.
- **Support for Pre-filtering Dimensions on Seed Level**: Supported annotating seed configurations to filter images by size (e.g. `min_image_size`) directly during crawl/evaluation, saving download resources by rejecting thumbnails before retrieval.

## [0.8.0] — 2026-07-14

### Added

- **AI-Focused CLI Wizard & Ingestion Utilities** (`cli_wizard.py`): Updated the terminal GUI to act as a **high-efficiency fuel pump for AI**. Added two new dedicated modes:
  - **Create Structured AI Dataset (Mode 4)**: Consolidates and groups downloaded assets from completed runs into structured formats (Flat, Domain-grouped, or Media-type grouped subfolders).
  - **Enterprise LLM RAG Ingestion Helper (Mode 5)**: Extracts page titles, alt texts, image contexts, and URLs from runs, exporting them as consolidated markdown docs, chunked page-level `.md` files, or JSONL embedding records for Vector DB ingestion.

- **`cloudflare_blocked` domain flag** (`seed_manifest.py`, `http_client.py`, `main.py`): New `DomainProfile` field parsed from `# cloudflare: true` seed annotation. When set, `HttpClient` raises `ScraperBypassError` immediately on 403/429 for that domain, skipping both Tier-1 and Tier-2 Crawl4AI browser runs entirely. Eliminates the ~25s per-page waste on domains protected by Cloudflare Turnstile that defeat all browser tiers. Registered automatically at startup via `HttpClient.register_cloudflare_blocked()`.

- **`max_pages` per-domain cap** (`seed_manifest.py`, `engine.py`): New `DomainProfile` field parsed from `# max_pages: N` seed annotation. The engine enforces a hard page-count ceiling per domain per run, preventing over-crawling of low-yield sources. Page is skipped with status `"max_pages_capped"` before any HTTP request is issued.

- **JSON-driven URL normalisation rules** (`data/url_normalisation_rules.json`, `config.py`): URL normalisation patterns are no longer hardcoded in any Python source file. `config.URL_NORMALISATION_RULES` is now populated at startup from `data/url_normalisation_rules.json`. Each rule is a `{ "pattern": "<regex>", "replacement": "<str>", "description": "..." }` object compiled to a `(re.Pattern, str)` tuple. Add new rules to the JSON file only.

- **Locale-collapse normalisation** (`data/url_normalisation_rules.json`): First entry in the new rules file. Strips the 2-character locale segment (`/de/`, `/fr/`, `/zh/`, etc.) from `get_file`/`contents`/`video` paths so all locale variants of the same video resolve to one canonical URL before entering the crawl queue. Prevents duplicate download requests per run.

- **`normalise_url()` re-export** (`http_client.py`): Kept as a thin delegation to `core.filters.normalize_url` for backward compatibility with existing call sites. All normalisation logic is now canonically in `filters.py`.

### Changed

- **`normalize_url()` extended** (`core/filters.py`): Now applies all rules from `config.URL_NORMALISATION_RULES` before standard URL canonicalisation (unquote → re-quote → strip fragment). No domain-specific knowledge embedded in the function body.

- **`_load_dynamic_config()` unified** (`config.py`): Merged domain config loading and URL normalisation rule loading into a single startup function. `url_normalisation_rules.json` is loaded alongside `domain_config.json`.

- **Seed file overhaul — Example Subject 1** (`seeds/example1.txt`):
  - Disabled zero-yield domains: `example-leak.vip` (0/11 pages), `example-folder.com` (CDN-only), `example-dead.net` (dead), `example-gallery.org` (JS-only gallery)
  - Added `cloudflare: true` + `Rate-limit: 0.1 req/s` to `example-protected.com`
  - Reduced rate limit `0.3 → 0.1 req/s` for `example-slow.com`
  - Added `max_pages: 5` cap to `example-capped.net` (previously 26 pages → 2 images)
  - Pruned 2 dead `example-stream.live` CDN URLs from `example-mobile.mobi` detail seeds

- **Seed file overhaul — Example Subject 2** (`seeds/example2.txt`):
  - Disabled auth-walled domains: `www.example-art.net`, `example.fanbox.cc`, `example-kemono.cr`, `example-archive.st`
  - Changed crawl strategy `direct → index→detail` for `example-rule.us`, `example-rule.world` — listing pages serve 256px thumbnails only; detail pages contain full-res CDN links

### System Limitations (documented)

- **Cloudflare Turnstile**: Domains protected by Turnstile (interactive JS challenge) cannot be bypassed by any automated tier including headful Crawl4AI. Mark these with `# cloudflare: true` in the seed file to avoid wasting fallback time.
- **Auth-walled sources**: specific sites are disabled pending a session-cookie injection workflow. These are high-value sources but require authenticated sessions that the current HTTP client does not support automatically.

## [0.7.0] — 2026-07-12

### Added (0.7.0)

- **Persistent Blacklist**: Active domain-level blacklisting (`src/utils/blacklist.py`) for domains consistently returning HTTP 404/403/Cloudflare challenge errors.
- **Session Persistence**: Implemented `SessionManager` (`src/utils/session.py`) for caching and loading cookies across run sessions.
- **Dynamic Domain Configurations**: Replaced hardcoded domains in `src/config.py` and `src/core/engine.py` with dynamic loaded configuration profiles from `data/domain_config.json`.
- **Dynamic Referer and Header Overrides**: Decoupled domain-specific HTTP header bypasses into the `referer_overrides` mapping in `data/domain_config.json`.
- **Dynamic Blacklisting Circuit Breaker Persistence**: Integrated domain blacklisting hooks (`add_to_blacklist`) with `HttpClient`'s 429 and error-rate circuit breaker thresholds, saving domain bans to the persistent JSON blacklist dynamically.
- **Fast-fail broken media URLs**: Added `is_broken_media_url` to quickly bypass placeholder, 404, or empty media links without making HTTP requests.
- **Pre-flight HEAD Checks**: Integrated validation HEAD requests in `MediaDownloader` (`src/storage/file_downloader.py`) to verify media exists before streaming downloads, significantly reducing bandwidth and error logging.
- **Aggressive Throttling & Deprioritization**: Configured crawler state to permanently deprioritize/throttle domains with extremely low yields (<2% after 20 pages).

### Fixed

- **Google Images NameError**: Added missing import of `is_thumbnail_url` in `_extract_media_from_json` within `src/scraper/google_images.py`.

## [Unreleased]

### Added (Unreleased)

- Seed manifest parser (`src/core/seed_manifest.py`): `# Rate-limit:` and `# skip-link-discovery` annotations
- `DomainProfile` fields: `min_image_size`, `thumbnail_prefix_pattern`, `requires_referer`
- Quality filter functions: `safe_join()`, `has_low_res_path_pattern()`, `_video_resolution_hint()`
- Engine: `has_low_res_path_pattern` / `thumbnail_prefix_pattern` checks in BFS loop, `RLock` for `add_rejected()`, `add_rejected()` dedup + count, `run_metadata` + `duration_seconds` in `ScrapeResult`
- Downloader: `referer`, `min_image_size`, `thumbnail_prefix_pattern` support in `_download_file`
- Robots: netloc caching via `self._parsers` dict
- **Tests**: Mock signatures updated; new tests for `safe_join`, `has_low_res_path_pattern`, `_video_resolution_hint`, dedup rejection counting

### Fixed (Unreleased)

- None-current `" ".join(...)` calls in filters replaced with `safe_join()` guard against None field concatenation
- Deadlock potential in engine.py resolved: `Lock` → `RLock` for nested critical sections
- Robots.txt cache: `@lru_cache` → per-netloc dict (`self._parsers`) for thread-safety

### Changed (Unreleased)

- `_download_file` signature expanded to accept `referer`, `min_image_size`, `thumbnail_prefix_pattern`
- Engine `_scrape_images` passes domain-level `min_image_size` / `thumbnail_prefix_pattern` to downloader
- Main entry stores `duration_seconds` via `time.monotonic()` and `run_metadata` dict on each result

### Security / Repository Hygiene

- `.gitignore` streamlined for production sweeps (block scratch files, temp logs, run outputs)
- Documentation updated: `README.md`, `ARCHITECTURE.md`, `USAGE.md`, `QUALITY_FILTERS.md`, `SCENARIOS.md`

## [0.6.0] — 2026-07-08

### Added (0.6.0)

- Full run analysis scripts and pipeline review infrastructure
- Fixed corrupt seed manifest file encoding (unicode arrows → ASCII-safe delimiters)
- Streamlined main.py pipeline logging and error handling

## 2026-07-10 — Seed Manifest Hardening & Quality Filters

## 2026-07-08 — Full Run Optimization & Seed Parsing Fixes

## [0.5.0] — 2026-07-07

### Added (0.5.0)

- Test suite for performance quality features (`test_performance_quality_features.py`): zero-yield cutoff, low-yield threshold, path-based low-res detection, robots cache
- Test suite for audit trail (`test_audit_trail.py`): default audit fields, engine in-place mapping, stealth timed block, shopping/json filters, CSV columns
- Advanced async HTTP session handling (`test_advanced_features.py`): sticky cookies rotation, adaptive throttling, circuit breaker
- Stealth circuit breaker tests (`test_stealth_circuit_breaker.py`): fallback to Crawl4AI after repeated 429s
- **Quality filters**: yield-based domain filtering, low-yield detection at 30% threshold
- **Robots checker**: 404 fast-fail, netloc-scoped parser cache
- **Post-run report**: full dump of metadata (workers, page limit, crawl depth, max results, entity tokens, download flag)

## [0.4.0] — 2026-07-05

### Added (0.4.0)

- Enhanced image dimension extraction (JPEG, PNG, GIF, WebP all variants)
- `parse_srcset` for highest-res selection
- JSON API media extraction
- Session pool with sticky cookies and rotation against blocks
- Adaptive concurrency throttling on HTTP 429
- Self-healing semantic selectors fallback chain
- Shopping/media site link extraction (Pinterest, Instagram, Flickr, Etsy, etc.)
- `crawl4ai` fallback for JS-rendered pages
- **Download retries**: configurable via `tenacity` with exponential backoff, network/server error separation
- **Stream downloader**: early-abort on invalid headers (content-type, content-length)
- **Stealth mode**: multi-session rotation, cookie jar isolation, configurable user-agent pool
- **Tests**: download retry, stealth mode, enhanced features, advanced crawl scenarios

## [0.3.0] — 2026-07-04

### Added (0.3.0)

- Seed manifest profile gating and annotation parsing
- Domain-level keyword gating (type + crawl strategy isolation)
- Normalized URL deduplication via `normalize_media_url()`
- Detail-page heuristic for link category classification
- Cross-run run-id tracking and run-persistence in output path

## [0.2.0] — 2026-07-02

### Added (0.2.0)

- Collective page scanning with multi-worker thread pools
- Deduplicated running-seen URL set (norm key, considered printed key)
- Active middleware-like page link extraction + discovery pipeline
- Fixed pagination limit parsing for per-domain page caps
- Intermediate hop middleware for video-scraping layout-skip handling
- Per-domain robots.txt parsing (with `--ignore-robots` override)

## [0.1.0] — 2026-06-28

### Added (0.1.0)

- Scraping engine (BFS crawl, scoring, download orchestration)
- Filters: relevance scoring, rejection reasons, low-res detection via query params
- File downloader: HTTP fetch with retries, image dimension validation
- Seed manifest: basic DomainProfile model, from_file loading with URL expansion
- CLI entry point: main.py with keyword/seed/max-results/output-dir
- Output: manifest.json generation with page reports, kept lists, domain stats, error counts
- CLI wizard (cli_wizard.py) for interactive configuration
- Seed file `seed.txt` for default/demo runs
- run.bat launcher
- Initial `.gitignore` for Python projects and generated artifacts
- Documentation: README.md, USAGE.md, ARCHITECTURE.md, QUALITY_FILTERS.md, SCENARIOS.md, CHANGELOG.md

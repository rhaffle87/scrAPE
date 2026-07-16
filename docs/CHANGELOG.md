# Changelog

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

- **AsianViralHub locale-collapse normalisation** (`data/url_normalisation_rules.json`): First entry in the new rules file. Strips the 2-character locale segment (`/de/`, `/fr/`, `/zh/`, etc.) from AsianViralHub `get_file`/`contents`/`video` paths so all 9 locale variants of the same video resolve to one canonical URL before entering the crawl queue. Prevents ~72 duplicate download requests per meenfox run.

- **`normalise_url()` re-export** (`http_client.py`): Kept as a thin delegation to `core.filters.normalize_url` for backward compatibility with existing call sites. All normalisation logic is now canonically in `filters.py`.

### Changed

- **`normalize_url()` extended** (`core/filters.py`): Now applies all rules from `config.URL_NORMALISATION_RULES` before standard URL canonicalisation (unquote → re-quote → strip fragment). No domain-specific knowledge embedded in the function body.

- **`_load_dynamic_config()` unified** (`config.py`): Merged domain config loading and URL normalisation rule loading into a single startup function. `url_normalisation_rules.json` is loaded alongside `domain_config.json`.

- **Seed file overhaul — meenfox** (`seeds/meenfox.txt`):
  - Disabled zero-yield domains: `hotleak.vip` (0/11 pages), `sorafolder.com` (CDN-only), `oneprotests.thefap.net` (dead), `e-hentai.org` (JS-only gallery)
  - Added `cloudflare: true` + `Rate-limit: 0.1 req/s` to `cosplaythots.com`
  - Reduced rate limit `0.3 → 0.1 req/s` for `cosplayrule34.com`
  - Added `max_pages: 5` cap to `pornasia.net` (previously 26 pages → 2 images)
  - Pruned 2 dead `dogestream.live` CDN URLs from `indoporn.mobi` detail seeds

- **Seed file overhaul — eatwaffles** (`seeds/eatwaffles.txt`):
  - Disabled auth-walled domains: `www.pixiv.net`, `eatwaffles.fanbox.cc`, `kemono.cr`, `pawchive.st`
  - Changed crawl strategy `direct → index→detail` for `rule34.us`, `rule34.world`, `rule34.xyz`, `kusowanka.com` — listing pages serve 256px thumbnails only; detail pages contain full-res CDN links

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

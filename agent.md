# agent.md — scrAPE Operator Guide

You are maintaining a media scraping system. Your job is to run it, read the results, figure out what went wrong or underperformed, fix it, and run it again. Repeat until quality stabilizes.

## Project Layout

```text
src/cli/main.py                     — CLI entry point, all flags documented via --help
src/cli/monitor_agent.py            — Watchdog entry point, continuous monitoring loop
src/cli/cli_wizard.py               — Interactive wizard for standard & watchdog runs
src/config.py               — Tunable constants (timeouts, concurrency, thresholds)
src/core/engine.py          — BFS crawl loop, page scoring, domain stats
src/core/filters.py         — URL classification, media detection, relevance scoring
src/core/models.py          — ScrapeResult, ImageItem, VideoItem dataclasses
src/scraper/google_images.py — Search provider + page scraper + link/media extraction
src/storage/file_downloader.py — Concurrent media downloader with MIME/size validation
src/utils/http_client.py    — Rate limiting, session pooling, 429 circuit breaker, Crawlee, Crawl4AI, DrissionPage & UC fallbacks
src/utils/blacklist.py      — Persistent domain blacklist (data/blacklist.json)
src/utils/session.py        — Persistent cookie cache (data/sessions/)
src/utils/session_pool.py   — Per-domain sticky sessions with disk persistence
src/utils/crawlee_client.py — Python bridge client for Node.js Crawlee operations
crawlee_bridge/             — Node.js Express server running Cheerio/Puppeteer stealth modes
data/domain_config.json     — Dynamic domain overrides (rate limits, referer, hotlink, deep scrape)
data/url_normalisation_rules.json — URL canonicalisation rules loaded into config.URL_NORMALISATION_RULES
src/config/subject_profiles.json — Subject profile presets (priority domains, max results)
seeds/                      — Per-subject seed manifest files (.txt)
output/<subject>/runs/<run_id>/ — Run output (results.json, domain_report.json, CSVs)
frontend/app.py             — Interactive FastAPI/HTMX dashboard server
frontend/templates/index.html — Brutalist WebUI dashboard template
run_frontend.bat            — Startup script for the interactive dashboard
output/cache/state_cache.db — SQLite database persisting processed URLs across watchdog runs
logs/run_<run_id>.log       — Full structured log per run
```

## The Loop

### 1. Run

```powershell
# Full production run with seed file
python src/cli/main.py --keyword "<subject>" --seed seeds/<subject>.txt ^
  --max-results 200 --workers 12 --dl-workers 16 ^
  --page-limit 300 --crawl-depth 3 --download-media

# Quick validation run (no downloads, low limits)
python src/cli/main.py --keyword "<subject>" --seed seeds/<subject>.txt ^
  --max-results 10 --page-limit 20 --crawl-depth 1

# Run without seeds (search-only discovery)
python src/cli/main.py --keyword "<subject>" --max-results 50 --page-limit 100

# Continuous Watchdog Agent (long-running with state cache)
python src/cli/monitor_agent.py --keyword "<subject>" --seed seeds/<subject>.txt --use-state-cache

# Clear stale cache before run
python src/cli/main.py --keyword "<subject>" --seed seeds/<subject>.txt --clear-cache

# Start Interactive WebUI Dashboard (Command Center + Vault Gallery)
./run_frontend.bat

# Global CLI Installation & Execution (like 9Router)
# 1. Run installer (once)
.\install.bat
# 2. Open new terminal and type 'scrape' from anywhere
scrape
```

### 2. Analyze

After a run completes, look at these files:

**Primary outputs** (in `output/<subject>/runs/<run_id>/` and `output/`):

- `index.html` (in `output/`) — visually browse downloaded media and monitor stats
- `results.json` — full result payload. Check `.images[]`, `.videos[]`, `.rejected_items[]`, `.page_reports[]`, `.domain_stats`, `.duration_seconds`, `.run_metadata`
- `domain_report.json` — per-domain yield breakdown (pages hit, images found, videos found)
- `images.csv` / `videos.csv` — flat export if `--output both` was used
- `state_cache.db` (in `output/cache/`) — tracks processed URLs to prevent redundant work

**Logs** (in `logs/`):

- `run_<run_id>.log` — full structured log. Search for these patterns:
  - `HTTP 429` — rate limited. Domain needs lower RPS in `data/domain_config.json`
  - `ScraperBypassError` — Crawl4AI fallback also failed. Domain may need referer override or is fully blocked
  - `cloudflare_blocked` / `Skipping Crawl4AI fallback` — domain flagged CF-blocked; expected, no action needed
  - `blacklisted` — domain hit circuit breaker threshold. Check `data/blacklist.json`
  - `cooldown` — domain entered temporary backoff
  - `fetch_error` — network/timeout failures
  - `Skipping scrape` — fast-fail on known dead domains
  - `max_pages_capped` — domain hit its `max_pages` limit; normal if set intentionally
  - `rejected` — media item failed quality filters

**Runtime state** (in `data/` and `output/cache/`):

- `blacklist.json` — domains auto-banned during the run. Review before next run: remove false positives, keep real dead domains
- `sessions/` — persisted cookies. Usually leave alone
- `state_cache.db` — processed URL cache for continuous watchdog execution

### 3. Diagnose

Read the analysis results and identify which category the problems fall into:

| Symptom | Where to look | What to change |
| --- | --- | --- |
| Low image/video count | `domain_report.json` — which domains yielded zero? | Add better seeds, check if domain is blacklisted |
| Too many rejected items | `results.json → rejected_items[]` — read the `reason` field | Tune filters in `src/core/filters.py` |
| Lots of 429 errors | Log grep for `HTTP 429` | Lower RPS in `data/domain_config.json` → `rate_limits` |
| Crawl4AI waste (25s+ per page) | Log grep for `Falling back to Crawl4AI` on same domain repeatedly | Add `# cloudflare: true` to that domain in seed file |
| Crawl4AI fallback failures | Log grep for `ScraperBypassError` | Add domain to `referer_overrides` or `hotlink_protected` in `data/domain_config.json` |
| Domain over-crawled (many pages, low yield) | `domain_report.json` — high pages_scanned, low images/videos | Add `# max_pages: N` annotation to seed file for that domain |
| Booru domains yield thumbnails only | Output images are 256px or named `pic256.jpg` | Set `# crawl: index→detail` and `# depth: 1` for that domain |
| Media is low-resolution | Check downloaded files | Add pattern to `transform_to_highres()` in `filters.py` |
| Heavy SPA (YouTube, TikTok) fails | Empty results from complex SPA sites | Ensure domain is routed to `SpecializedExtractor` (uses `yt-dlp`) in `engine.py` |
| Same URL downloaded multiple times | Log grep for duplicate filenames or locale variants in paths | Add URL normalisation rule to `data/url_normalisation_rules.json` |
| Downloads failing | `results.json → images/videos` where `status == "failed"` | Check `failure_reason` field. Common: blocked hotlink, too small, wrong MIME |
| Pages returning empty | `page_reports[]` where `images_found == 0 && videos_found == 0` | Domain may need `deep_scrape` config or different link patterns |
| Run too slow | `duration_seconds` in results, log timestamps | Increase `--workers`, check if cooldowns are dominating |
| Placeholder/broken images downloaded | Check downloaded file sizes, look for tiny files | Add URL patterns to `is_broken_media_url()` in `filters.py` |
| Large downloads failing/restarting | Downloader logs show file fetch restarts | Range retries automatically append bytes from `.tmp` files. Verify server supports `Range` requests and local disk has space. |
| Crawler hangs/spins on WAF/Login | Log shows consecutive request failures or auth redirect cutoff | Circuit breakers automatically block and skip the domain. Check `data/blacklist.json` or update credentials. |

### 4. Fix

Changes you can make, ordered by where they live:

**No code changes needed** (config/data only):

- `data/domain_config.json` — rate limits, referer overrides, hotlink protection, deep scrape targets, domain handler patterns
- `data/url_normalisation_rules.json` — add a `{ "pattern": "...", "replacement": "..." }` entry to collapse duplicate URL variants
- `data/blacklist.json` — remove false positive bans, or add permanently dead domains
- `seeds/<subject>.txt` — add/remove seed URLs; add annotations (`# type:`, `# Rate-limit:`, `# cloudflare: true`, `# max_pages: N`, `[CDN]`)
- `src/config/subject_profiles.json` — subject profile presets

**Tuning constants** (`src/config.py`):

- `DEFAULT_REQUESTS_PER_SECOND` — global default RPS
- `DOMAIN_COOLDOWN_THRESHOLD` — how many 429s before circuit breaker trips
- `DOMAIN_COOLDOWN_SECONDS` — escalation durations [30, 60, 120]
- `MIN_IMAGE_DOWNLOAD_BYTES` / `MIN_VIDEO_DOWNLOAD_BYTES` — size floor for downloads
- `MIN_IMAGE_WIDTH` / `MIN_IMAGE_HEIGHT` — dimension floor
- `CONCURRENT_PAGES_PER_BATCH` / `CONCURRENT_DOWNLOADS` — parallelism defaults

**Filter logic** (`src/core/filters.py`):

- `is_broken_media_url()` — add patterns for known placeholder/error image URLs
- `looks_like_media()` — tweak media detection heuristics
- `should_keep_image()` / `should_keep_video()` — quality gate criteria
- `CDN_ASSET_DOMAINS` — domains to skip during crawl (ad networks, trackers, stock photo sites)
- `GENERIC_ASSET_TERMS` — filename tokens that indicate non-target assets (logo, icon, banner)

**Extraction logic** (`src/scraper/google_images.py` and `src/scraper/specialized.py`):

- `_extract_images()` — how images are found in page HTML
- `_extract_page_links()` — how crawl links are discovered
- `scrape_page()` — exception handling, status classification
- `SpecializedExtractor` — yt-dlp integrations for zero-DOM extraction on YouTube/TikTok/Reddit

**HTTP behavior** (`src/utils/http_client.py`):

- `_headers()` — how request headers are built per domain (reads from `REFERER_OVERRIDES`)
- `_DomainCooldownState` — circuit breaker thresholds and escalation
- Crawl4AI fallback tiers — stealth browser escalation

**Download behavior** (`src/storage/file_downloader.py`):

- `_make_download_headers()` — per-domain header injection for media downloads
- `_download_file()` — stream validation, MIME checks, size checks
- `_attempt_download()` — Resolution upscaling attempts and origin URL fallbacks

### 5. Verify

Before doing another full run:

```powershell
# Run all backend tests
python -m pytest tests/ -v

# Run frontend Playwright UX tests (E2E & transitions)
pytest tests/test_frontend_ux.py -v -s

# Quick smoke test
python src/cli/main.py --keyword testrun --max-results 1 --page-limit 1 --crawl-depth 0 --clear-cache
```

Then go back to step 1.

## Rules

- Never hardcode specific subject names, target URLs, or domain names in source files under `src/`. All domain-specific behavior goes in `data/domain_config.json`, `data/url_normalisation_rules.json`, `src/config/subject_profiles.json`, or `seeds/*.txt`.
- The `data/` and `src/config/` directories are gitignored. They contain target-specific operational data that stays local.
- After modifying any source code, run `python -m pytest tests/ -v` before doing a full run. All tests must pass.
- When analyzing a run, always read `results.json` AND the log file. The JSON tells you what happened; the log tells you why.
- If a domain gets auto-blacklisted during a run and you think it was wrong, delete its entry from `data/blacklist.json` before the next run.
- If you add a new domain-specific behavior (referer, rate limit, handler pattern), add it to `data/domain_config.json` — not inline in Python.
- If a domain serves duplicate URLs via locale or variant path segments, add a normalisation rule to `data/url_normalisation_rules.json` — not inline in Python.
- If a domain is protected by Cloudflare Turnstile (defeats all browser tiers), add `# cloudflare: true` to its seed block. This skips wasted 25s Crawl4AI fallback attempts that are guaranteed to fail.
- If a domain is over-crawled (many pages scanned, few assets kept), add `# max_pages: N` to its seed block to hard-cap crawl cost without affecting other domains.
- Update `docs/CHANGELOG.md` when making meaningful system changes. Update `docs/ARCHITECTURE.md` when adding new components or changing data flow.

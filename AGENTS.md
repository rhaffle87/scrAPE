# AGENTS.md — scrAPE AI Agent Instructions & Operator Guide

This document provides unified project-scoped instructions, architectural guidelines, coding standards, and operational workflows for AI coding assistants and operators working in the **scrAPE** workspace.

---

## 1. Project Layout & Architecture

```text
src/cli/main.py                     — CLI entry point, all flags documented via --help
src/cli/monitor_agent.py            — Watchdog entry point, continuous monitoring loop
src/cli/cli_wizard.py               — Interactive wizard for standard & watchdog runs
src/config.py                       — Tunable constants (timeouts, concurrency, thresholds)
src/core/engine.py                  — BFS crawl loop, page scoring, domain stats
src/core/filters.py                 — URL classification, media detection, relevance scoring
src/core/models.py                  — ScrapeResult, ImageItem, VideoItem dataclasses
src/scraper/google_images.py        — Search provider + page scraper + link/media extraction
src/storage/file_downloader.py      — Concurrent media downloader with MIME/size validation
src/utils/http_client.py            — Rate limiting, session pooling, 429 circuit breaker, Crawlee, Crawl4AI, DrissionPage & UC fallbacks
src/utils/blacklist.py              — Persistent domain blacklist (data/blacklist.json)
src/utils/session.py                — Persistent cookie cache (data/sessions/)
src/utils/session_pool.py           — Per-domain sticky sessions with disk persistence
src/utils/crawlee_client.py         — Python bridge client for Node.js Crawlee operations
crawlee_bridge/                     — Node.js Express server running Cheerio/Puppeteer stealth modes
data/domain_config.json             — Dynamic domain overrides (rate limits, referer, hotlink, deep scrape)
data/url_normalisation_rules.json   — URL canonicalisation rules loaded into config.URL_NORMALISATION_RULES
src/config/subject_profiles.json   — Subject profile presets (priority domains, max results)
seeds/                              — Per-subject seed manifest files (.txt)
output/<subject>/runs/<run_id>/     — Run output (results.json, domain_report.json, CSVs)
frontend/app.py                     — Interactive FastAPI/HTMX dashboard server
frontend/templates/index.html       — Brutalist WebUI dashboard template
run_frontend.bat                    — Startup script for the interactive dashboard
output/cache/state_cache.db         — SQLite database persisting processed URLs across watchdog runs
logs/run_<run_id>.log               — Full structured log per run
scratch/                            — Test scripts, scratch validation scripts, and diagnostic tools
```

---

## 2. Tech Stack & Core Rules

- **Core Engine**: Python 3.10+ (`src/core/`), FastAPI (`frontend/app.py`), HTMX, SQLite (WAL mode).
- **Stealth & Extraction**: 7-tier WAF fallback pipeline (`src/utils/http_client.py`), Crawlee Express Bridge (`crawlee_bridge/`), `yt-dlp` plugins (`src/plugins/`).
- **WebUI Design System**: Utilitarian Brutalism — strict 90° square corners (`border-radius: 0 !important`), `Oswald` headers, `JetBrains Mono` body/forms, high-contrast dark theme (`#0b0d0c` / `#ff5500` accent).

### Mandatory Coding Rules
1. **Empirical Log Diagnostics**:
   - NEVER form a diagnostic hypothesis for a runtime failure or test breakage without reading the un-truncated error log.
   - Trace errors back to authoritative code before modifying files.
2. **No Hardcoded Domain Rules in Source**:
   - NEVER hardcode domain-specific URL normalisation regex rules or specific subject names in Python source files under `src/`.
   - All URL canonicalisation rules MUST be placed in `data/url_normalisation_rules.json`. All domain-specific behavior goes in `data/domain_config.json`, `data/url_normalisation_rules.json`, `src/config/subject_profiles.json`, or `seeds/*.txt`.
3. **`None`-Safety in Filters & Utilities**:
   - Always use `filters.safe_join(items)` when concatenating string tokens to prevent `TypeError` when processing items with `None` fields (e.g. missing alt text or page titles).
4. **Preserve API Contracts & Backward Compatibility**:
   - Do not alter function signatures or return types without updating all invocation sites across `src/`, `frontend/`, and `scratch/`.
5. **No Superficial Symptom Patches**:
   - Never resolve errors by masking symptoms, swallowing exceptions, returning dummy fallbacks, or deleting failing test scripts in `scratch/`.

---

## 3. WebUI & Aesthetic Rules

1. **Strict Brutalist Geometry**:
   - All UI elements MUST have zero border radius (`border-radius: 0 !important`).
2. **Typography**:
   - Headers (`<h1>`, `<h2>`, `.logo-text`, `.stat-card .value`): `Oswald` font.
   - Code, Forms, Labels, Logs, Buttons: `JetBrains Mono` font.
3. **Color Tokens**:
   - Use CSS variables (`var(--accent)`, `var(--bg-base)`, `var(--bg-surface)`, `var(--text-primary)`, `var(--text-muted)`).
4. **Context-Aware Telemetry**:
   - Stat cards display global totals on Command Center view and subject-scoped totals on Media Vault view.

---

## 4. The Operator Loop

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

# Start Interactive WebUI Dashboard (Command Center + Vault Gallery + Seed Studio)
./run_frontend.bat

# Global CLI Installation & Execution
.\install.bat
scrape
```

### 2. Analyze

After a run completes, inspect these primary outputs:
- `index.html` (in `output/`) — visually browse downloaded media and monitor stats
- `results.json` — full result payload (`.images[]`, `.videos[]`, `.rejected_items[]`, `.page_reports[]`, `.domain_stats`, `.duration_seconds`, `.run_metadata`)
- `domain_report.json` — per-domain yield breakdown (pages hit, images found, videos found)
- `images.csv` / `videos.csv` — flat export if `--output both` was used
- `state_cache.db` (in `output/cache/`) — tracks processed URLs to prevent redundant work
- `logs/run_<run_id>.log` — full structured log (`HTTP 429`, `ScraperBypassError`, `cloudflare_blocked`, `blacklisted`, `rejected`, etc.)

### 3. Diagnose

| Symptom | Where to look | What to change |
| --- | --- | --- |
| Low image/video count | `domain_report.json` — which domains yielded zero? | Add better seeds, check if domain is blacklisted |
| Too many rejected items | `results.json → rejected_items[]` — read `reason` | Tune filters in `src/core/filters.py` |
| Lots of 429 errors | Log grep for `HTTP 429` | Lower RPS in `data/domain_config.json` → `rate_limits` |
| Crawl4AI waste (25s+ per page) | Log grep for `Falling back to Crawl4AI` on same domain repeatedly | Add `# cloudflare: true` to that domain in seed file |
| Crawl4AI fallback failures | Log grep for `ScraperBypassError` | Add domain to `referer_overrides` or `hotlink_protected` in `data/domain_config.json` |
| Domain over-crawled | `domain_report.json` — high pages_scanned, low yield | Add `# max_pages: N` annotation to seed file for that domain |
| Booru domains yield thumbnails only | Output images are 256px or `pic256.jpg` | Set `# crawl: index→detail` and `# depth: 1` for that domain |
| Media is low-resolution | Check downloaded files | Add pattern to `transform_to_highres()` in `filters.py` |
| Heavy SPA (YouTube, TikTok) fails | Empty results from complex SPA sites | Ensure domain is routed to `SpecializedExtractor` (uses `yt-dlp`) in `engine.py` |
| Same URL downloaded multiple times | Duplicate filenames or locale variants | Add URL normalisation rule to `data/url_normalisation_rules.json` |
| Downloads failing | `results.json → images/videos` (`status == "failed"`) | Check `failure_reason` (blocked hotlink, small size, MIME) |

### 4. Fix & Configure

- `data/domain_config.json` — rate limits, referer overrides, hotlink protection, deep scrape targets, domain handler patterns
- `data/url_normalisation_rules.json` — canonicalisation patterns
- `data/blacklist.json` — domain bans (remove false positives or add dead domains)
- `seeds/<subject>.txt` — seed URLs and domain header annotations (`# type:`, `# Rate-limit:`, `# cloudflare: true`, `# max_pages: N`, `[CDN]`)
- `src/config.py` — global thresholds and constants

---

## 5. Verification & Testing

- All testing and test scripts are maintained exclusively inside `scratch/` (the `tests/` directory is deleted and unused).
- Run test scripts via pytest:
  ```powershell
  pytest scratch/ -v
  ```
- Always run `pytest scratch/` after completing code edits to verify that test scripts pass cleanly before declaring completion.

---

## 6. Documentation Maintenance

- Keep documentation synchronized across `README.md`, `docs/`, `AGENTS.md`, `DESIGN.md`, `CONTRIBUTING.md`, and `docs/CHANGELOG.md`.

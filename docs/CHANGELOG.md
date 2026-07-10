# Changelog

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

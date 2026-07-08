# Changelog

## [Unreleased]

### Fixed

- **Trailing-slash media URL parsing** (`video_scraper.py`, `filters.py`):
  Some sites (e.g. sites using tokenised CDN paths) emit media URLs with a
  trailing slash *before* the query string — `…/video.mp4/?token=abc`. Three
  fixes were applied:
  - `DIRECT_VIDEO_PATTERN`, `HLS_PATTERN`, and `DASH_PATTERN` in
    `video_scraper.py` were updated to accept an optional `/` between the file
    extension and the `?` query separator.
  - `detect_video_type()` now normalises the URL path via `urlparse` and
    `str.rstrip("/")` before testing the extension, so `.mp4/` and `.mp4` are
    treated identically.
  - `is_probable_image()` and `is_probable_video()` in `filters.py` call
    `path.rstrip("/")` before the extension suffix check for the same reason.

### Changed

- **`monitor_agent.py` — configurable target keyword/seed file**: The
  previously hardcoded `--keyword` and `--seed-file` values are now top-level
  constants (`KEYWORD` and `SEED_FILE`) defined at the top of the file. Edit
  those two lines to point the monitor at any keyword without touching the
  rest of the script.

### Security / Repository Hygiene

- Replaced all real-world subject names, CDN hostnames, and target site
  domains that had leaked into committed files (tests, source docstrings) with
  generic fictional placeholders (`example_subject`, `video-site.example.com`,
  etc.). Affected files:
  - `tests/test_enhanced_features.py` — sanitised six test functions.
  - `src/core/seed_manifest.py` — sanitised the `entity_tokens` docstring
    example.
  - `scratch/analyze_run.py`, `scratch/check_cache.py`,
    `scratch/test_video_download.py` — sanitised hardcoded run paths and CDN
    URLs (these files are gitignored but cleaned for local hygiene).

---

## [0.6.0] — 2026-07-08

### Added

- **`normalize_media_url()` in `filters.py`**: New utility function used as
  the canonical deduplication key for all collected media items. It strips
  query parameters (auth tokens), decodes percent-encoded path segments
  (`%20` → space), lowercases the path, strips trailing slashes, and
  normalises the scheme to `https`. This ensures that URLs differing only in
  encoding or token value are collapsed to the same key.

- **Tokenless → tokened URL upgrade in `engine.py`**: `seen_images` and
  `seen_videos` were changed from `set[str]` to `dict[str, item]` so that
  each deduplication key maps back to the live item object. When a duplicate
  key is detected and the incoming URL carries query parameters (an auth
  token) while the stored URL does not, the stored item's `.url` field is
  silently upgraded in-place instead of being rejected. This prevents
  tokenless URLs that arrive via JSON-LD `contentUrl` from being downloaded
  and receiving a `403 Forbidden` when the real file requires a token
  present only in the inline `<script>` block discovered later in the same
  page pass.

- **Deferred download phase in `engine.py`**: All media downloads are now
  initiated *after* the full concurrent page-fetching loop completes. This
  guarantees that all URL upgrades (tokenless → tokened) are finalised before
  the first download request is made, eliminating the race condition where a
  partially-upgraded URL could be dispatched to the downloader.

- **Shared `httpx.Client` for downloads in `file_downloader.py`**: The
  `MediaDownloader` is now constructed with a reference to the **scrAPE** engine's
  existing `HttpClient` instance (`http=self.search_provider.http`) and calls
  `self.http.client.get()` directly instead of opening a fresh
  `httpx.Client(...)` per download. This reuses the same connection pool and
  cookie jar across all concurrent download workers, reducing connection
  overhead and preserving any session state set during crawling.

### Added (previous Unreleased entries promoted)

- **Direct binary downloader for media assets**: `MediaDownloader._download_file`
  uses a dedicated raw `httpx.Client` instead of routing through
  `HttpClient.get()`. This prevents the WAF/Crawl4AI browser fallback from
  intercepting binary media URLs, which previously caused CDN-protected videos
  to be silently discarded after Crawl4AI returned an HTML error page instead
  of the binary payload.
- **Browser-like `Referer` + `Origin` header injection** via
  `_make_download_headers()`: CDN authentication checks are satisfied by
  sending the full header set derived from the source page URL, improving
  compatibility across CDN providers.
- **Codebase Reorganisation**: Moved the seed manifest parser to
  `src/core/seed_manifest.py` and removed the redundant `src/seeds` package
  to eliminate Git configuration ignore conflicts.

---

## [0.5.0] — 2026-07-07

### Added

- **Manifest-Driven Focused Mode**: Automatically parses metadata annotations from seed files to enforce crawling rules and lock allowed hosts.
- **Seed Manifest Annotations**:
  - `# subject:` to auto-inject keyword and entity tokens into the relevancy engines.
  - `# type:` to apply domain-level media gating (e.g., image-only or video-only constraints).
  - `# crawl:` to change BFS traversal strategy (`direct` vs `index->detail`).
  - `# [CDN]` to white-list external asset hosts associated with specific seed domains.
- **Dynamic CDN Allow-Listing & Relevancy Penalty Bypass**:
  - Implemented `_get_allowed_hosts(domain_profiles)` in `filters.py` to aggregate all configured domain keys and annotated CDN hosts.
  - Updated media rejection heuristics and relevance scoring to automatically bypass the `-15` index page penalty for assets hosted on white-listed CDNs.
- **Observability Summary**: Added a startup profile log table displaying active domains, strategies, depths, and CDN hosts in real-time.
- Two-tier adaptive Crawl4AI fallback in `HttpClient.get()`:
  - **Tier 1** — Standard Playwright stealth browser (resolves most WAF 403/429 blocks).
  - **Tier 2** — `UndetectedAdapter` browser mode for Cloudflare Turnstile and deep fingerprinting.
- `ScraperBypassError` custom exception that short-circuits `tenacity` retry loops on hard-blocked URLs.
- Cloudflare challenge detection heuristics via DOM title inspection and URL signature matching (`_is_cloudflare_challenge`).
- Crawl4AI internal `is_blocked` override to prevent false-positive early aborts during browser fallback.
- Granular logging for per-URL tier escalation events (Tier 1 success, Tier 2 escalation, total failure).
- `crawl4ai` added to `requirements.txt`.

## [0.4.0] — 2026-07-05

### Added

- Round-robin host balancing in `ScrapingEngine` — pages are de-queued one per host at each depth level to spread load across domains.
- Depth-aware queue (`queues: dict[int, dict[str, deque]]`) replacing the previous flat candidate list.
- `discovered_links_counts` tracking for per-page link discovery reporting in `pages.csv`.
- Keyword-aware link filtering at depth > 0 to avoid following irrelevant discovered links.

## [0.3.0] — 2026-07-04

### Added

- `is_archive_or_index_page` heuristic that applies extra relevance penalties to media found on category/tag/paginated index pages.
- `in_layout_container` flag on `ImageItem` and `VideoItem` with hard `-20` score penalty and `layout_decoration` rejection reason.
- `parent_anchor_href` and `parent_anchor_text` context fields on media items for archive-page relevance scoring.
- `MIN_IMAGE_WIDTH` / `MIN_IMAGE_HEIGHT` enforcement in `rejection_reason_for_image` with `low_resolution` rejection reason.

## [0.2.0] — 2026-07-02

### Added

- Expanded support for more web image and video formats (`.avif`, `.apng`, `.bmp`, `.heic`, `.heif`, `.m4v`).
- Tightened relevance filtering to reject thumbnails, preview images, low-resolution size hints, and generic decorative assets.
- `_preview_penalty` scoring function applied to both image and video relevance.
- Quality-aware download logic that skips tiny or low-value media (`MIN_IMAGE_DOWNLOAD_BYTES`, `MIN_VIDEO_DOWNLOAD_BYTES`).
- `QUALITY_FILTERS.md` documentation.
- `USAGE.md` CLI usage guide.
- `.gitignore` and repository hygiene files.

## [0.1.0] — 2026-06-28

### Added

- Initial production launch of **scrAPE** with keyword-based DuckDuckGo search.
- HTML media extraction: `<img>`, `<video>`, `<source>`, OpenGraph tags, lazy-loaded `data-src` attributes.
- `ScrapingEngine` with BFS crawl loop, seed URL support, and domain allow/block filtering.
- Retry-aware `HttpClient` with `tenacity`, SHA-256 disk cache, and user-agent rotation.
- `RateLimiter` with configurable requests-per-second.
- `robots.txt` compliance checking via `RobotsChecker`.
- JSON and CSV output writers with page-level provenance.
- `MediaDownloader` with MIME/signature validation.
- `--strict-domain`, `--site-tree-only`, `--entity-token`, `--skip-search` CLI flags.

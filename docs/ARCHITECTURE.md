# Architecture

## Module Layout

```text
scraper/
├── main.py                   # CLI entry point, argparse, output dispatch
├── monitor_agent.py          # Watchdog — repeatedly runs scrAPE on a configurable interval
├── seed.txt                  # Root template for auto-generating per-keyword seed files
├── requirements.txt
├── seeds/                    # Per-keyword seed URL files (gitignored — add your own)
│   └── <keyword_slug>.txt
├── docs/
│   ├── ARCHITECTURE.md       # This file
│   ├── CHANGELOG.md
│   ├── QUALITY_FILTERS.md
│   └── USAGE.md
└── src/
    ├── config.py             # All tuneable constants (timeouts, thresholds, keywords)
    ├── core/
    │   ├── engine.py         # ScrapingEngine — orchestrates the full crawl lifecycle
    │   ├── filters.py        # Relevance scoring, rejection logic, URL utilities
    │   │                     #   └─ normalize_media_url() — canonical dedup key
    │   ├── models.py         # Dataclasses: ImageItem, VideoItem, PageReport, ScrapeResult
    │   ├── parser.py         # HTML parser factory (BeautifulSoup + lxml)
    │   └── seed_manifest.py  # SeedManifest — parses and normalizes manifest annotations
    ├── scraper/
    │   ├── base.py           # BaseSearchScraper ABC
    │   ├── google_images.py  # SearchProviderScraper — DuckDuckGo search + page scraping
    │   └── video_scraper.py  # VideoScraper — embed/iframe/JSON-LD video extraction
    │                         #   └─ detect_video_type() — trailing-slash aware
    ├── storage/
    │   ├── csv_writer.py     # CSV output for images, videos, pages, rejected
    │   ├── file_downloader.py# MediaDownloader — MIME/signature validated file writes
    │   │                     #   └─ uses shared httpx.Client (no per-file reconnect)
    │   └── json_writer.py    # Structured JSON output
    └── utils/
        ├── http_client.py    # HttpClient — tiered request engine with WAF fallback
        ├── image_helper.py   # Image signature validation helpers
        ├── logger.py         # Logging configuration
        ├── rate_limiter.py   # Token-bucket rate limiter (thread-safe)
        └── robots.py         # robots.txt compliance checker
```

## Data Flow

```text
CLI args
  │
  ▼
main.py ──► SeedManifest.from_file()   ← Parse domain profiles & CDNs
  │
  ▼
ScrapingEngine.run()
  │
  ├─► SearchProviderScraper.search_pages()   ← DuckDuckGo (disabled in Focused Mode)
  │         │
  │         ▼
  │   candidate page URLs
  │
  ├─► BFS crawl loop (depth/host-balanced deque)
  │         │
  │         ├─► SearchProviderScraper.discover_links()
  │         │         └─► HttpClient.get()  ← tiered fetch
  │         │
  │         └─► SearchProviderScraper.scrape_page()
  │                   ├─► extract images + videos from HTML
  │                   └─► dedup via normalize_media_url()
  │                             └─► tokenless → tokened URL upgrade if needed
  │
  ├─► VideoScraper.search()   ← embed/iframe discovery
  │
  ├─► _finalize_images() / _finalize_videos()
  │         ├─► score_*_relevance()
  │         ├─► rejection_reason_for_*()
  │         └─► deduplicate + sort by score
  │
  └─► MediaDownloader.download()  (deferred — runs after all pages fetched)
            └─► shared httpx.Client (no reconnect per file)
```

## HTTP Client — Two-Tier Adaptive Fallback

```text
HttpClient.get(url)
  │
  ├─► 1. Cache hit? ──► return cached response
  │
  ├─► 2. httpx.get()
  │     ├─► 200 OK ──► store cache, return
  │     └─► 403/401/429
  │               │
  │               ▼
  │         _get_with_crawl4ai(url)
  │               │
  │               ├─► Tier 1: AsyncPlaywrightCrawlerStrategy
  │               │     (headless, enable_stealth=True, magic=True)
  │               │     ├─► Success + no CF challenge ──► cache + return
  │               │     └─► CF challenge or error ──► escalate
  │               │
  │               └─► Tier 2: AsyncPlaywrightCrawlerStrategy
  │                     + UndetectedAdapter()
  │                     ├─► Success + no CF challenge ──► cache + return
  │                     └─► Still blocked ──► raise ScraperBypassError
  │
  └─► ScraperBypassError (non-retryable, exits tenacity loop immediately)
```

## Media URL Deduplication

All collected images and videos are keyed by `normalize_media_url()` in `filters.py` before insertion into the result set. This function:

1. Strips query parameters (auth tokens, cache-busters).
2. Decodes percent-encoded path segments (`%20` → space) so `file%20name.mp4` and `file name.mp4` resolve to the same key.
3. Lowercases the path and strips trailing slashes.
4. Normalises the scheme to `https`.

`seen_images` and `seen_videos` in `engine.py` are `dict[str, item]` (not sets), so the engine can **upgrade** a stored item in-place when a duplicate key arrives with a query-parameter-bearing URL (a CDN auth token) and the stored entry has none. This resolves the common pattern where a page's JSON-LD emits a tokenless `contentUrl` first and its inline `<script>` block later emits the full tokened URL required for a successful download.

### Deferred Download Phase

All downloads are dispatched **after** the full concurrent page-fetching loop finishes. This guarantees every tokenless → tokened upgrade has been applied before the first byte is requested from the CDN.

## Relevance Scoring

Every `ImageItem` and `VideoItem` gets a numeric score computed by `score_image_relevance` / `score_video_relevance` in `filters.py`.

| Signal | Δ Score |
| --- | --- |
| Exact keyword/entity token match in URL/alt/title | +5 per match |
| Compact (joined) token match | +3 |
| Media type matches expected type of domain profile | +3 |
| Has alt text | +1 |
| Has page title | +1 |
| Probable image/video extension | +2 |
| Known video type (youtube, direct, hls…) | +2 |
| Generic asset term (logo, icon, banner…) | −3 |
| Captcha / placeholder / blank token | −4 |
| Preview marker in URL (thumb, preview, small…) | −4 per marker |
| Low-res query param (`width=120`) | −3 |
| Small explicit dimension (`width < 300`) | −20 |
| Layout container (`in_layout_container`) | −20 |
| Non-relevant item on archive/index page | −15 |

### Allowed Hosts & CDN Bypass

- **CDN Host bypass**: If a media item is hosted on a profile's primary domain or any of its associated `# [CDN]` hosts, it is classified as a CDN asset (`is_cdn_asset_domain` is True) and **bypasses the −15 index page relevance penalty**.
- Items with a final score < 1 are rejected with reason `low_score`. Items with no subject text at all are rejected with `low_subject_relevance`.

## Configuration Constants (`config.py`)

| Constant | Default | Description |
| --- | --- | --- |
| `DEFAULT_REQUESTS_PER_SECOND` | `1.0` | Global rate limit for `httpx` requests |
| `DEFAULT_TIMEOUT_SECONDS` | `15.0` | Per-request timeout |
| `DEFAULT_RETRY_ATTEMPTS` | `3` | Max tenacity retries for network errors |
| `DEFAULT_CACHE_TTL_SECONDS` | `3600` | Disk cache TTL (1 hour) |
| `MAX_PAGE_FETCHES` | `0` (unlimited) | Page crawl limit |
| `MAX_CRAWL_DEPTH` | `0` (unlimited) | BFS depth limit |
| `MIN_IMAGE_DOWNLOAD_BYTES` | `10240` | Minimum image file size (10 KB) |
| `MIN_VIDEO_DOWNLOAD_BYTES` | `16384` | Minimum video file size (16 KB) |
| `MIN_IMAGE_WIDTH` | `400` | Minimum image width (px) |
| `MIN_IMAGE_HEIGHT` | `300` | Minimum image height (px) |

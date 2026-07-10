# Architecture — scrAPE

## 1. Data Flow

```mermaid
flowchart TD
    SM["Seed Manifest<br/>(seeds/*.txt)"]
    P["SeedManifest<br/>.from_file() → DomainProfile[]"]
    EO["EngineOptions<br/>(keyword, entity_tokens,<br/>domain_profiles, max_results,<br/>page_limit, crawl_depth)"]
    SE["ScrapingEngine<br/>.run()"]
    BF["BFS Page Discovery<br/>(depth 0, 1, 2, …)"]
    AS["Asset Scoring &amp; Filtering<br/>(filters.py)"]
    DL["Download Pipeline<br/>(ThreadPool, profile-aware)"]
    SR["ScrapeResult<br/>→ manifest.json<br/>→ rejected_items<br/>→ run_metadata<br/>→ duration_secs"]

    SM --> P --> EO --> SE
    SE --> BF & AS & DL
    BF --> SR
    AS --> SR
    DL --> SR
```

## 2. Module Layout

```text
main.py                          — CLI entry point, dry-run, run orchestration
seed.txt                         — Default literal seed (test/demo only)

src/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── engine.py                — ScrapingEngine: BFS crawl, scoring, download orchestration
│   ├── filters.py               — Relevance scoring, rejection reasons, low-res detection
│   ├── models.py                — ScrapeResult, RejectedItem, EngineOptions, DomainProfile
│   └── seed_manifest.py         — SeedManifest parser: annotations → DomainProfile[]
├── storage/
│   └── file_downloader.py       — FileDownloader: HTTP fetch with retries, size filter, thumbnail rejection
└── utils/
    ├── __init__.py
    └── robots.py                — RobotsChecker: per-domain thread-safe parser cache

tests/
├── test_advanced_features.py
├── test_audit_trail.py
├── test_download_retries.py
└── test_performance_quality_features.py

docs/
├── CHANGELOG.md
├── USAGE.md
├── ARCHITECTURE.md
├── QUALITY_FILTERS.md
└── SCENARIOS.md
```

## 3. Core Components

### 3.1 Seed Manifest (`seed_manifest.py`)

`SeedManifest.from_file()` reads a `.txt` seed file and produces a list of `DomainProfile` objects.

**Parser features:**

- Lines beginning with `# type:` → parsed as media type / crawl strategy annotation
- Lines beginning with `# Rate-limit:` → parsed as float req/s
- Lines beginning with `# skip-link-discovery` → flag set on domain profile
- Lines beginning with `[CDN]` → CDN whitelist entry
- All annotations preceding a URL belong to that domain's profile
- Unrecognized comment lines ignored

**DomainProfile fields:**

| Field | Source | Default |
| --- | --- | --- |
| `seed_urls` | URLs listed after annotations | `[]` |
| `type` | `# type:` parse | `""` |
| `crawl` | `# crawl:` within type line | `""` |
| `depth` | `# depth:` | `None` (engine default) |
| `rate_limit` | `# Rate-limit:` | `None` |
| `skip_link_discovery` | `# skip-link-discovery` | `False` |
| `min_image_size` | Programmatic / future annotation | `None` |
| `thumbnail_prefix_pattern` | Programmatic / future annotation | `None` |
| `requires_referer` | Programmatic / future annotation | `False` |

### 3.2 Filter Pipeline (`filters.py`)

**`safe_join(items, sep)`** — Joins only non-None items; replaces all `" ".join([...])` calls in filter functions for `None`-safety.

**Relevance scoring** uses `weighted_subject_score()`:

- URL tokens get 3× weight
- Alt text tokens get 2× weight  
- Source page / page title tokens get 1× weight
- Entity tokens (keyword + additional) get 2× bonus when matched in high-weight fields

**Rejection reasons** (checked in order):

| Reason | When |
| --- | --- |
| `duplicate` | Same URL seen already (norm key collision) |
| `placeholder_asset` | Generic URL pattern with no subject keywords |
| `preview_or_thumbnail` | Preview markers detected (query param or path pattern) |
| `low_resolution_hint` | `has_low_res_query_param()` OR `has_low_res_path_pattern()` |
| `low_subject_relevance` | Below score threshold (image < 3, video < 2) |
| `archive_or_index` | Source page is archive/index AND low score; also CDN-bypassable |
| `max_results_limit` | Collection already full |

**Low-resolution path patterns** (`has_low_res_path_pattern()`):

- Double dimensions: `-150x150`, `_200x300`, `/150x150/`
- Resizer paths: `/resize/150/150/`, `/w_150,h_150/`, `/w_150/h_150/`
- Single dimension: `_150x.jpg` (width-based), `_x150.jpg` (height-based)
- Minimum thresholds: width < 400px, height < 300px

### 3.3 Scraping Engine (`engine.py`)

**Concurrency:**

- Page fetching: all queued pages submitted to `ThreadPoolExecutor`; per-domain `RateLimiter` ensures polite crawl
- Downloading: all qualified items submitted to separate `ThreadPoolExecutor` (configurable via `--dl-workers`)
- `result_lock` is an `RLock` (reentrant) — supports nested critical sections safely

**Deduplication:**

- Global `add_rejected(kind, url, source_page, reason, score)` closure — dedup by `(url, reason)` tuple via `seen_rejected_urls` set. Same URL+reason only logged once.

**Video resolution hint:**

- `_video_resolution_hint(url)` — extracts numeric resolution from URL path (e.g. `_1080p`, `_720p`) via regex `[_\-/](\d{3,4})p`

### 3.4 Download Pipeline (`file_downloader.py`)

`_download_file(url, directory, stem, media_kind, referer=None, min_image_size=None, thumbnail_prefix_pattern=None)`:

1. If `min_image_size` set and media is image: skip if size < threshold
2. If `thumbnail_prefix_pattern` set: skip if URL matches pattern (thumbnail heuristic)
3. HTTP fetch with retry (`tenacity`)
4. Dimension extraction (HEAD request + PIL if needed)
5. Skip on: < configured min size, unparseable dimensions, invalid media type

### 3.5 Robots Checker (`robots.py`)

`RobotsChecker` maintains a per-domain parser cache (`self._parsers` dict) instead of `@lru_cache` for thread safety.

### 3.6 Main Entry (`main.py`)

- Captures `time.monotonic()` start → end → `duration_seconds` on result
- Stores `run_metadata` dict with: `seed_file`, `workers`, `dl_workers`, `page_limit`, `crawl_depth`, `max_results`, `entity_tokens`, `download_media`

## 4. Concurrency Model

```mermaid
flowchart LR
    subgraph SE["ScrapingEngine"]
        PP["Page Fetch Pool<br/>(--workers)<br/>Per-domain rate limiter<br/>(asyncio-like queuing)"]
        DP["Download Pool<br/>(--dl-workers)<br/>Profile-aware:<br/>- referer<br/>- min_image_size<br/>- thumb_pattern"]
        RL["result_lock = RLock()<br/>seen_rejected_urls = set[(url, reason)]"]
    end
```

## 5. Error Handling

- `RobotsChecker` — fetch failures logged, treated as "allowed"
- `_download_file` — returns `(success, reason_dict)` tuple; callers update `item.status`/`item.failure_reason`
- Download exceptions → `item.status = "failed"`, `failure_reason = "exception_{TypeName}"`
- Page fetch failures → skipped with `scope_reason` logged via `add_rejected("page", ...)`

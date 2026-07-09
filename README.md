# scrAPE

```text
  ██████  ▄████▄   ██▀███   ▄▄▄       ██▓███  ▓█████ 
▒██    ▒ ▒██▀ ▀█  ▓██ ▒ ██▒▒████▄    ▓██░  ██▒▓█   ▀ 
░ ▓██▄   ▒▓█    ▄ ▓██ ░▄█ ▒▒██  ▀█▄  ▓██░ ██▓▒▒███   
  ▒   ██▒▒▓▓▄ ▄██▒▒██▀▀█▄  ░██▄▄▄▄██ ▒██▄█▓▒ ▒▒▓█  ▄ 
▒██████▒▒▒ ▓███▀ ░░██▓ ▒██▒ ▓█   ▓██▒▒██▒ ░  ░░▒████▒
▒ ▒▓▒ ▒ ░░ ░▒ ▒  ░░ ▒▓ ░▒▓░ ▒▒   ▓▒█░▒▓▒░ ░  ░░░ ▒░ ░
░ ░▒  ░ ░  ░  ▒     ░▒ ░ ▒░  ▒   ▒▒ ░░▒ ░      ░ ░  ░
░  ░  ░  ░          ░░   ░   ░   ▒   ░░          ░   
      ░  ░ ░         ░           ░  ░            ░  ░
         ░                                           
```

Production-oriented Python scraper that collects public image and video URLs for a keyword query or a user-supplied set of seed pages. Features a __two-tier adaptive fallback system__ that transparently handles WAF-protected and Cloudflare-challenged endpoints using headless browser automation.

## Features

- __Interactive Terminal GUI Wizard__ (`run.bat` / `run.sh` / `cli_wizard.py`) for automated step-by-step setup of Quick, Deep, Targeted, and Watchdog tasks without typing complex command line flags.
- __Adaptive Concurrency Control (Auto-Throttling)__: dynamically scales concurrent crawler tasks up or down based on moving response latencies and server load.
- __Sticky SessionPool__: maintains a persistent cookie jar and consistent User-Agent per target domain to prevent bot detection caused by changing identities.
- __Self-Healing Semantic Selectors__: scores DOM element properties (nesting, alt text, attributes) as a fallback strategy when layout structures or CSS classes change.
- Keyword-based media discovery via DuckDuckGo
- Direct seed URL scraping from CLI or text file with auto-generated seed files from a template
- Entity-aware relevance scoring with optional `--entity-token` aliases
- Domain allow/block rules, strict seed-domain mode, and seed subtree scoping
- Recursive in-domain link discovery with round-robin host balancing and path prioritization
- HTML parsing for images, videos, OpenGraph media, lazy-loaded assets, JSON-LD videos, inline script URLs, and embeds
- __Media URL deduplication via `normalize_media_url()`__: strips auth tokens and query params, decodes percent-encoding, and normalises scheme/case/trailing slashes so structurally identical URLs from different discovery sources collapse to the same key
- __Tokenless → tokened URL upgrade__: when a page exposes a media URL twice (once without and once with a CDN auth token), the engine upgrades the stored entry in-place so downloads always use the authenticated URL
- __Trailing-slash aware extraction__: `DIRECT_VIDEO_PATTERN`, `HLS_PATTERN`, `DASH_PATTERN`, `detect_video_type()`, `is_probable_image()`, and `is_probable_video()` all handle URLs where a trailing `/` precedes the query string
- __Deferred download phase__: all media downloads start after the full crawl loop completes, guaranteeing every URL upgrade is finalised before the first download request
- __Two-tier adaptive HTTP fallback:__
  - __Tier 1__ — Crawl4AI stealth browser (standard Playwright + stealth flags)
  - __Tier 2__ — Crawl4AI `UndetectedAdapter` (bypasses deep fingerprinting and Cloudflare Turnstile)
- Cloudflare challenge detection via DOM and HTTP heuristics
- `ScraperBypassError` for hard-blocked resources that terminates retry loops immediately
- Retry-aware HTTP client with per-domain rate limiting, SHA-256 content caching, and user-agent rotation
- JSON and CSV output with page-level provenance and rejection reasons
- Optional media download mode with MIME/signature validation and tiny-file rejection
- Basic `robots.txt` compliance check for page fetches

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
crawl4ai-setup   # installs Playwright browsers required for WAF fallback
```

> __Note:__ `crawl4ai-setup` must be run at least once to install the Playwright browser engines used by the anti-bot fallback system.

## Usage

For the easiest way to configure and launch runs without memorising complex command line flags, run the interactive terminal wizard:

- __On Windows__: Run `run.bat` (or double-click it in File Explorer).
- __On macOS / Linux__: Run `chmod +x run.sh && ./run.sh`.

Alternatively, configure the CLI parameters manually:

```bash
# Basic keyword search
python main.py --keyword "example_subject" --max-results 100 --output both

# Seed-URL crawl (no search), download all media
python main.py --keyword "example_subject" --seed-file seeds/example_subject.txt --download-media

# Deep crawl with domain scoping
python main.py --keyword "example_subject" --download-media --max-results 500 \
    --page-limit 200 --crawl-depth 6 --strict-domain

# Extra entity aliases to boost relevance
python main.py --keyword "example_subject" --entity-token "alias1" --entity-token "alias2"

# Allow / block specific domains
python main.py --keyword "example_subject" --allow-domain targetsite.com --allow-domain blog.com

# Site-tree-scoped crawl within a profile subtree
python main.py --keyword "example_subject" --seed-url "https://example.com/profile/example_subject" \
    --strict-domain --site-tree-only

# Continuous mode — run scrAPE repeatedly on a 60-second interval
# Edit KEYWORD and SEED_FILE at the top of the file first, then:
python monitor_agent.py
```

## Seed Manifest Format

__scrAPE__ supports a __rich manifest-driven focused-mode__ where seed files (placed at `seeds/<keyword_slug>.txt`) contain metadata annotations to configure crawl behavior and allowed CDNs on a per-domain basis:

```text
# subject: example_subject | alias1 | alias2

# type: image
# crawl: direct
# [CDN] cdn.targetsite.com
https://targetsite.com/gallery/example_subject/

# type: video
# crawl: index->detail
# [CDN] video-cdn.com
https://blog.com/posts/example_subject-videos/
```

### Supported Annotations

- __`# subject: name | alias1 | alias2`__: Configures keyword and entity tokens to auto-inject for scoring.
- __`# type: image | video | mixed`__: Gating constraint. Drops non-matching media types (e.g. discards videos on image-only sites).
- __`# crawl: direct | index->detail`__: BFS strategy. `direct` scrapes media only from the listed page. `index->detail` traverses only detail links from the page.
- __`# [CDN] hostname`__: Explicitly registers domain-associated CDNs, bypassing archive-page relevance penalties for files served from those CDN hosts.

Seed files placed at `seeds/<keyword_slug>.txt` are automatically picked up. If the file does not exist and a `seed.txt` template is present in the project root, it is auto-generated with keyword substitution.

## Output Layout

```text
output/
└── <keyword_slug>/
    └── runs/
        └── 20260706T163900Z/
            ├── results.json     # full structured result set
            ├── images.csv       # image inventory with scores and provenance
            ├── videos.csv       # video inventory with scores and provenance
            ├── pages.csv        # per-page crawl report
            ├── rejected.csv     # items rejected with reasons
            ├── images/          # downloaded images (--download-media)
            └── videos/          # downloaded videos (--download-media)
```

## Anti-Bot Fallback Behaviour

When a page returns __403__ or __429__, the client automatically escalates:

1. __Tier 1 (Standard Stealth)__ — Playwright browser with `magic=True`, `simulate_user=True`, and `override_navigator=True`. Resolves most WAF soft-blocks in ~6–7 s.
2. __Tier 2 (Undetected Browser)__ — Same browser stack but with `UndetectedAdapter` injected to bypass deep fingerprinting and Cloudflare Turnstile challenges.
3. __ScraperBypassError__ — If both tiers fail, a non-retryable exception is raised immediately, skipping the URL without exhausting the `tenacity` retry budget.

Successfully bypassed content is written to the disk cache and served from there on subsequent runs.

## Notes

- __scrAPE__ only targets public pages and does not bypass paywalls or authenticated areas.
- `--strict-domain` keeps the crawl inside the seed-domain set.
- `--site-tree-only` narrows discovered links to the same seed path subtree.
- Download mode only saves direct or manifest media that passes MIME/signature checks and minimum size thresholds.
- Cache TTL defaults to __1 hour__. Delete `.cache/` to force a fresh crawl.

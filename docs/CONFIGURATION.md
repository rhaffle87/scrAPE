# Configuration & Settings Reference — scrAPE
> Complete reference guide for seed manifest annotations, dynamic JSON configuration files, and system parameter guardrails.

---

## 1. Seed Manifest Annotations

Seed files (`seeds/*.txt`) configure extraction rules per domain. Annotations are formatted as comment lines (`# key: value`) preceding a domain or URL block.

| Annotation | Syntax / Values | Default | Description |
|---|---|---|---|
| `type` | `# type: <video \| image \| mixed>` | `mixed` | Expected target media type hint and extraction policy. |
| `crawl` | `# crawl: <direct \| index→detail>` | `index→detail` | `direct` scrapes target URLs only. `index→detail` performs BFS link discovery. |
| `depth` | `# depth: <int>` | `None` | BFS crawl depth limit override for the domain. |
| `Rate-limit` | `# Rate-limit: <float> req/s` | `None` | Per-domain request speed ceiling (e.g., `0.2 req/s` = 1 req / 5 sec). |
| `max_pages` | `# max_pages: <int>` | `None` | Hard ceiling on pages crawled for this domain per run. |
| `engine` | `# engine: <camoufox \| flaresolverr \| ...>` | `None` | Prioritizes a specific WAF fallback engine for this domain. |
| `cloudflare` | `# cloudflare: true` | `false` | Instructs engine to fail fast on 403/429, skipping light fallback loops. |
| `skip-link-discovery` | `# skip-link-discovery` | `false` | Disables page scanning and link discovery entirely for this domain. |
| `[CDN]` | `# [CDN] <hostname>` | `[]` | Whitelists hostname as a CDN domain (bypasses archive/index penalties). |
| `# min_image_size` | `# min_image_size: WxH` | `None` | Minimum image dimension filter (e.g., `800x600`). |
| `# thumbnail_prefix` | `# thumbnail_prefix: <pattern>` | `None` | Path prefix pattern used to identify and skip thumbnail URLs early. |
| `# requires_referer` | `# requires_referer` | `false` | Sends page URL as HTTP Referer header during file download. |
| `# google-fallback` | `# google-fallback: true` | `false` | Fall back to Google Images when page returns 0 images. |

### Example Seed Manifest

```text
# Subject: Apple / Tech Assets
# ---------------------------------------------------------------------------
# gallery.apple.com
# ---------------------------------------------------------------------------
# type: image | crawl: direct
# min_image_size: 1000x800
# thumbnail_prefix: /thumbs/
https://gallery.apple.com/iphone

# ---------------------------------------------------------------------------
# cdn.apple-assets.org
# ---------------------------------------------------------------------------
# type: video | crawl: index→detail
# depth: 1
# Rate-limit: 0.5 req/s
# max_pages: 10
# [CDN] cdn.apple-assets.org
# requires_referer
https://cdn.apple-assets.org/videos
```

---

## 2. Dynamic JSON Configuration Files

JSON files in the `data/` directory isolate domain parameters and canonicalisation rules from Python source code.

### 2.1 Domain Configuration (`data/domain_config.json`)

Controls dynamic settings for known domains to prevent blocks and optimize extraction.

```json
{
    "hotlink_protected": ["example-cdn.com"],
    "rate_limits": { "slow-domain.org": 0.2 },
    "deep_scrape": ["archive-domain.net"],
    "referer_overrides": {
        "protected-media.com": "https://www.protected-media.com/"
    },
    "domain_handlers": {
        "some-booru.net": { "link_pattern": "/post/\\d+" }
    },
    "stealth_required": ["heavily-protected.com"],
    "preferred_engines": { "cf-site.com": "camoufox" },
    "highres_transforms": {
        "cdn.example.com": { "pattern": "-thumb", "replacement": "" }
    },
    "auth_gated": ["members-only-site.com"]
}
```

- **`hotlink_protected`**: Domains enforcing Referer header checks on media downloads.
- **`rate_limits`**: Default requests-per-second ceilings per domain.
- **`deep_scrape`**: Domains configured for deep traversal.
- **`referer_overrides`**: Custom HTTP Referer header values sent during requests.
- **`domain_handlers`**: Per-domain link discovery configuration (`link_pattern` regex used with `# crawl: index→detail`).
- **`stealth_required`**: Domains that skip lightweight HTTP tiers and escalate immediately to stealth browsers on any non-200 response.
- **`preferred_engines`**: Manually pinned WAF fallback engine per domain.
- **`highres_transforms`**: URL substring replacement rules applied to discovered image URLs.
- **`auth_gated`**: Domains that require authentication (crawler skips them unless a valid session cookie is available).

### 2.2 URL Normalisation Rules (`data/url_normalisation_rules.json`)

Defines regex-based canonicalisation rules compiled into `config.URL_NORMALISATION_RULES` at startup.

```json
{
    "rules": [
        {
            "description": "Locale path collapse",
            "pattern": "(example\\.com)/[a-z]{2}/(media|posts|video)",
            "replacement": "\\1/\\2"
        }
    ]
}
```

### 2.3 Blacklist Registry (`data/blacklist.json`)

Maintained automatically by the circuit breaker. Domains triggering persistent 429s or connection failures are blacklisted to prevent future request delays:

```json
{
    "blocked-domain.com": {
        "reason": "consecutive_429s",
        "timestamp": "2026-07-22T14:20:00.000000"
    }
}
```

---

## 3. Environment Variables & Docker Configuration

scrAPE uses environment variables (loaded via `.env` or system environment) to configure API keys and container deployment settings without hardcoding secrets:

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | API token for the Telegram notification bot. |
| `TELEGRAM_CHAT_ID` | Target chat ID for Telegram notifications. |
| `CAPSOLVER_API_KEY` | API key for CapSolver universal captcha resolution. |
| `PUPPETEER_SKIP_DOWNLOAD` | If `true`, prevents `npm install` from downloading Chromium. **Mandatory in Docker** to ensure the Node.js bridge hooks into the Playwright Chromium binary. |

---

## 4. Parameter Safety Guardrails

To prevent memory contention, CPU spikes, bandwidth saturation, or CDN IP rate-limiting during extractions, adhere to these guidelines:

| Parameter | Safe Baseline | High-Performance | Warning Threshold | System Risk / Impact |
|---|---|---|---|---|
| **Scraper Workers** (`--workers`) | **4 – 8** | **12 – 16** | **> 16 workers** | CPU/RAM spikes, browser process spawning stalls |
| **Download Workers** (`--dl-workers`) | **4 – 8** | **12 – 16** | **> 24 workers** | Bandwidth saturation, CDN IP bans (429/503) |
| **Crawl Depth** (`--crawl-depth`) | **1 – 2** | **3 levels** | **> 4 levels** | Exponential link graph explosion |
| **Max Results** (`--max-results`) | **50 – 200** | **500 – 1000** | **0 (Unlimited)** | Unbounded disk usage (gigabytes of media) |
| **Page Limit** (`--page-limit`) | **20 – 50** | **100 – 200** | **0 (Unlimited)** | High network traffic, long job duration |

*The WebUI Command Center includes a dynamic JavaScript validator that displays warning badges if worker counts exceed safe hardware thresholds.*

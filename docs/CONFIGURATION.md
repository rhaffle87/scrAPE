# Configuration & Settings Reference — scrAPE

> Complete reference guide for seed manifest annotations, dynamic JSON configuration files, WAF circuit breakers, parameter safety guardrails, and AI dataset tools.

---

## 1. Seed Manifest Annotations

Seed files (`seeds/*.txt`) configure extraction rules per domain. Annotations are formatted as comment lines (`# key: value`) preceding a domain or URL block:

| Annotation | Syntax / Values | Default | Description |
|---|---|---|---|
| `type` | `# type: <video \| image \| mixed>` | `mixed` | Expected target media type hint and extraction policy. |
| `crawl` | `# crawl: <direct \| index→detail>` | `index→detail` | `direct` scrapes target URLs only (depth 0). `index→detail` performs BFS link discovery. |
| `depth` | `# depth: <int>` | `None` (engine default) | BFS crawl depth limit override for the domain. |
| `Rate-limit` | `# Rate-limit: <float> req/s` | `None` (1.0 req/s) | Per-domain request speed ceiling (e.g. `0.2 req/s` = 1 req / 5 sec). |
| `max_pages` | `# max_pages: <int>` | `None` (unlimited) | Hard ceiling on pages crawled for this domain per run. |
| `cloudflare` | `# cloudflare: true` | `false` | Instructs engine to fail fast on 403/429, skipping light browser fallback loops. |
| `skip-link-discovery` | `# skip-link-discovery` | `false` | Disables page scanning and link discovery entirely for this domain. |
| `[CDN]` | `# [CDN] <hostname>` | `[]` | Whitelists hostname as a CDN domain (bypasses archive/index page penalties). |
| `# min_image_size` | `# min_image_size: WxH` | `None` | Minimum image dimension filter (e.g. `800x600`). Smaller images are rejected. |
| `# thumbnail_prefix` | `# thumbnail_prefix: <pattern>` | `None` | Path prefix pattern used to identify and skip thumbnail URLs early. |
| `# requires_referer` | `# requires_referer` | `false` | Sends page URL as HTTP Referer header during file download to bypass hotlink protection. |

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

JSON files in the `data/` directory isolate domain parameters and canonicalisation rules from Python source code:

### 2.1 Domain Configuration (`data/domain_config.json`)

```json
{
    "hotlink_protected": [
        "example-cdn.com"
    ],
    "rate_limits": {
        "slow-domain.org": 0.2
    },
    "deep_scrape": [
        "archive-domain.net"
    ],
    "referer_overrides": {
        "protected-media.com": "https://www.protected-media.com/"
    }
}
```

- `hotlink_protected`: Array of domains enforcing Referer header checks.
- `rate_limits`: Default requests-per-second ceilings per domain.
- `deep_scrape`: List of domains configured for deep traversal.
- `referer_overrides`: Custom HTTP Referer header overrides map.

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

## 3. Parameter Safety Guardrails & Recommendations

To prevent memory contention, CPU spikes, bandwidth saturation, or CDN IP rate-limiting during extractions:

| Parameter | Safe Baseline | High-Performance | Warning Threshold | System Risk / Impact |
|---|---|---|---|---|
| **Scraper Workers** (`--workers`) | **4 – 8** | **12 – 16** | **> 16 workers** | CPU/RAM spikes, browser process spawning stalls |
| **Download Workers** (`--dl-workers`) | **4 – 8** | **12 – 16** | **> 24 workers** | Bandwidth saturation, CDN IP bans (429/503) |
| **Crawl Depth** (`--crawl-depth`) | **1 – 2** | **3 levels** | **> 4 levels** | Exponential link graph explosion |
| **Max Results** (`--max-results`) | **50 – 200** | **500 – 1000** | **0 (Unlimited)** | Unbounded disk usage (gigabytes of media) |
| **Page Limit** (`--page-limit`) | **20 – 50** | **100 – 200** | **0 (Unlimited)** | High network traffic, long job duration |

*The WebUI Command Center includes a dynamic JavaScript validator (`validateSafetyThresholds()`) that displays warning badges if worker counts exceed safe hardware thresholds.*

---

## 4. AI Ingestion & Dataset Formatting Settings

The interactive wizard (`python src/cli/cli_wizard.py`) provides export settings for AI model training:

### 4.1 Structured AI Dataset Layouts (Option 4)
- **Consolidated Flat**: Copies all images and videos into a single directory, prefixing filenames with domain names to avoid collisions.
- **Domain-Grouped**: Subdirectories per origin domain (`/domain_com/images/`).
- **Media-Type Grouped**: Organized into `/images` and `/videos` folders.

### 4.2 LLM RAG Ingestion Formats (Option 5)
- **Single Consolidated Markdown**: A unified `.md` file summarizing page titles, alt texts, image contexts, and source URLs.
- **Chunked Page Markdown Documents**: Individual `.md` files per page, formatted for vector database document splitters (LangChain, LlamaIndex).
- **JSON-Lines (JSONL) Embeddings Format**: One JSON object per line containing normalized metadata ready for vector embedding models.

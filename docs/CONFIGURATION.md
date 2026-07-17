# Configuration & Settings Guide — scrAPE

This document provides a detailed reference for all configuration options, seed manifest annotations, dynamic configuration files, WAF bypass settings, and AI ingestion helper parameters.

---

## 1. Seed Manifest Annotations

Seed files (`seeds/*.txt`) contain target entry URLs. Annotations (formatted as `# key: value` comments) placed immediately preceding a URL apply to all URLs in that block.

| Annotation | Syntax / Values | Default | Description |
| --- | --- | --- | --- |
| `type` | `# type: <video \| image \| mixed>` | `mixed` | Hint to the crawler indicating the expected target media type. |
| `crawl` | `# crawl: <direct \| index→detail>` | `index→detail` | `direct` targets the seed URLs only (BFS depth 0). `index→detail` follows discovered links. |
| `depth` | `# depth: <int>` | `None` (engine default) | BFS crawl depth limit override for the domain. |
| `Rate-limit` | `# Rate-limit: <float> req/s` | `None` (1.0 req/s) | Limits request speed on a per-domain basis (e.g. `0.1 req/s` is 1 request every 10 seconds). |
| `max_pages` | `# max_pages: <int>` | `None` (unlimited) | Hard ceiling on pages fetched for this domain per run to prevent over-crawling of noisy sites. |
| `cloudflare` | `# cloudflare: true` | `false` | Instructs the crawler to skip all Crawl4AI browser fallback tiers immediately on a 403 or 429 response. |
| `skip-link-discovery` | `# skip-link-discovery` | `false` | Disables page scanning and link discovery for matching URLs. |
| `[CDN]` | `# [CDN] <hostname>` | `[]` | Registers a hostname as a whitelist CDN domain. Assets on these hosts bypass the archive/index page penalty. |
| `min_image_size` | `# min_image_size: WxH` | `None` | Minimum image dimension filter (e.g. `800x600`). Files smaller than this are rejected. |
| `thumbnail_prefix` | `# thumbnail_prefix: <pattern>` | `None` | Path prefix pattern matching to reject thumbnail URLs early. |
| `requires_referer` | `# requires_referer` | `false` | Sets page URL as Referer header when performing file downloads to bypass hotlink protection. |

### Example Seed Block

```text
# type: video | crawl: index→detail
# depth: 1
# Rate-limit: 0.1 req/s
# max_pages: 5
# [CDN] cdn.myvideos.com
# requires_referer
https://myvideos.com/category/subject
```

---

## 2. Dynamic JSON Configuration Files

JSON configurations located in the `data/` directory are loaded at startup. This isolates environment parameters and domain settings from the application code.

### 2.1 Domain Configuration (`data/domain_config.json`)

Stores default limits, request headers, and custom scraper behaviours:

* **`hotlink_protected`** (Array of string domains): Triggers automatic Referer header injection for file downloads on listed hosts.
* **`rate_limits`** (Object mapping domain to float): Default Requests Per Second (RPS) ceiling.
* **`deep_scrape`** (Array of string domains): Flags domains that should use deep traversal defaults.
* **`domain_handlers`** (Object mapping domain to patterns): Specific parsing configurations (e.g. link extraction prefixes).
* **`referer_overrides`** (Object mapping domain to URL): Custom referers used to bypass strict cross-origin hotlink protections.

```json
{
    "hotlink_protected": [
        "example1.com"
    ],
    "rate_limits": {
        "example2.com": 0.1
    },
    "deep_scrape": [
        "example3.com"
    ],
    "referer_overrides": {
        "example4.com": "https://www.example4.com/"
    }
}
```

### 2.2 URL Normalisation Rules (`data/url_normalisation_rules.json`)

Defines regular expression patterns used to collapse duplicate URLs (such as query params or locale prefixes) to canonical forms:

```json
{
    "rules": [
        {
            "description": "Example locale prefix collapse",
            "pattern": "(example\\.com)/[a-z]{2}/(get_file|contents|video)",
            "replacement": "\\1/\\2"
        }
    ]
}
```

### 2.3 Blacklist Registry (`data/blacklist.json`)

Maintained by the circuit breaker. Domains hitting consecutive 429s or HTTP error counts are written to this file and bypassed instantly on subsequent requests:

```json
{
    "example.com": {
        "reason": "consecutive_429s",
        "timestamp": "2026-07-13T00:18:04.690969"
    }
}
```

---

## 3. Web Application Firewall (WAF) & Cloudflare Bypass Tiers

To bypass Cloudflare Turnstile, captchas, and WAF protection, the scraper employs an escalating 7-tier fallback chain:

| Tier | Fetcher Method | Typical Cost | Bypass Capability |
| --- | --- | --- | --- |
| **Tier 0** | `httpx` + Local Cookie Harvesting | ~0.5s–2.0s | Low (relies on active local session cookies) |
| **Tier 1** | `Crawlee` (Cheerio) | ~1.0s–3.0s | Moderate (spoofs standard TLS fingerprints) |
| **Tier 2** | `Crawl4AI` (Headless/Headful) | ~8.0s–15.0s | High (stealth-configured chromium) |
| **Tier 3** | `DrissionPage` | ~10.0s–20.0s | High (handles light JS walls and Captchas) |
| **Tier 4** | `Crawlee` (Puppeteer) | ~15.0s–25.0s | Very High (heavy JS-rendering with stealth plugins) |
| **Tier 5** | `Helium` | ~20.0s | Very High (high-level automation) |
| **Tier 6** | `undetected-chromedriver` (UC) | ~25.0s–35.0s | Extreme (ultimate Turnstile & JS challenge bypass) |

### Cloudflare Block Flag (`cloudflare: true`)

Some WAF configurations (such as Turnstile) prompt an interactive checkbox puzzle that cannot be solved by automated Chromium instances.
Setting `# cloudflare: true` registers the host in a fast-fail set. When a request hits a 403 or 429, the system **immediately raises an error and moves on**, preventing the worker from hanging for 30+ seconds attempting headless/headful browser loops.

---

## 4. Downstream AI & RAG Integrations

The interactive terminal GUI (`src/cli/cli_wizard.py`) provides tools to package scrape runs directly into formats suited for model training or Retrieval-Augmented Generation (RAG):

### 4.1 Create Structured AI Dataset (TUI Option 4)

Exposes downloaded assets with three grouping structures:

1. **Consolidated Flat**: Copies all images and videos into one folder with filenames prefixed by domain to avoid name collisions.
2. **Domain-Grouped**: Organizes assets into subfolders based on origin domain names.
3. **Media-Type Grouped**: Splits files into `/images` and `/videos` directories.

### 4.2 Enterprise LLM RAG Ingestion (TUI Option 5)

Extracts page contexts, image alt text descriptions, and source metadata, exporting to:

1. **Consolidated Markdown Document**: A single file summarizing the entire run.
2. **Chunked Page-Level Documents**: One `.md` file per scraped page, perfect for vector database document splitters.
3. **JSON-Lines (JSONL) Format**: One line per asset containing normalized text descriptions and metadata mappings for automated embedding models.

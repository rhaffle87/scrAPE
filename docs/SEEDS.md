# Seed Manifest Specification & Guide — scrAPE

> Complete reference for creating, annotating, validating, and managing declarative seed files (`seeds/*.txt`).

---

## 1. Overview

Seed files in **scrAPE** are plain text files (`.txt`) used to bootstrap and fine-tune crawls. They define structured **Domain Profiles** and target URLs for specific subjects without hardcoding crawler policies in Python code.

---

## 2. Manifest Syntax

Seed files are parsed line-by-line using a two-pass parser (`src/core/seed_manifest.py`). Comment lines preceding a URL block build up annotations for that domain profile.

### 2.1 Subject Header
The first matching `# Subject:` comment line defines the target subject name and enriches the crawl with automatic entity tokens:

```text
# Subject: Apple / Tech Assets
```

### 2.2 Section Dividers
Lines starting with `# ---` or `# ===` reset all pending domain profile annotations. Use them to cleanly partition domain blocks.

### 2.3 Domain Profile Annotations

| Keyword | Syntax / Format | Description | Example |
|---|---|---|---|
| **Type** | `# type: <image\|video\|mixed>` | Media gating policy for kept assets. | `# type: image` |
| **Crawl Strategy** | `# crawl: <direct\|index→detail>` | `direct` scrapes target URLs only. `index→detail` crawls links. | `# crawl: direct` |
| **CDN Host** | `# [CDN] <hostname>` | Whitelists external CDN domain. | `# [CDN] cdn.domain.com` |
| **Depth** | `# depth: <N>` | BFS crawl depth limit for this domain. | `# depth: 1` |
| **Rate Limit** | `# Rate-limit: <N> req/s` | Sets per-domain request speed ceiling. | `# Rate-limit: 0.5 req/s` |
| **Max Pages** | `# max_pages: <N>` | Hard cap on pages crawled for this domain per run. | `# max_pages: 10` |
| **Cloudflare** | `# cloudflare: true` | Skips light browser fallbacks fast on 403/429. | `# cloudflare: true` |
| **Disabled** | `# disabled` | Skips this entire domain and all its URLs. | `# disabled` |
| **Requires Referer** | `# requires_referer` | Sends page Referer header to bypass hotlink protection. | `# requires_referer` |
| **Min Image Size** | `# min_image_size: WxH` | Filters out images smaller than threshold. | `# min_image_size: 800x600` |
| **Thumbnail Prefix** | `# thumbnail_prefix: <pattern>` | Path prefix to reject thumbnails early. | `# thumbnail_prefix: /thumbs/` |

---

## 3. Normalized Seed Manifest Example

```text
# Subject: Apple / Tech Assets
# ===========================================================================
# Domain Profiles & Target Configurations
# ===========================================================================

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

## 4. Validating Seed Files

Validate seed file syntax and print parsed domain profiles without initiating a crawl:

```bash
python src/cli/main.py --keyword apple --seed seeds/apple.txt --dry-run
```

Or run explicit seed validation mode:

```bash
python -m src.cli.main --validate-seed seeds/apple.txt
```

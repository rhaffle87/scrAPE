# Seed Files Specification & Guide

Seed files in **scrAPE** are plain text files (`.txt`) used to bootstrap and fine-tune crawls. They allow you to define structured **Domain Profiles** and seed URLs for specific search subjects without hardcoding crawler policies in Python code.

---

## 1. The Syntax

Seed files are parsed line-by-line using a two-pass parser. Comment lines preceding a URL block build up annotations for that domain.

### Subject Header
The very first matching `# Subject:` comment line in the file defines the scrape target name.
```text
# Subject: Apple / Apple Inc.
```
*Normalisation*: This automatically enriches the crawl with entity tokens (e.g. `["apple", "inc"]`) used for relevance filtering.

### Section Dividers
Lines starting with `# ---` or `# ===` reset all pending domain profile annotations. Use them to separate different domains.

### Domain Profile Annotations
All other comment lines that precede a URL list are scanned for specific configuration keywords:

| Keyword | Format | Description | Example |
| :--- | :--- | :--- | :--- |
| **Type** | `type: <image\|video\|mixed>` | Gating filter for media items kept on this domain. | `# type: image` |
| **Crawl Strategy** | `crawl: <direct\|index→detail>` | If `direct`, only harvests media from the page. If `index→detail`, crawls nested links. | `# crawl: index→detail` |
| **CDN Host** | `[CDN] <hostname>` | Declares valid external CDN domains that serve media assets. | `# [CDN] static.example.com` |
| **Depth** | `depth: <N>` | Maximum depth for link traversal on this domain. | `# depth: 1` |
| **Rate Limit** | `Rate-limit: <N> req/s` | Sets target requests per second for this host. | `# Rate-limit: 0.5 req/s` |
| **Max Pages** | `max_pages: <N>` | Hard cap on pages fetched from this domain to avoid infinite loops. | `# max_pages: 15` |
| **Disabled** | `disabled` | Skips this entire domain and all its seed URLs. | `# disabled` |
| **Requires Referer** | `requires_referer` | Force requests to send the host as a `Referer` to bypass hotlinking. | `# requires_referer` |
| **Cloudflare** | `cloudflare: true` | Skips the Crawl4AI fallback and errors out fast on WAF checks. | `# cloudflare: true` |
| **Min Image Size** | `min-image-size: <width>x<height>` | Filters out images smaller than this threshold. | `# min-image-size: 400x400` |
| **Thumbnail Prefix** | `thumbnail-prefix: <pattern>` | Path prefix/pattern used to identify and skip low-res thumbnails. | `# thumbnail-prefix: /thumbs/` |
| **Credentials** | `Username: <val>`, `Password: <val>`, `Email: <val>` | Placeholder/fields for credentials (if session login required). | `# Username: user123` |

---

## 2. Generalization & Sanitization

To ensure your seed files are clean, reproducible, and ready for sharing:

1. **No Sensitive Data**: Never commit real usernames, passwords, API tokens, or session IDs in your seed file. Use placeholder comments and instruct the user to configure these via the CLI cookie injection mechanisms (`--login` or `--inject-cookies`).
2. **Use Relative Section Layouts**: Clearly partition your domains using headers and clean spacing.
3. **Avoid Target-Specific Hacks**: Do not hardcode ad-hoc filters for specific targets. Use `domain_config.json` for custom domain handlers and use standard annotations for seed-specific settings.

---

## 3. Normalized Example Seed File

Below is a template showing a well-formed, normalized seed file:

```text
# Subject: Orange Fruit / Citrus
# ===========================================================================
# Domain Profiles & Seed Configurations
# ===========================================================================

# ---------------------------------------------------------------------------
# openverse.org
# ---------------------------------------------------------------------------
# type: mixed | crawl: direct
# Rate-limit: 1.0 req/s
https://openverse.org/search?q=orange

# ---------------------------------------------------------------------------
# unsplash.com
# ---------------------------------------------------------------------------
# type: image | crawl: index→detail
# depth: 1
# [CDN] images.unsplash.com
# min-image-size: 500x500
https://unsplash.com/s/photos/orange
```

---

## 4. Validating Seeds

You can validate any seed file's syntax and annotations using the CLI:

```bash
python -m src.cli.main --validate-seed seeds/apple.txt
```

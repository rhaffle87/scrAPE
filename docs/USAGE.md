# Usage guide

## Prerequisites

```bash
pip install -r requirements.txt
crawl4ai-setup   # one-time — installs Playwright browsers for WAF fallback
```

---

## Basic keyword search

```bash
python main.py --keyword "example_subject" --max-results 100 --output both
```

## Download media

```bash
python main.py --keyword "example_subject" --download-media --max-results 500 \
    --page-limit 200 --crawl-depth 6
```

## Seed-URL crawl (no search)

When a seed manifest file is used, **scrAPE** automatically enters a **Focused Mode**:

- Broad keyword search is **disabled automatically** (unless overridden with `--force-search`).
- Allowed domains are **auto-locked** to the seed domains plus their respective CDN hosts.
- Extra entity tokens/aliases are **auto-injected** from the `# subject:` header.

```bash
python main.py --keyword "example_subject" --seed-file seeds/example_subject.txt --download-media
```

## Restrict to specific domains manually

If not using a manifest, you can manually lock domains:

```bash
python main.py --keyword "example_subject" \
    --allow-domain targetsite.com \
    --allow-domain blog.com \
    --skip-search --seed-file seeds/example_subject.txt
```

## Extra entity aliases (boost relevance for alternate names)

```bash
python main.py --keyword "example_subject" \
    --entity-token "alias1" \
    --entity-token "alias2" \
    --entity-token "alias1 alias2"
```

## Scoped site-tree crawl

```bash
python main.py --keyword "example_subject" \
    --seed-url "https://example.com/profile/example_subject" \
    --strict-domain --site-tree-only --skip-search
```

## Block unwanted domains

```bash
python main.py --keyword "example_subject" \
    --block-domain blockedsite.com \
    --block-domain badsite.com
```

---

## Monitoring agent (continuous mode)

`monitor_agent.py` is a lightweight watchdog that runs **scrAPE** repeatedly at a fixed interval, useful for long-running scheduled collection jobs.

```bash
python monitor_agent.py
```

The agent performs an initial scrape immediately, then sleeps and repeats on the configured interval. It tails the child process stdout in real-time and enforces a per-run timeout (default 30 minutes) to prevent runaway sessions. Press `Ctrl+C` to stop gracefully.

**Configure the target before running** — edit the two constants at the top of `monitor_agent.py`:

```python
KEYWORD   = "example_subject"            # keyword passed to --keyword
SEED_FILE = "seeds/example_subject.txt"  # seed manifest passed to --seed-file
```

**All tunable parameters inside `monitor_agent.py`:**

| Variable | Default | Description |
| --- | --- | --- |
| `KEYWORD` | `"example_subject"` | The keyword / subject name to scrape |
| `SEED_FILE` | `"seeds/example_subject.txt"` | Path to the matching seed manifest file |
| `interval_seconds` | `60` | Seconds between the end of one run and the start of the next |
| `timeout` | `1800` | Max seconds a single scrape run may take before it is killed |

---

## All CLI flags

| Flag | Default | Description |
| --- | --- | --- |
| `--keyword` | *(required)* | Primary search keyword |
| `--max-results` | `0` (unlimited) | Max media items per type |
| `--output` | `json` | `json`, `csv`, or `both` |
| `--download-media` | off | Download files to disk |
| `--seed-url` | — | Seed page URL (repeat for multiple) |
| `--seed-file` | — | Text file with one URL per line |
| `--seed-domain` | — | Extra in-scope domain root |
| `--allow-domain` | — | Restrict crawl to these domains |
| `--block-domain` | — | Skip these domains |
| `--entity-token` | — | Extra relevance alias (repeat as needed) |
| `--skip-search` | off | Disable DuckDuckGo search |
| `--page-limit` | `0` (unlimited) | Max pages to visit |
| `--crawl-depth` | `0` (unlimited) | Max BFS link depth |
| `--strict-domain` | off | Restrict to seed domain set |
| `--site-tree-only` | off | Restrict to seed path subtrees |
| `--domain-delay` | — | Override per-domain request rate (e.g. `example.com=3.0`) |
| `--workers` | `12` | Number of concurrent pages to fetch |
| `--dl-workers` | `16` | Number of concurrent media downloads |
| `--force-search` | off | Force DuckDuckGo search even when a seed file is loaded |

---

## Notes

- **scrAPE** targets public pages only and does not bypass paywalls or authenticated areas.
- WAF-protected pages (403/429) are automatically retried via Crawl4AI stealth browser (Tier 1), then Undetected browser mode (Tier 2).
- Quality filters bias results toward substantive media and away from thumbnails, decorative assets, and previews — see `docs/QUALITY_FILTERS.md`.
- Output is written to `output/<keyword_slug>/runs/<run_id>/`.
- Cache TTL is 1 hour by default. Delete `.cache/` to force a fresh crawl.

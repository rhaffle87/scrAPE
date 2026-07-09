# Usage guide

## Prerequisites

```bash
pip install -r requirements.txt
crawl4ai-setup   # one-time — installs Playwright browsers for WAF fallback
```

---

## Interactive Terminal GUI Wizard

For the easiest way to configure and run scrapers without remembering CLI flags, launch the interactive console wizard:

### On Windows

Double-click `run.bat` or execute in terminal:

```cmd
run.bat
```

### On macOS / Linux

```bash
chmod +x run.sh
./run.sh
```

The wizard guides you step-by-step through three different execution flows:

1. **General/Broad Search**: Guides you to input keyword search, output format, result limits, and crawl depth.
2. **Specified/Targeted Crawling**: Configures strict scraping targeting a loaded seed manifest file (e.g. `seeds/apple.txt`) and automatically sets up focus options.
3. **Continuous Watchdog**: Configures and starts the interval watchdog for continuous background monitoring.

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
python monitor_agent.py --keyword "example_subject" --seed-file seeds/example_subject.txt --download-media --interval 60 --timeout 1800
```

The agent performs an initial scrape immediately, then sleeps and repeats on the configured interval. It tails the child process stdout in real-time and enforces a per-run timeout (default 30 minutes) to prevent runaway sessions. Press `Ctrl+C` to stop gracefully.

**All CLI flags for `monitor_agent.py`:**

| Flag | Env Variable | Default | Description |
| --- | --- | --- | --- |
| `--keyword`, `-k` | `SCRAPE_KEYWORD` | *(required)* | The keyword / subject name to scrape |
| `--seed-file`, `-s` | `SCRAPE_SEED_FILE` | `None` | Path to the matching seed manifest file |
| `--interval`, `-i` | `SCRAPE_INTERVAL` | `60` | Seconds between the end of one run and the start of the next |
| `--timeout`, `-t` | `SCRAPE_TIMEOUT` | `1800` | Max seconds a single scrape run may take before it is killed |
| `--download-media`, `-d` | — | off | Enable downloading of discovered media |

Any additional unknown arguments provided to `monitor_agent.py` will be automatically passed down to the underlying `main.py` executions.

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
- Operational Scenarios Guide — see `docs/SCENARIOS.md` for recommended inputs.
- Quality filters bias results toward substantive media and away from thumbnails, decorative assets, and previews — see `docs/QUALITY_FILTERS.md`.
- Output is written to `output/<keyword_slug>/runs/<run_id>/`.
- Cache TTL is 1 hour by default. Delete `.cache/` to force a fresh crawl.

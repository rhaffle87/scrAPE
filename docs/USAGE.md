# Usage — scrAPE CLI

## Synopsis

```bash
python main.py --keyword <keyword> --seed <path> [options]
```

## Arguments

 | Argument | Type | Default | Description |
 | --- | --- | --- | --- |
 | `--keyword` | `str` | **required** | Search keyword / subject name |
 | `--seed` | `str` | `seed.txt` | Path to seed manifest file |
 | `--max-results` | `int` | `50` | Max images+videos per run |
 | `--output-dir` | `str` | `./output` | Root output directory |
 | `--workers` | `int` | `8` | Page fetch concurrency |
 | `--dl-workers` | `int` | `6` | Download concurrency |
 | `--page-limit` | `int` | `100` | Max pages to crawl |
 | `--crawl-depth` | `int` | `2` | BFS max depth |
 | `--download-media` | flag | `False` | Enable actual file download |
 | `--ignore-robots` | flag | `False` | Skip robots.txt checks |
 | `--entity-token` | `str[]` | `[]` | Additional entity tokens (repeatable) |
 | `--yes` | flag | `False` | Skip confirmations (non-interactive) |
 | `--dry-run` | flag | `False` | Parse seed + validate, no crawl |
 | `--run-id` | `str` | auto | Override run ID |
 | `--keyword-slug` | `str` | auto | Override output dir slug |

## Seed Manifest

Domain profiles are defined in `.txt` seed files. See [README.md](../README.md#seed-manifest-format) for full annotation syntax.

```bash
# Basic run
python main.py --keyword example_subject --seed seeds/example_subject.txt

# Targeted with extra tokens
python main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --entity-token "Entity Name" --entity-token "topic"

# Production sweep (high concurrency, no confirmations)
python main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --max-results 100 --workers 16 --dl-workers 8 ^
  --page-limit 200 --crawl-depth 3 --download-media --yes

# Validate seed manifest only
python main.py --keyword example_subject --seed seeds/example_subject.txt --dry-run

# Stealth mode (single worker, polite speed)
python main.py --keyword example_subject --seed seeds/example_subject.txt ^
  --workers 1 --page-limit 20 --crawl-depth 1
```

## Output Structure

```text
output/{keyword_slug}/runs/{run_id}/
├── manifest.json            # Full scrape result
└── media/                   # (if --download-media)
    ├── images/
    │   └── {filename}.{ext}
    └── videos/
        └── {filename}.{ext}
```

### manifest.json fields

 | Field | Description |
 | --- | --- |
 | `keyword` | Search keyword |
 | `run_id` | Unique run identifier |
 | `duration_seconds` | Total wall-clock time |
 | `run_metadata` | CLI flags used (workers, page_limit, etc.) |
 | `page_count` | Total pages scanned |
 | `scanned_pages` | List of page URLs visited |
 | `page_reports` | Per-page scan diagnostics |
 | `images` / `videos` | Kept asset items |
 | `rejected_items` | Rejected items with reason + score |
 | `domain_stats` | Per-domain stats (pages scanned, kept, rejected) |
 | `errors` | Per-domain error counts |

## Dry Run

```bash
python main.py --keyword test --seed seed.txt --dry-run
```

Parses the seed file and prints the domain profiles without crawling.

## Terminal GUI Wizard

```bash
python cli_wizard.py
```

Interactive TUI for configuring and running scrapes. Launched via `run.bat`.

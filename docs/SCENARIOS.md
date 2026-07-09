# Operational Guide — scrAPE Scenarios & Recommended Inputs

This guide explains the distinct usage scenarios for **scrAPE** and recommends specific input values for each.

---

## 1. General / Broad Exploration Mode

* **Goal**: Discover files broadly across the web using search engines (DuckDuckGo/Google Images) and recursively follow links.
* **Best For**: Unstructured research, building generic subject datasets, or finding new source domains.

### Recommended Inputs

| Field | Recommended Value | Reason |
| --- | --- | --- |
| **Search Keyword** | `[Your keyword]` | Simple term or entity name (e.g. `apple`, `tesla`). |
| **Download Media** | `y` | Set to `n` first if you only want to preview links in `results.json` without consuming disk space. |
| **Max Results** | `50` to `200` | Limits target assets per type (images/videos) so the run finishes quickly. |
| **Max Page Limit** | `30` to `50` | Prevents the crawler from wandering infinitely onto external links. |
| **Max Crawl Depth** | `2` | **Depth 1** crawls only the search results. **Depth 2** follows one hop from those pages. Depth 3+ spreads too widely. |
| **Ignore Robots** | `n` | Highly recommended to respect robots.txt on broad runs to avoid IP bans on general websites. |

---

## 2. Specified / Targeted Seed Archiving Mode

* **Goal**: Focus extraction strictly on a pre-defined set of domain seeds.
* **Best For**: High-yield scraping of specific known galleries, forum threads, or dedicated profiles.

### Recommended Inputs

| Field | Recommended Value | Reason |
| --- | --- | --- |
| **Keyword Identifier** | `[Entity name]` | Matches the seed file configuration slug. |
| **Seed Manifest File** | `seeds/subject.txt` | Path to the text file containing custom seed domain structures. |
| **Download Media** | `y` | Usually the main goal of targeted runs. |
| **Ignore Robots** | `y` | Targeted media host websites often block crawlers in `robots.txt` default rules. Bypassing is necessary here. |
| **Force Search** | `n` | Keeps the scrape strictly localized to the seed file hosts. Set to `y` only if you also want to augment files via search engine keywords. |

---

## 3. Uncapped Production/Archive Run

* **Goal**: Extract every single piece of media matching the targeted seeds with no limits.
* **Best For**: Building a complete offline mirror of a subject gallery.

### Recommended Inputs

| Field | Recommended Value | Reason |
| --- | --- | --- |
| **Max Results** | `0` (Unlimited) | Runs until no new media matches the criteria. |
| **Max Page Limit** | `0` (Unlimited) | Traverses all candidate sub-pages in the BFS queue. |
| **Max Crawl Depth** | `0` (Unlimited) | Crawls all linked pages within target domains. |
| **Ignore Robots** | `y` | Avoids failure states on restricted domain subfolders. |

---

## 4. Continuous Watchdog Mode

* **Goal**: Periodically scrape seeds to capture new additions (e.g., daily updates).
* **Best For**: Scheduled runs on home servers or VPS nodes.

### Recommended Inputs

| Field | Recommended Value | Reason |
| --- | --- | --- |
| **Interval** | `3600` (1 hour) or `86400` (1 day) | Prevents hitting target servers too frequently, which could trigger IP blocks. |
| **Timeout** | `1800` (30 mins) | Automatically terminates a hung or stuck scraping process before the next scheduled run starts. |

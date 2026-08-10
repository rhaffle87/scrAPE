# scrAPE Knowledge Base & Architecture

This document serves as the single source of truth for the `scrAPE` project's architecture, historical benchmarks, and system capabilities. It replaces the old chronological log dumps to provide a clear, accurate, and up-to-date picture of the codebase.

## 1. Architectural Overview

The scrAPE codebase is a highly resilient media scraping engine that successfully implements a tiered approach to bot mitigation (WAF fallbacks, circuit breakers) and manages persistent state effectively for continuous watchdog execution.

- **CLI Layer (`src/cli`)**: Provides a robust entry point including an interactive wizard (`cli_wizard.py`), a continuous watchdog monitor (`monitor_agent.py`), and standard batch execution (`main.py`).
- **Core Engine (`src/core`)**: Drives the BFS crawl loop. Logic heavily relies on `filters.py` to evaluate URL relevance and media validity.
- **Scraping Layer (`src/scraper`)**: Features generic HTML DOM parsers (`google_images.py`, etc.). Complex targets (like YouTube, TikTok) are delegated to Specialized Extractors (e.g., using `yt-dlp`).
- **Storage & State (`src/storage`, `output/cache`)**: Uses a SQLite-backed `StateCache` configured with Write-Ahead Logging (WAL mode) to avoid lock contention under heavy multi-threading. It tracks processed URLs to avoid redundant work across runs.
- **Networking & Stealth (`src/network`)**: Features an 8-tier WAF fallback pipeline orchestrator (`stealth_pipeline.py`) seamlessly integrating Playwright, FlareSolverr, Crawlee, and Universal Captcha strategies to bypass modern anti-bot systems.

## 2. Frontend UI & Telemetry Standards

The frontend (`frontend/app.py`, `frontend/templates/index.html`) is built on **Utilitarian Brutalism** design principles:
- **Aesthetic**: Industrial, high-contrast, zero border radius (`border-radius: 0 !important`).
- **Typography**: `Oswald` for headers, `JetBrains Mono` for data, logs, and inputs.
- **Telemetry**: Real-time stat cards with live active pulses, utilizing HTMX for dynamic, non-blocking page updates without React/Vue overhead.
- **Hardware Safety Bounds**: The UI incorporates alert banners when user parameters exceed safe bounds (e.g., >16 scrapers, >24 downloaders) to prevent socket starvation (`OSError: 10055`).

## 3. Storage & Database Optimization

- **State Cache Impact**: When `use_state_cache=ON`, the crawler queries SQLite to skip previously visited URLs, enabling hyper-fast incremental crawls. 
- **SQLite Performance**: The SQLite database (`state_cache.db`) explicitly uses `PRAGMA journal_mode=WAL` to resolve lock contention when running concurrent downloader threads (e.g., `--dl-workers 16`).

## 4. Historical Benchmarks & Yield Capacities

### Multi-Seed Extraction Yield
In an un-capped benchmark across 32 domain targets, the engine processed over **1,643 images and 202 videos (~9.31 GB)** in a single multi-seed run.

### WAF Fallback Performance
During a 7-tier WAF fallback benchmark run against 18 seed domains:
- The system successfully traversed complex bot protections (e.g., Cloudflare Turnstile).
- FlareSolverr integration efficiently handled initial token negotiation, falling back to Playwright/Crawl4AI when necessary.
- **Media Stream Downloader**: Successfully parsed 302 redirects and 200 OK streams for high-definition video files with dynamic session cookie enrichment (e.g., automatically attaching 9+ required session cookies for CDNs).

---
*Note: Obsolete bug reports (such as pre-v0.24.0 path traversal vulnerabilities and zero-limit infinite loops) and anomalous cross-project testing logs have been pruned from this record.*

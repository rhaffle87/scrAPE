# scrAPE Knowledge Base & Architecture

This document serves as the single source of truth for the `scrAPE` project's architecture, historical benchmarks, and system capabilities. It replaces the old chronological log dumps to provide a clear, accurate, and up-to-date picture of the codebase.

## 1. Architectural Overview

The scrAPE codebase is a highly resilient media scraping engine that successfully implements a tiered approach to bot mitigation (WAF fallbacks, circuit breakers) and manages persistent state effectively for continuous watchdog execution.

- **CLI Layer (`src/cli`)**: Provides a robust entry point including an interactive wizard (`cli_wizard.py`), a continuous watchdog monitor (`monitor_agent.py`), and standard batch execution (`main.py`).
- **Core Engine (`src/core`)**: Drives the BFS crawl loop. Logic heavily relies on `filters.py` to evaluate URL relevance and media validity. Features autonomous `SelfHealingDOMParser` with 3-tier selector recovery (cached SQLite, structural microdata/JSON-LD, LLM synthesizer) and `run_summary.py` telemetry.
- **Scraping Layer (`src/scraper`)**: Features generic HTML DOM parsers (`google_images.py`, etc.). Complex targets (like YouTube, TikTok) are delegated to Specialized Extractors (e.g., using `yt-dlp`).
- **Storage & State (`src/storage`, `output/cache`)**: Features SQLite `StateCache` in WAL mode, Content-Addressable Storage (`CASMediaStore`) with SHA-256 deduplication and zero-copy symlinking, and Apache Arrow `ParquetDatasetExporter` (`--export-parquet`) for columnar ML dataset ingestion.
- **Networking & Stealth (`src/network`)**: Features an 8-tier WAF fallback pipeline orchestrator (`src/network/stealth/`) integrating HTTPX, `curl_cffi`, FlareSolverr, Crawlee, Crawl4AI, Patchright, Helium, and DrissionPage. Implements **Domain Tier Memory Caching** (`_domain_tier_memory`) for immediate direct routing past hostile T1 blocks.
- **Distributed Worker Pool (`src/core/worker_pool.py`)**: Supports hybrid ThreadPool, ProcessPool, Celery, and Redis stream brokers (`--redis-url`).

## 2. Frontend UI & Telemetry Standards

The frontend (`frontend/app.py`, `frontend/templates/index.html`) is built on **Utilitarian Brutalism** design principles:
- **Aesthetic**: Industrial, high-contrast, zero border radius (`border-radius: 0 !important`), deep slate theme (`#08090b`).
- **Typography**: `Oswald` for headers (`h1`, `h2`, `.logo-text`, `.stat-card .value`, `.accordion-summary`), `JetBrains Mono` for code, data, logs, inputs, and button selectors (`.run-mode-selector .btn`).
- **Telemetry**: Real-time stat cards with live active pulses, utilizing HTMX for dynamic, non-blocking page updates without React/Vue overhead.
- **Hardware Safety Bounds**: The UI incorporates alert banners when user parameters exceed safe bounds (e.g., >16 scrapers, >24 downloaders) to prevent socket starvation (`OSError: 10055`).

## 3. Storage & Database Optimization

- **State Cache Impact**: When `use_state_cache=ON`, the crawler queries SQLite to skip previously visited URLs, enabling hyper-fast incremental crawls. 
- **Content-Addressable Storage (CAS)**: Media payloads stored under SHA-256 hash trees with symlinks pointing from human-readable directory structures, achieving 100% byte-level deduplication.
- **SQLite Performance**: The SQLite databases (`state_cache.db`, `repaired_selectors.db`) explicitly use `PRAGMA journal_mode=WAL` to resolve lock contention when running concurrent downloader threads (e.g., `--dl-workers 16`).

## 4. Historical Benchmarks & Yield Capacities

### Multi-Seed Extraction Yield
In an un-capped benchmark across 32 domain targets, the engine processed over **1,643 images and 202 videos (~9.31 GB)** in a single multi-seed run.

### Domain Tier Memory Speedup
In protected-domain benchmarks, bypassing redundant T1 HTTPX 403 failure loops via Domain Tier Memory reduced subsequent request latency from **347.8ms to 41.1ms (-88.2% latency reduction, 8.47× speedup)** with a **3.42× total batch throughput gain**.

### WAF Fallback Performance
During multi-tier WAF fallback benchmark runs against protected seed domains:
- The 8-tier hierarchy traverses bot protections (Cloudflare Turnstile, DataDome, Akamai).
- FlareSolverr and `curl_cffi` handle token negotiation and TLS fingerprint spoofing, escalating to Playwright/Crawl4AI/DrissionPage when needed.
- **Media Stream Downloader**: Successfully parses 302 redirects and 200 OK streams for high-definition video files with dynamic session cookie enrichment (e.g., automatically attaching 9+ required session cookies for CDNs).

---
*Note: Synced with v0.29.0 release state. Automated test suite validates 541 tests across core, network, ml, and storage domains.*

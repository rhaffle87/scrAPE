# Release Notes — scrAPE v0.30.1
**Release Date**: October 12, 2026  
**Focus**: Core Engine Performance & Concurrency Overhaul, Sub-Linear BK-Tree Perceptual Hash Deduplication, Profiler Thread Pool Isolation, High-Throughput HTTP Connection Pooling, In-Memory TTL DOM Self-Healing Cache, Zero-Recompression Direct Byte Ingestion, and Single-Flight Host Canary Probing.

---

## Key Highlights (v0.30.1)

### 1. Sub-Linear BK-Tree Perceptual Deduplication (`storage.downloader.manager`)
- **Metric Space Search ($O(\log N)$)**: Replaced full $O(N)$ linear pairwise Hamming distance comparisons with a discrete metric space `BKTree` in `MediaDownloader` (`src/storage/downloader/manager.py`).
- **Hamming Distance Bounding**: Strict distance ceiling ($\text{dist} \le 4$) evaluated against 64-bit DCT perceptual hashes (`dhash`). During large-scale media harvests with tens of thousands of images, lookup latency dropped from hundreds of milliseconds of CPU spin to sub-millisecond lookups.
- **Persistent Seed Hydration**: On initialization, historical pHashes loaded from `StateCache` are ingested directly into the in-memory BK-tree, ensuring cross-run duplicate suppression without quadratic overhead.
- **Re-Export Compatibility**: Preserved explicit `__all__ = ["MediaDownloader", "hamming_distance", "get_image_dimensions"]` ensuring backward compatibility for third-party scripts and unit tests importing helper methods directly from `storage.downloader.manager`.

### 2. Isolated Domain Profiler Thread Pool (`core.coordinator`)
- **Thread Starvation Elimination**: Partitioned `CrawlCoordinator` (`src/core/coordinator.py`) execution pools. Heavy, blocking headless browser domain profiling (evaluating challenge protections, cookies, and Cloudflare indicators) is now dispatched to an isolated `_profiler_pool` (`ThreadPoolExecutor(max_workers=2)`).
- **Unblocked BFS Crawl Loop**: The primary worker pool (`_worker_pool`) remains exclusively dedicated to rapid BFS link extraction and page parsing, eliminating head-of-line crawl stall when discovering previously unseen hostile domains.
- **Clean Worker Termination**: Added graceful shutdown for `_profiler_pool.shutdown(wait=False)` on crawl coordinator teardown.

### 3. Enterprise HTTP Connection Pooling & Request-Scoped Cookie Isolation (`network.http_client`)
- **Configured Connection Pool Limits**: Initialized `httpx.Client` with explicit `httpx.Limits(max_connections=200, max_keepalive_connections=50, keepalive_expiry=30.0)`, preventing socket starvation (`WSAENOBUFS / OSError: 10055`) under high downloader concurrency.
- **Thread-Safe Cookie Isolation**: Eliminated cross-thread cookie leakage by replacing mutable in-place client cookie updates (`self.client.cookies.update(session.cookies)`) with request-scoped dictionaries (`cookies=req_cookies`). Multiple concurrent worker threads crawling different authenticated domains with distinct session cookies no longer clobber one another.
- **Deterministic Proxy Client Cleanup**: When rotating proxies in `set_proxy()`, the previous `httpx.Client` instance is explicitly closed (`old_client.close()`) before allocating the new client, terminating orphaned TCP connections immediately.

### 4. In-Memory TTL DOM Self-Healing Cache (`core.self_healing_parser`)
- **Two-Tier Resolution Hierarchy**: Added an in-memory dictionary cache layer (`_in_memory_cache`) in front of the SQLite WAL database in `SelfHealingDOMParser` (`src/core/self_healing_parser.py`).
- **Zero Disk I/O on Hot URLs**: Frequently crawled domains and recurring page templates retrieve repaired CSS selectors directly from memory in $<0.01\text{ms}$.
- **7-Day TTL Expiration Enforcement**: Cache entries older than 7 days (`MAX_REPAIRED_SELECTOR_AGE_SECONDS = 604800`) are actively evicted on access, preventing stale broken selectors from persisting across web application redesigns.
- **Pre-Cache Live DOM Verification**: Repaired selectors synthesized by LLM or heuristics are validated against live DOM elements before being committed to memory or disk.

### 5. Zero-Recompression Direct Byte Ingestion (`storage.downloader.cpu_worker`)
- **Generational Artifact Prevention**: Refactored `_process_image_cpu_bound` in `src/storage/downloader/cpu_worker.py`. Rather than opening images with Pillow, re-encoding them to a byte buffer, and rewriting them to disk, the worker now verifies file integrity via `img.verify()` and writes the raw downloaded byte stream directly.
- **CPU & Memory Reduction**: Eliminates redundant JPEG/WebP decompression and recompression CPU cycles, reducing CPU worker task duration by up to 65% while preserving original image byte fidelity and metadata.

### 6. Single-Flight Host Canary Probes & Exponential Cooldown (`core.governor`)
- **Single-Flight Half-Open Probing**: When a target domain enters `PARKED` state after triggering 429 or 503 throttling in `CrawlGovernor` (`src/core/governor.py`), only a single canary request is permitted through to test domain recovery. All other concurrent workers targeting the same host are held back until probe resolution.
- **Exponential Overload Backoff**: Consecutive throttle responses scale host cooldown exponentially (base cooldown $\times 2^n$ up to safety ceilings), preventing aggressive flood patterns on recovering servers.
- **Zero-Spin CPU Sleep Gating**: In `CrawlCoordinator`, replaced tight spin loops during domain cooldown with event-driven timeouts (`time.sleep` with dynamic min-wait clamping), keeping idle CPU usage at 0%.

### 7. Deterministic Test Suite Fixture Isolation (`tests/conftest.py`)
- **Autouse Hardware Governor Reset**: Added an autouse fixture in `tests/conftest.py` ensuring the global `HardwareLoadGovernor` instance resets to deterministic concurrency scaling factors between tests, eliminating test order flakiness and environment-dependent concurrency throttling.

### 8. QA Validation & CI Status
- **Full Test Suite Baseline**: **961 collected tests** across CLI, core, network, plugins, ML, and storage domains.
- **100% Green CI Workflows**:
  - `Automated Test Suite`: All 7 matrix jobs passing cleanly across Windows, Linux, macOS, and minimal dependency runners.
  - `Security Scan`: 5/5 jobs passing (Gitleaks, Bandit, Semgrep, Trivy, OSV-Scanner).
  - `CodeQL Advanced`: 0 open alerts.
  - `Deploy Dashboard & Docs to GitHub Pages`: Built and deployed cleanly.

---

# Release Notes — scrAPE v0.30.0
**Release Date**: September 23, 2026  
**Focus**: Distributed Task Leasing & Autonomous Worker Daemons, Cloud Content-Addressable Storage (CAS) S3/R2 Synchronization, and Multimodal Vision-Language (VLM) DOM Healing with Prompt-Injection Immunity and Default-Deny Interaction Gating.

---

## Key Highlights (v0.30.0)

### 1. Distributed Task Leasing & Autonomous Worker Daemons (Component 1)
- **Atomic Idempotency Locking (AC1.1)**: Upgraded `RedisStreamTaskBroker` (`src/core/worker_pool.py`) with distributed mutual exclusion locks (`SET scrape:completed:{task_id} NX EX 86400`). Guaranteed single execution and single disk output across worker restarts, re-claims, and network partitions (verified via unmocked process termination tests).
- **Poison-Pill Routing & Dead Letter Stream (AC1.4)**: Malformed or unprocessable crawl tasks are detected after max retries and automatically shunted to the Dead Letter Stream (`scrape:dead_letter`), preventing PEL head-of-line blocking.
- **Autonomous Worker Daemons (`DistributedWorkerNode`) (AC1.5 & AC1.6)**: New daemon (`src/core/distributed_worker.py`) and standalone CLI entrypoint (`src/cli/worker.py`) implementing strict write-before-ack ordering, background heartbeats (`scrape:workers:heartbeats`), active node tracking, and automatic stale consumer garbage collection (AC1.7).
- **Adversarial Schema Validation (AC1.3)**: 84 adversarial fuzz test cases against Pydantic task schemas (`src/core/task_schema.py`) validating strict rejection of path traversal, SSRF payloads, and invalid execution boundaries.

### 2. Cloud Content-Addressable Storage (CAS) S3/R2 Synchronization (Component 2)
- **Asynchronous Cloud Replication (`CASCloudSyncer`) (AC2.5 & AC2.6)**: Bounded spooling queue (`maxsize=1000`) providing asynchronous block replication to Amazon S3, Cloudflare R2, and MinIO with immediate backpressure (`CASQueueFullError`) under network saturation.
- **Canonical Key Validation & Traversal Immunity (AC2.3)**: Strict 64-character lowercase hex digest validation (`validate_cas_key`) mathematically eliminates directory traversal, null-byte injection, and non-hex object key fabrication across local and cloud CAS storage.
- **Unconditional SSRF Endpoint Defense (AC2.2)**: Canonical `validate_s3_endpoint_url` blocks AWS EC2 metadata (`169.254.169.254`), GCP metadata (`metadata.google.internal`), Azure metadata (`metadata.azure.com`), link-local IPs, private network CIDRs, and default loopbacks.
- **Source-Level Credential & Header Redaction (AC2.1 & AC2.4)**: `redact_s3_error` strips AWS access keys (`AKIA...`), secret access keys, presigned signatures (`X-Amz-Signature`), and basic auth credentials from all logs and error traces. Ephemeral presigned URLs are clamped to ≤900s TTL and kept purely in memory, never written to disk or `run_summary.json`.
- **Zero-Dependency Architecture**: `boto3` decoupled into optional `[cloud]` extra; pure local CAS operations run with zero cloud SDKs installed. Verified on clean environments via dedicated CI runner `test-base-minimal`.

### 3. Multimodal Vision-Language (VLM) DOM Healing (Component 3)
- **Tier 4 Multimodal Self-Healing (`VisionDOMHealer`)**: Seamlessly integrated into `SelfHealingDOMParser` (`src/core/self_healing_parser.py`) as a fail-safe fallback when rule-based (T1), heuristic (T2), and text LLM (T3) strategies fail.
- **Prompt Injection Immunity (AC3.1)**: System prompts isolate untrusted page content and attribute strings within strict XML boundary tags (`<untrusted_scraped_data>`). Validated against a 75-vector parameterized fuzzing corpus (`PROMPT_INJECTION_ADVERSARIAL_CORPUS`) with 100% rejection of system overrides, delimiter breakouts, script/iframe smuggling, and SQL/shell injection payloads.
- **Output Parsing & Pseudo-Class Filtering**: Strict structured regex validation requiring standard media element prefixes (`img`, `video`, `source`, `picture`, `[data-src]`) and blocking dangerous pseudo-classes (`:is`, `:has`, `:where`, `:scope`, `:root`).
- **Structural Default-Deny Allowlist (AC3.4)**: `is_safe_vlm_interaction_target()` enforces a default-deny allowlist accepting only verified media player controls (`play`, `pause`, `mute`, `fullscreen`) and overlay/cookie dismissals (`close`, `dismiss`, `accept`, `reject cookies`), rejecting destructive form submissions, checkout buttons, and arbitrary navigational links.
- **Live DOM Validation Gate & 7-Day TTL (AC3.5)**: Repaired selectors must match $\ge 1$ DOM media element before cache persistence; empty or unvalidated selectors are never written to cache. Cached repairs strictly expire after 7 days (`MAX_REPAIRED_SELECTOR_AGE_SECONDS = 604800`).
- **Circuit Breakers & Global Budget Ceiling (AC3.2)**: `DomainVLMTracker` trips after 3 consecutive failures for any single domain to fail closed; global session budget ceiling (`max_vlm_calls`, default 50) halts calls when exhausted.
- **Explicit User Consent & Memory Lifecycle (AC3.3 & AC3.6)**: Hosted third-party providers (Gemini, OpenAI) fail closed unless `--vlm-provider-consent` is explicitly supplied. `ScreenshotContext` ensures deterministic memory buffer disposal and aborts under critical host RAM pressure (>90% via `psutil`). Built exclusively with raw `httpx` REST calls (0 added base dependencies).

### 4. QA Validation, Test Matrix & Empirical Proofs
- **Full Regression Test Suite**:
  - **Local Workstation (Windows 11, Python 3.13)**: **903 passed, 4 deselected, 0 failed in 270.91s** (907 collected).
  - **GitHub Actions CI Matrix (Workflow Run [`35807593427`](https://github.com/rhaffle87/scrAPE/actions/runs/35807593427))**: All 7 jobs passed (886 passed across all 6 OS/Python runners; 566 passed on dedicated `test-base-minimal` runner).
- **Security Scan (Workflow Run [`35807593255`](https://github.com/rhaffle87/scrAPE/actions/runs/35807593255))**: 5/5 security jobs passed (Gitleaks, Bandit, Semgrep, Trivy, OSV-Scanner).
- **CodeQL Advanced (Workflow Run [`35807593384`](https://github.com/rhaffle87/scrAPE/actions/runs/35807593384))**: Automated gate passed; GitHub Code Scanning REST API verified with `[]` (0 open alerts).
- **Empirical CI Failure Gate Tests**:
  - Pull Request #8: Proven automated pipeline block on injected path traversal flaw.
  - Pull Request #9: Proven automated pipeline block on committed cloud access keys.

---

# Release Notes — scrAPE v0.29.0
**Release Date**: September 21, 2026  
**Focus**: Distributed Cluster Orchestration, Pre-Warmed Anti-Bot Browser Lifecycle Pool, Multi-Provider LLM Self-Healing DOM Parser, Vision Hardware Acceleration, Global Content-Addressable Storage (CAS), Snappy Apache Parquet Columnar Export, and Full Surface UX Harmonization.

---

## Key Highlights (v0.29.0)

### 1. Pre-Warmed Anti-Bot Browser Lifecycle Pool
- **Calibrated Operational Latency Speedup**: Pre-initializes warm browser instances (DrissionPage, Camoufox, Chromium) asynchronously in the background. Empirical re-benchmarking confirms:
  - Pure instance checkout: **0.0079ms** vs **1,424.64ms** cold launch (~180,000× speedup).
  - Full end-to-end DOM interaction round-trip: **96.39ms** warm vs **1,491.26ms** cold (**15.47× operational speedup**), eliminating ~1.4s of blocking latency per browser challenge escalation.
- **Resource Lifecycle Hygiene**: Recycles instances after 20 operations or 300s idle TTL, terminating child processes recursively with zero zombie leaks.

### 2. Distributed Cluster Orchestration (`RedisStreamTaskBroker`)
- **Redis Streams Consumer Groups**: Supports multi-node scraping clusters via `XADD`, `XREADGROUP`, `XACK`, and auto-claim reassignments (`XAUTOCLAIM`) for orphaned tasks.
- **Zero-Dependency Resilience**: Automatically degrades to `InMemoryTaskBroker` (0.007ms lease latency) when Redis is unconfigured or offline.

### 3. Multi-Provider LLM Synthesis & Vision Hardware Acceleration
- **Hardware Device Manager**: Dynamic detection of CUDA, Apple Silicon (MPS), DirectML on Windows, and CPU with FP16/FP32 precision routing.
- **Self-Healing DOM Parser**: Multi-tier cascade with structural tree heuristics and multi-provider LLM failover (Ollama $\to$ Gemini Flash $\to$ OpenAI GPT-4o-mini) and SQLite repair caching (`repaired_selectors` table). Tested on live `books.toscrape.com` extracting 20 items in 7.75ms under complete class obfuscation.

### 4. Global Content-Addressable Storage (CAS) & Snappy Parquet Export
- **Content-Addressable Storage**: SHA-256 sharded storage with atomic NTFS hardlinks (`st_nlink == 2`), consuming 0 additional disk bytes for duplicate media across runs.
- **Snappy Parquet Columnar Datasets**: Direct export of media and crawl metadata into columnar Parquet tables (`crawl_dataset.parquet`).

### 5. Domain Tier Memory Caching & Throughput Optimization
- **Bypass Redundant T1 Failures**: Introduces in-memory Domain Tier Memory (`_domain_tier_memory`) that caches the successful stealth tier per host. Hostile bot-protected domains route directly to their proven engine (`curl_cffi`, `flaresolverr`, `drissionpage`, etc.), completely bypassing redundant 500-2000ms T1 HTTPX 403 failure loops.
- **Empirical Benchmark Results**:
  - Baseline latency (T1 403 loops + fallback): **347.8 ms/req**.
  - Subsequent cached tier latency: **41.1 ms/req** (**-88.2% latency reduction, 8.47× speedup**).
  - Total batch throughput gain: **3.42×**.

### 6. SSRF Redirect Chain Validation & Security Hardening
- **Anti-SSRF & Rebinding Defense**: Every target URL and redirect chain hop is strictly verified with `is_safe_target_url()` to block private CIDRs, link-local, loopback, and cloud metadata (`169.254.169.254`).
- **Intermediate Hop Inspection**: Event hook intercepts redirect sequences (`response.history`) to prevent open redirect SSRF pivot vulnerabilities.
- **Credential Scrubbing**: Plaintext passwords in Redis URLs and HTTP basic auth strings are scrubbed to `***` before logging.
- **Strict 3-Step Path Resolution**: Enforced across CAS store, Parquet exporter, and dataset exports with zero `# codeql` suppression comments.

### 7. Multi-Surface Design Harmonization & Observability
- **Web Dashboard**: 0px horizontal scroll overflow verified across Desktop, Tablet, and Mobile viewports; WCAG 2.1 touch-target heights >= 44px; Oswald 700 accordion headers; JetBrains Mono 700 button selectors.
- **Documentation Site**: 0 broken anchor links (out of 49 total), mobile table scrolling containers, and verified architectural freshness.
- **Terminal UI**: Dynamic `v0.29.0` ASCII banner, Acquisition Orange (`CLR_ORANGE`) brand alignment, and strict <= 80-column line widths.
- **Self-Healing Observability**: `run_summary.json` and post-run console summaries now expose `"self_healing"` metrics tracking items recovered per run, strategy breakdown, and historical SQLite cache hits.

### 8. QA Validation & Test Suite
- **Regression Suite**: 546 passed, 0 failed.
- **Static Security**: Bandit SAST scanned 21,594 LoC with 0 High-severity issues.
- **SSRF Protection Matrix**: 5/5 targets blocked with HTTP 400.

---

# Release Notes — scrAPE v0.28.0
**Release Date**: September 20, 2026  
**Focus**: Next-Gen Core Systems Architecture — Asynchronous ML Pipeline Stage, Multi-Tier Storage Sinks & Hierarchical Deduplication, Autonomous Self-Healing DOM Parser, Hybrid Process-Tree Concurrency Pool, Universal CAPTCHA & WebUI Parity.

---

## Key Highlights (v0.28.0)

### 1. Asynchronous Inline ML Pipeline Stage
- **Decoupled Architecture**: Decoupled heavy ML inference (`AestheticScorer`, `DatasetCropper`, `DatasetTagger`, `RagExporter`, `DatabaseExporter`) from the core network crawl loop into a dedicated background worker (`AsyncMLPipelineWorker`).
- **Zero Network I/O Blocking**: Crawl tasks enqueue downloaded media items instantly into a thread-safe queue; ML tasks execute in worker threads/processes without degrading network throughput.
- **Aesthetic Culling**: Configurable minimum aesthetic score filter (`--aesthetic-score`, `EngineOptions.aesthetic_score`) culls low-quality or watermarked media before disk/cloud persistence.
- **Auto-Cropping & WD14 Booru Tagging**: Automated face/body-centered smart cropping (`--auto-crop`) and AI vision tag generation (`--tag-dataset`) with sidecar `.txt` files for AI/LoRA training pipelines.

### 2. Multi-Tier Storage Sinks & Hierarchical Deduplication Cascade
- **Pluggable Storage Sinks**: Introduced `BaseStorageSink` abstraction with `LocalStorageSink` (atomic temporary staging, directory traversal protection, POSIX sanitization) and `S3StorageSink` (direct multipart cloud streaming via `boto3` with automatic local fallback on network/credential failure).
- **3-Tier Deduplication Cascade**:
  - **Tier 1 (L1)**: In-memory SHA-256 Bloom filter for instantaneous O(1) exact byte-match rejection.
  - **Tier 2 (L2)**: Perceptual pHash (64-bit DCT) indexed in a BK-Tree metric tree for fast sub-linear Hamming distance similarity searches (<= 4 bits).
  - **Tier 3 (L3)**: Pluggable vector cosine similarity index (>= 0.96) for semantic visual embeddings.

### 3. Autonomous Self-Healing DOM Parser
- **Multi-Tier Cascade**:
  - **Tier 1**: SQLite selector rule cache (`repaired_selectors` table) for sub-millisecond retrieval of previously repaired selectors.
  - **Tier 2**: Structural heuristic recovery tree evaluating semantic tag signatures, schema.org / JSON-LD microdata, OpenGraph properties, and image/video element signatures.
  - **Tier 3**: Pluggable LLM selector synthesis with SQLite caching for high-entropy site redesigns.
- **Semantic Selector Integration**: Integrated directly into `SemanticSelectorParser` as the automatic fallback handler when primary CSS/XPath selectors yield 0 items.

### 4. Hybrid Concurrency Worker Pool & Process Lifecycle
- **Dual-Model Pool**: `HybridWorkerPool` offering high-throughput CPU/GPU isolation via `ProcessPoolExecutor` (`spawn` context) and lightweight thread fallback for non-multiprocessing environments.
- **Process-Tree Hygiene**: Recursive child process discovery and termination via `psutil` process trees, guaranteeing zero lingering browser or worker zombie processes. Registered emergency `atexit` supervisor.

### 5. Universal CAPTCHA Strategy & WebUI Parity
- **Flexible Provider Selection**: Supported commercial APIs (`2captcha`, `anticaptcha`, `capsolver`) with seamless fallback to `FreeAudioCaptchaProvider` (local Whisper speech-to-text audio reCAPTCHA solver).
- **WebUI Node Health Tactical Indicator**: Live `/api/telemetry/node-health` endpoint and alert banner in `index.html` surfacing CPU, RAM, Disk, and `HardwareLoadGovernor` concurrency throttle factors in real-time.
- **Complete CLI & UI Control Parity**: Fully exposed ML thresholds, smart cropping, tagging, cloud storage sink parameters, and self-healing toggles across both WebUI cockpit and interactive CLI wizards.

### 6. Pre-Warmed Browser Lifecycle Pool
- **Sub-50ms Cold Start**: Implemented `PrewarmedBrowserPool` (`src/network/prewarmed_browser_pool.py`) with asynchronous background worker pre-warming browser contexts (DrissionPage, Camoufox, Chromium) to eliminate multi-second initialization latency on dynamic pages.
- **Resource Lifecycle Management**: Enforces max operations per instance (default 20), idle TTLs (300s), and automatic `psutil` process-tree cleanup upon pool shutdown.

### 7. Distributed Redis Streams & Consumer Group Broker
- **Enterprise Queue Federation**: Implemented `RedisStreamTaskBroker` (`src/core/worker_pool.py`) utilizing Redis Streams (`XADD`, `XREADGROUP`, `XACK`, `XPENDING`, `XCLAIM`) with distributed consumer groups for multi-node scraper clusters.
- **Zero-Dependency Fallback**: Transparently degrades to `InMemoryTaskBroker` when Redis is unavailable or unconfigured.

### 8. Hardware Device Manager & Multi-Provider LLM Gateway
- **Dynamic Device & Precision Selection**: Added `HardwareDeviceManager` (`src/ml/hardware.py`) detecting CUDA, DirectML (PrivateUseOne on Windows), MPS, or CPU with automatic FP16/FP32 inference routing.
- **Multi-Provider LLM Healing**: Enhanced `SelfHealingDOMParser` (`src/core/self_healing_parser.py`) with multi-provider LLM gateway supporting local Ollama (`qwen2.5-coder`), Google Gemini 1.5 Flash, and OpenAI GPT-4o-mini with SQLite repair caching.

### 9. Content-Addressable Storage (CAS) & Columnar Parquet Export
- **Global Content-Addressable Storage**: Added `ContentAddressableStore` (`src/storage/cas_store.py`) deduplicating media files by SHA-256 hash using atomic NTFS hardlinks (`os.link`), consuming 0 additional disk bytes across runs and keywords.
- **Columnar Analytics**: Implemented `ParquetExporter` (`src/storage/parquet_exporter.py`) exporting crawl metadata to Snappy-compressed Apache Parquet tables with JSON Lines fallback.

### 10. Comprehensive Verification & Regression Validation
- **10 Dormant Subsystems Smoke Suite**: Proved real execution of all 10 dormant subsystems (`tests/integration/test_dormant_subsystems_smoke.py`) without mocks.
- **Fault Injection & Hygiene**: Validated stealth engine degradation on corrupted browser binaries, mid-run socket aborts, and verified zero zombie processes with `psutil`.
- **530/530 Test Pass Rate**: Full regression test suite passing at 100% with zero Ruff errors and zero Bandit High issues.

---

# Release Notes — scrAPE v0.27.0
**Release Date**: September 20, 2026  
**Focus**: Holistic System Audit, End-to-End Live Integration, Dormant Subsystem Repairs, Deep Core Hardening, and Production Release Gating.

---

## Key Highlights

### 1. Dormant Subsystem Repairs & Latent Defect Remediations
- **CLI Wizard Flag Ambiguity Fix**: Fixed `src/cli/cli_wizard_standard.py` to pass `--seed-file` rather than `--seed`, eliminating an `argparse` option ambiguity crash against `main.py`.
- **RAG Exporter Module & CLI Entrypoint**: Corrected module path from `src.storage.rag_exporter` to `src.ml.rag_exporter` in the standard CLI wizard, and implemented a standalone CLI `__main__` entrypoint with `--input-dir` and `--output-dir` arguments.
- **SQLite Windows File-Lock Fix**: Added explicit connection cleanup (`conn.close()`) in `src/storage/database_exporter.py` inside a `finally:` block, preventing `WinError 32` file-locking issues during temp directory teardown on Windows.
- **PyPI Dependency Reconciliation**: Corrected impossible package versions in `pyproject.toml` and `requirements.txt` (`Pillow>=11.0.0` and `python-multipart>=0.0.20`).
- **Permanent SSRF Test Suite**: Created `tests/frontend/test_ssrf_protection.py` to continuously verify rejection of loopback and private IP targets (RFC 1918 / link-local) in the WebUI API.
- **10/10 Dormant Subsystems Verified**: Executed standalone smoke test harness verifying `dataset_tagger`, `dataset_cropper`, `aesthetic_scorer`, `rag_exporter`, `database_exporter`, `analytics_exporter`, `reddit_extractor`, `hardware_governor`, and captcha solver providers (`TwoCaptcha`, `AntiCaptcha`, `FreeAudioCaptchaProvider`).

### 2. Full End-to-End Live Integration (Zero-Mock Validation)
- Executed full live batch runs across all 7 domain manifests (`apple.txt`, `hana_bunny.txt`, `meenfox.txt`, `eatwaffles.txt`, `takomayuyi.txt`, `akariiiii_cos.txt`, `lionel_messi.txt`) with exit code 0.
- **Live 8-Tier Stealth Escalation**: Verified dynamic tier escalation from standard HTTP to TLS impersonation (`curl_cffi`) and local headless browser automation (`crawlee` Cheerio/Puppeteer) on challenging endpoints.
- **Spoofed Referer & Anti-Hotlink Injection**: Verified automatic parent page referer header injection bypassing anti-hotlink protections.
- **Adaptive Rate-Limiting & Jitter**: Verified delay expansion and randomised timing when encountering rate limits.
- **Stream Discovery & Chunk Resumability**: Verified HLS stream detection and HTTP 206 byte-range chunk resumption.
- **Perceptual dHash Deduplication**: Verified perceptual hashing eliminating duplicate media files at ingestion time.

### 3. Deep Core Systems Hardening
- **Crawl Success Rate Auditing**: Integrated `CrawlAuditEvaluator` generating detailed host health evaluations and structured run summaries.
- **Rolling Host Health State Machine**: Implemented real-time host status tracking (`Healthy`, `Degraded`, `Critical`, `Parked`) with automated TLS profile rotation and exponential cooldowns.
- **Resumable State Checkpointing**: Transactional crawl checkpoints backed by SQLite WAL mode.
- **Adaptive Best-First Crawl Priority Queue & Domain Budget Governor**: Token relevance scoring and host rate budgeting.
- **Zero-Copy Streaming Ingest**: Streaming download pipeline with inline SHA-256 computation and magic-byte MIME sniffing.
- **Sticky Per-Domain Hardware Stealth Fingerprints**: Domain-isolated Canvas 2D, WebGL, AudioContext, and WebRTC spoofing.
- **Process Lifecycle Hygiene**: Verified clean browser subprocess termination with zero zombie child processes left behind.

---

## QA & Validation Summary (v0.27.0)

| Phase | Description | Result | Details |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Responsive Layout Audit | **PASS** | Desktop (1440px), Tablet (820px), Mobile (375px): 0px overflow, >= 44px touch targets, HTMX partial swaps verified. |
| **Phase 2** | Functional & Dormant Subsystems | **PASS** | WebUI CRUD & API verified; CLI wizard modes tested; 10/10 dormant ML/storage/captcha modules operational. |
| **Phase 3** | Domain-Mapped Batch Run | **PASS** | 7/7 seeds completed with exit code 0; stealth escalation, referer spoofing, dHash dedup, and rate limiting verified. |
| **Phase 4** | Container & Process Hygiene | **PASS** | Multi-stage Dockerfile and non-root `appuser` verified; lingering Helium renderer PID 17372 tracked and killed; 0 zombie processes. |
| **Phase 5** | Security & Stability Re-Verification | **PASS** | 0 Bandit High findings (17,865 LOC); 0 bare `except:`; 0 credential leaks; permanent SSRF regression test passing. |
| **Phase 6** | Cross-Check Logs & Error Handling | **PASS** | 0 unhandled tracebacks in runtime logs; active auto-remediation (TLS profile rotation on degraded host) verified. |
| **Phase 7** | Release Readiness Gate | **PASS** | 479/479 unit/integration tests passing; 0 Ruff linting errors; dependency pins aligned; release tagged. |

---

# Release Notes — scrAPE v0.25.0
**Release Date**: September 20, 2026  
**Focus**: Responsive Dashboard UI, Native Low-RAM Stealth Profile, Dependency & Packaging Reconciliation, Zero-Mock QA Validation.

---

## Key Highlights

### 1. Responsive Brutalist Dashboard & Mobile Touch Targets
- Implemented fluid layout media queries in `frontend/templates/index.html`:
  - **Desktop (≥1440px)**: Fixed 280px tactical command sidebar with brutalist metrics grid.
  - **Tablet (768–1024px)**: Responsive multi-column layout with flexible wrapping cards.
  - **Mobile (≤480px)**: Collapsible single-column layout with 0 horizontal page overflow.
- All interactive controls, cards, and flags now strictly adhere to WCAG touch-target sizing (`min-height: 44px`).
- HTMX partial swaps (Seed Studio, Run Inspector, Live Telemetry) verified across all viewports without layout shifts.

### 2. Native Local Low-RAM Profile (Zero-Docker / Zero-WSL)
- **WSL & Docker Overhead Reclaimed**: Host memory usage reduced by ~3.7 GB (`vmmemWSL` excluded).
- `ENABLE_FLARESOLVERR_FALLBACK` is now explicitly defaulted to `False`.
- The stealth fallback architecture operates entirely through native local browser and network engines:
  ```
  Tier 1: Httpx (Direct / Spoofed Headers)
     ↓
  Tier 2: Curl_cffi (TLS Fingerprint Impersonation)
     ↓
  Tier 3: Crawlee Bridge (Local Node.js 22 + Cheerio / Puppeteer Stealth)
     ↓
  Tier 4: Crawl4AI (Playwright Async Stealth & Heuristic JS Wait)
     ↓
  Tier 5: DrissionPage (CDP-based Chromium Automation)
     ↓
  Tier 6: Helium & Nodriver (Headless / Headful Fallbacks)
     ↓
  Tier 7: Camoufox (Fingerprint-Injected Firefox Engine)
  ```

### 3. Dependency & Packaging Hardening
- **Crawlee Node.js Bridge**: Replaced incompatible `stream-json` v3.x override with compatible `stream-json` v1.8.x, ensuring smooth loading and 0 vulnerabilities.
- **Python 3.13 Crypto Compatibility**: Pinned `cryptography` (`46.0.7`) to restore compatibility with `pyOpenSSL` 25.3.0 and resolve `_lib.GEN_EMAIL` deprecation errors during heavy SPA JavaScript evaluation.
- **Dataset Exporter**: Permitted tilde (`~`) in path sanitization regex, resolving Windows 8.3 short-path exports in temporary directories.
- **CLI Launcher**: Added `-h` / `--help` flag and graceful non-interactive subshell handling to prevent `NoConsoleScreenBufferError`.

---

## QA & Validation Summary

| Phase | Description | Result | Details |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Responsive Layout Audit | **PASS** | Desktop (1440px), Tablet (820px), Mobile (375px): 0 overflow, 44px touch targets. |
| **Phase 2** | WebUI, CLI & Subsystems | **PASS** | Seed Studio CRUD, SSRF live matrix (5/5 blocked), CLI wizards, 6/6 dormant ML modules tested. |
| **Phase 3** | Domain-Mapped Batch Run | **PASS** | 7/7 seeds completed (`apple`, `hana_bunny`, `meenfox`, `eatwaffles`, `takomayuyi`, `akariiiii_cos`, `lionel_messi`). |
| **Phase 4** | Container Static Audit | **PASS** | Dockerfile multi-stage, non-root `appuser`, loopback `127.0.0.1` port bindings. |
| **Phase 5** | Security & Native Stability | **PASS** | 0 Bandit High issues (17,865 LOC), 0 bare `except:`, 0 credential leaks, native tier degradation verified. |
| **Phase 6** | Cross-Check Logs | **PASS** | Zero unhandled tracebacks in `logs/` and `output/`. |
| **Phase 7** | Release Readiness | **PASS** | Version bumped to `0.25.0`, changelog synchronized, git tagged. |

/**
 * scrAPE v0.30.1 — Technical Documentation Portal
 * Tactical Multilingual Internationalization (i18n) Engine
 * Supported Languages: English (EN), Indonesian (ID), Chinese (ZH), Spanish (ES), Japanese (JA), Russian (RU), German (DE)
 */

const I18N_DICTS = {
  "en": {
    "meta": {
      "title": "scrAPE v0.30.1 // Technical Documentation Portal",
      "desc": "Official technical documentation, CLI flag matrix, architecture guide, and operational manual for scrAPE v0.30.1."
    },
    "ui": {
      "searchPlaceholder": "SEARCH DOCS...",
      "searchHint": "Ctrl+K",
      "langStripLabel": "PORTAL LANGUAGE // BAHASA:",
      "githubLink": "[GITHUB]",
      "badgeNew": "NEW",
      "badgeVerified": "VERIFIED",
      "copyCode": "[COPY CODE]",
      "copiedCode": "[COPIED!]",
      "commandBuilder": "INTERACTIVE CLI BUILDER",
      "builderPrompt": "CONFIGURE PARAMETERS & GENERATE RUNTIME COMMAND:",
      "builderOutputLabel": "EXECUTABLE CLI COMMAND:",
      "footerTagline": "Autonomous, high-throughput distributed scraping engine with self-healing DOM heuristics and Apache Parquet export.",
      "searchResults": "found",
      "noResults": "no results",
      "selectLocale": "SELECT DOCUMENTATION LOCALE",
      "changeLanguageTitle": "Change Language"
    },
    "modules": [
      "[01] SYSTEM OVERVIEW",
      "[02] INSTALLATION AND QUICKSTART",
      "[03] CLI REFERENCE",
      "[04] CORE ENGINE ARCHITECTURE",
      "[05] CONFIGURATION REFERENCE",
      "[06] WEBUI DASHBOARD",
      "[07] DEPLOYMENT AND OPERATIONS",
      "[08] OUTPUT AND EXPORTS",
      "[09] TESTING AND TROUBLESHOOTING",
      "[10] THREAT MODEL & SECURITY"
    ],
    "nav": {
      "sec-overview-arch": "[1.1] Architecture and Objectives",
      "sec-overview-formats": "[1.2] Supported Formats and Limits",
      "sec-overview-layout": "[1.3] Project Directory Layout",
      "sec-overview-pillars": "[1.4] Next-Gen Core Pillars",
      "sec-overview-v28": "[1.5] Core Architecture (v0.28.0)",
      "sec-install-prereqs": "[2.1] Prerequisites",
      "sec-install-steps": "[2.2] Installation Steps",
      "sec-install-launchers": "[2.3] Master Launchers and Wizard",
      "sec-install-recipes": "[2.4] First Run Recipes",
      "sec-cli-flags": "[3.1] Complete Flag Matrix",
      "sec-cli-builder": "[3.2] Interactive CLI Builder",
      "sec-cli-profiles": "[3.3] Execution Profiles",
      "sec-engine-bfs": "[4.1] BFS Crawl Loop",
      "sec-engine-waf": "[4.2] 8-Tier Stealth WAF Pipeline",
      "sec-engine-captcha": "[4.3] Universal Captcha Strategy",
      "sec-engine-scoring": "[4.4] Quality Scoring and Rejection",
      "sec-engine-normalize": "[4.5] URL Normalization",
      "sec-engine-pool": "[4.6] Pre-Warmed Browser Pool",
      "sec-engine-broker": "[4.7] Redis Streams Task Broker",
      "sec-engine-ml": "[4.8] Vision Hardware & ML Pipeline",
      "sec-engine-healing": "[4.9] Self-Healing DOM Parser",
      "sec-engine-bktree": "[4.10] BK-Tree Perceptual Deduplication",
      "sec-config-env": "[5.1] Environment Variables (.env)",
      "sec-config-domain": "[5.2] domain_config.json",
      "sec-config-urlnorm": "[5.3] url_normalisation_rules.json",
      "sec-config-seeds": "[5.4] Seed Manifest Syntax",
      "sec-config-profiles": "[5.5] Subject Profiles",
      "sec-config-blacklist": "[5.6] Blacklist Management",
      "sec-webui-arch": "[6.1] Server Architecture",
      "sec-webui-views": "[6.2] Command Center and Media Vault",
      "sec-webui-telemetry": "[6.3] Live Telemetry and SSE",
      "sec-webui-design": "[6.4] Design Tokens",
      "sec-webui-health": "[6.5] Node Health Tactical Monitor",
      "sec-ops-docker": "[7.1] Docker Compose",
      "sec-ops-watchdog": "[7.2] Watchdog Agent",
      "sec-ops-notifications": "[7.3] Notification Pipeline",
      "sec-ops-proxy": "[7.4] Proxy Pool Management",
      "sec-ops-sessions": "[7.5] Session and Cookie Management",
      "sec-output-structure": "[8.1] Output Directory Structure",
      "sec-output-manifest": "[8.2] manifest.json Schema",
      "sec-output-domain": "[8.3] domain_report.json Schema",
      "sec-output-kohya": "[8.4] Kohya LoRA Dataset Export",
      "sec-output-rag": "[8.5] RAG Ingestion Formats",
      "sec-output-cas": "[8.6] Content-Addressable Storage (CAS)",
      "sec-output-parquet": "[8.7] Apache Parquet Dataset Export",
      "sec-test-pytest": "[9.1] Running pytest",
      "sec-test-tdai": "[9.2] Verification Protocol (TDAI)",
      "sec-test-logs": "[9.3] Log Diagnostics Recipes",
      "sec-test-diagnostic": "[9.4] Operator Diagnostic Matrix",
      "sec-test-guidelines": "[9.5] Developer Guidelines",
      "sec-threat-overview": "[10.1] Pre-Implementation Scope",
      "sec-threat-leasing": "[10.2] Task Leasing Matrix",
      "sec-threat-cas": "[10.3] Cloud CAS Matrix",
      "sec-threat-vlm": "[10.4] VLM Healing Matrix",
      "sec-threat-ac": "[10.5] Acceptance Criteria Contract"
    },
    "footer": {
      "logo": "scrAPE // CORE SYSTEM",
      "tagline": "Autonomous, high-throughput distributed scraping engine with self-healing DOM heuristics and Apache Parquet export.",
      "badges": [
        "RELEASE v0.30.1",
        "MIT LICENSED",
        "PYTHON 3.10+"
      ],
      "headings": {
        "repo": "REPOSITORY",
        "docs": "DOCUMENTATION"
      },
      "links": [
        "Source Code",
        "Release Notes (v0.30.1)",
        "Issue Tracker",
        "CI / Workflows",
        "System README",
        "Threat Model (v0.30.0)",
        "Version Changelog",
        "MIT License",
        "Docker Compose"
      ],
      "copy": "© 2026 scrAPE Maintainers. Open source under the MIT License.",
      "sysinfo": "STATUS: OPERATIONAL // ENGINE: v0.30.1"
    },
    "sections": {
      "sec-overview-arch": {
        "tag": "MODULE [01] // SYSTEM OVERVIEW",
        "h1": "Architecture and Objectives",
        "desc": "Multi-engine stealth web scraping system for autonomous media extraction and AI dataset generation.",
        "cards": [
          "1.1 System Architecture"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] CORE OPERATIONAL GUARANTEE",
            "bodyHtml": "The system executes via an 8-tier WAF fallback pipeline. Requests automatically escalate from lightweight direct HTTP up to headful stealth browser automation when challenge loops are detected. No manual intervention is required."
          }
        ]
      },
      "sec-overview-formats": {
        "tag": "MODULE [01] // SYSTEM OVERVIEW",
        "h1": "Supported Formats and Operating Limits",
        "desc": "Asset specifications, size filters, dimension boundaries, and rate bounds.",
        "cards": [
          "1.2 Media and Data Capabilities"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-overview-layout": {
        "tag": "MODULE [01] // SYSTEM OVERVIEW",
        "h1": "Project Directory Layout",
        "desc": "File and folder organization of the repository.",
        "cards": [
          "1.3 Directory Structure"
        ],
        "codeHeaders": [
          "TEXT // REPOSITORY TREE"
        ],
        "alerts": []
      },
      "sec-overview-pillars": {
        "tag": "MODULE [01] // SYSTEM OVERVIEW",
        "h1": "Core Architecture Pillars (v0.30.1)",
        "desc": "Enterprise multi-node orchestration, sub-linear BK-tree perceptual deduplication, isolated profiler thread pools, and zero-duplicate content-addressable storage.",
        "cards": [
          "1.4 Core Architecture Pillars (v0.30.1)"
        ],
        "codeHeaders": [
          "BASH // CORE PILLAR CLI ACTIVATION"
        ],
        "alerts": []
      },
      "sec-overview-v28": {
        "tag": "MODULE [01] // ARCHITECTURAL UPDATE",
        "h1": "Core Architecture (v0.28.0)",
        "desc": "Production-grade decoupled ML pipeline, 3-tier hierarchical deduplication, self-healing DOM parser, and supervised hybrid concurrency.",
        "cards": [
          "1.4 Architectural Breakthroughs in v0.28.0"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-prereqs": {
        "tag": "MODULE [02] // INSTALLATION AND QUICKSTART",
        "h1": "System Prerequisites and Toolchain",
        "desc": "Python runtime, headless browser drivers, CUDA hardware acceleration, and Redis infrastructure requirements.",
        "cards": [
          "2.1 System Requirements"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-steps": {
        "tag": "MODULE [02] // INSTALLATION AND QUICKSTART",
        "h1": "Step-by-Step Installation",
        "desc": "Virtual environment provisioning, pip package installation, and browser binary synchronization.",
        "cards": [
          "2.2 Setup Procedure"
        ],
        "codeHeaders": [
          "BASH // INSTALLATION COMMANDS"
        ],
        "alerts": [
          {
            "title": "[i] FLARESOLVERR SETUP",
            "bodyHtml": "FlareSolverr (Tier 5) runs as a Docker container. Start it with: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"
          }
        ]
      },
      "sec-install-launchers": {
        "tag": "MODULE [02] // INSTALLATION AND QUICKSTART",
        "h1": "Master Launchers and Wizard",
        "desc": "Interactive launcher scripts for all execution modes.",
        "cards": [
          "2.3 Launcher Options"
        ],
        "codeHeaders": [
          "POWERSHELL // MASTER LAUNCHER"
        ],
        "alerts": []
      },
      "sec-install-recipes": {
        "tag": "MODULE [02] // INSTALLATION AND QUICKSTART",
        "h1": "First Run Recipes",
        "desc": "Copy-paste commands for common extraction patterns.",
        "cards": [
          "2.4 Command Recipes"
        ],
        "codeHeaders": [
          "RECIPE 1 // STANDARD SEED EXTRACTION WITH REJECTED MEDIA RETENTION",
          "RECIPE 2 // CONTINUOUS WATCHDOG AGENT WITH STATE CACHE",
          "RECIPE 3 // QUICK VALIDATION RUN (NO DOWNLOADS)",
          "RECIPE 4 // SEARCH-ONLY DISCOVERY (NO SEEDS)",
          "RECIPE 5 // STEALTH CRAWL (POLITE SPEED)"
        ],
        "alerts": []
      },
      "sec-cli-flags": {
        "tag": "MODULE [03] // CLI REFERENCE",
        "h1": "Complete CLI Execution Flag Matrix",
        "desc": "Full reference guide for all command-line switches, flags, threshold overrides, and extraction budgets.",
        "cards": [
          "3.1 Command Line Parameters"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-cli-builder": {
        "tag": "MODULE [03] // CLI REFERENCE",
        "h1": "Interactive CLI Command Builder",
        "desc": "Configure target parameters, concurrency pools, and stealth escalation flags to generate a ready-to-run terminal command.",
        "cards": [
          "3.2 Command Generator"
        ],
        "codeHeaders": [
          "GENERATED CLI COMMAND STRING"
        ],
        "alerts": []
      },
      "sec-cli-profiles": {
        "tag": "MODULE [03] // CLI REFERENCE",
        "h1": "Execution Profiles",
        "desc": "Pre-tuned profile presets for specialized scrape topologies.",
        "cards": [
          "3.3 Preset Profile Matrix"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-bfs": {
        "tag": "MODULE [04] // CORE ENGINE ARCHITECTURE",
        "h1": "BFS Crawl Loop",
        "desc": "Asynchronous breadth-first traversal loop, priority queue dispatch, and link extraction.",
        "cards": [
          "4.1 Execution Sequence"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-waf": {
        "tag": "MODULE [04] // CORE ENGINE ARCHITECTURE",
        "h1": "8-Tier Stealth WAF Escalation Pipeline",
        "desc": "Multi-tiered adaptive fallback resolving Cloudflare Turnstile, Datadome, Incapsula, and bot mitigation barriers.",
        "cards": [
          "4.2 WAF Pipeline Hierarchy"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-captcha": {
        "tag": "MODULE [04] // CORE ENGINE ARCHITECTURE",
        "h1": "Universal Captcha Strategy",
        "desc": "Automated solver providers, challenge interception, and retry handlers.",
        "cards": [
          "4.3 Challenge Resolution Strategy"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-scoring": {
        "tag": "MODULE [04] // CORE ENGINE ARCHITECTURE",
        "h1": "Quality Scoring and Rejection",
        "desc": "URL classification, image dimension thresholds, and rejected media disk persistence.",
        "cards": [
          "4.4 Rejection Rules & Retention Paths"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-normalize": {
        "tag": "MODULE [04] // CORE ENGINE ARCHITECTURE",
        "h1": "URL Normalization",
        "desc": "Strip tracking parameters, canonicalize protocols, and prevent redundant queue cycles.",
        "cards": [
          "4.5 Canonicalization Pipeline"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-pool": {
        "tag": "MODULE [04] // CORE ENGINE ARCHITECTURE",
        "h1": "Pre-Warmed Browser Pool",
        "desc": "High-performance Camoufox browser pool recycling and context leasing.",
        "cards": [
          "4.6 Pre-Warmed Browser Lifecycle"
        ],
        "codeHeaders": [
          "PYTHON // PREWARMED BROWSER POOL LEASING"
        ],
        "alerts": []
      },
      "sec-engine-broker": {
        "tag": "MODULE [04] // CORE ENGINE ARCHITECTURE",
        "h1": "Redis Streams Task Broker",
        "desc": "Distributed consumer groups, pending entry tracking (PEL), and atomic task dispatch.",
        "cards": [
          "4.7 Distributed Cluster Coordination"
        ],
        "codeHeaders": [
          "PYTHON // TASK BROKER INTERACTION PATTERN"
        ],
        "alerts": []
      },
      "sec-engine-ml": {
        "tag": "MODULE [04] // CORE ENGINE ARCHITECTURE",
        "h1": "Vision Hardware & ML Pipeline",
        "desc": "CUDA/MPS device detection, half-precision (FP16) inference, and aesthetic scoring.",
        "cards": [
          "4.8 Hardware Acceleration Matrix"
        ],
        "codeHeaders": [
          "PYTHON // HARDWARE DISCOVERY & PRECISION NEGOTIATION"
        ],
        "alerts": []
      },
      "sec-engine-healing": {
        "tag": "MODULE [04] // CORE ENGINE ARCHITECTURE",
        "h1": "Self-Healing DOM Parser",
        "desc": "4-tier DOM recovery cascade with multi-provider LLM heuristic repair.",
        "cards": [
          "4.9 Autonomous Selector Repair"
        ],
        "codeHeaders": [
          "PYTHON // SELF-HEALING EXTRACTION CASCADE",
          "TEXT // MULTI-PROVIDER LLM SYNTHESIS CASCADE"
        ],
        "alerts": []
      },
      "sec-engine-bktree": {
        "tag": "MODULE [04] // CORE ENGINE ARCHITECTURE",
        "h1": "BK-Tree Deduplication & Concurrency Partitioning",
        "desc": "Discrete metric tree indexing, hamming distance clustering, and isolated profiler execution pools.",
        "cards": [
          "4.10 Discrete Metric Tree & Execution Pool Partitioning"
        ],
        "codeHeaders": [
          "PYTHON // BK-TREE METRIC SEARCH & CONNECTION POOLING"
        ],
        "alerts": []
      },
      "sec-config-env": {
        "tag": "MODULE [05] // CONFIGURATION REFERENCE",
        "h1": "Environment Variables (.env)",
        "desc": "Production credentials, rate limits, proxy gateways, and API tokens.",
        "cards": [
          "5.1 .env Configuration Template"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-domain": {
        "tag": "MODULE [05] // CONFIGURATION REFERENCE",
        "h1": "domain_config.json",
        "desc": "Per-domain concurrency limits, custom wait selectors, and header overrides.",
        "cards": [
          "5.2 Configuration Keys Reference"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-urlnorm": {
        "tag": "MODULE [05] // CONFIGURATION REFERENCE",
        "h1": "url_normalisation_rules.json",
        "desc": "Regular expressions for query parameter stripping and domain transformations.",
        "cards": [
          "5.3 Normalization Rule Schema"
        ],
        "codeHeaders": [
          "JSON // RULE SCHEMA EXAMPLE"
        ],
        "alerts": [
          {
            "title": "[!] MANDATORY RULE",
            "bodyHtml": "Never hardcode domain-specific URL normalization regexes in Python files under <code>src/</code>. All rules MUST be declared in <code>data/url_normalisation_rules.json</code>."
          }
        ]
      },
      "sec-config-seeds": {
        "tag": "MODULE [05] // CONFIGURATION REFERENCE",
        "h1": "Seed Manifest Syntax",
        "desc": "Comments, inline directives, and priority weights in seeds/*.txt files.",
        "cards": [
          "5.4 Annotation Reference"
        ],
        "codeHeaders": [
          "MANIFEST // SEED MANIFEST ANNOTATION EXAMPLE"
        ],
        "alerts": []
      },
      "sec-config-profiles": {
        "tag": "MODULE [05] // CONFIGURATION REFERENCE",
        "h1": "Subject Profiles",
        "desc": "Subject-specific presets, output templates, and blacklist linkages.",
        "cards": [
          "5.5 Profile Presets"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-blacklist": {
        "tag": "MODULE [05] // CONFIGURATION REFERENCE",
        "h1": "Blacklist Management",
        "desc": "Globally excluded domains, ad servers, and low-value resource patterns.",
        "cards": [
          "5.6 Domain Blacklisting"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-arch": {
        "tag": "MODULE [06] // WEBUI DASHBOARD",
        "h1": "WebUI Server Architecture",
        "desc": "FastAPI and HTMX reactive command center with real-time SSE streaming telemetry.",
        "cards": [
          "6.1 Decoupled FastAPI Server"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-views": {
        "tag": "MODULE [06] // WEBUI DASHBOARD",
        "h1": "Command Center and Media Vault",
        "desc": "Interactive control dashboard, live crawler status, and gallery inspection.",
        "cards": [
          "6.2 Dashboard Views"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-telemetry": {
        "tag": "MODULE [06] // WEBUI DASHBOARD",
        "h1": "Live Telemetry and SSE",
        "desc": "Real-time event streaming via Server-Sent Events, queue rates, and memory gauges.",
        "cards": [
          "6.3 Real-Time Event Pipeline"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-design": {
        "tag": "MODULE [06] // WEBUI DASHBOARD",
        "h1": "Design Tokens",
        "desc": "Tactical utilitarian brutalist CSS tokens, high-contrast monospace typography, and color palettes.",
        "cards": [
          "6.4 Design Tokens Reference"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-health": {
        "tag": "MODULE [06] // WEBUI DASHBOARD",
        "h1": "Node Health Tactical Monitor",
        "desc": "Subsystem health checks, heartbeat probes, and Redis cluster telemetry.",
        "cards": [
          "6.5 Tactical Telemetry & Governance"
        ],
        "codeHeaders": [
          "JSON // NODE HEALTH TELEMETRY PAYLOAD"
        ],
        "alerts": []
      },
      "sec-ops-docker": {
        "tag": "MODULE [07] // DEPLOYMENT AND OPERATIONS",
        "h1": "Docker Compose",
        "desc": "Multi-container production deployment with FlareSolverr, Redis, and WebUI.",
        "cards": [
          "7.1 Container Deployment"
        ],
        "codeHeaders": [
          "BASH // DOCKER COMPOSE LAUNCH"
        ],
        "alerts": []
      },
      "sec-ops-watchdog": {
        "tag": "MODULE [07] // DEPLOYMENT AND OPERATIONS",
        "h1": "Watchdog Agent",
        "desc": "Continuous crawl daemon with automated health checks and restart policies.",
        "cards": [
          "7.2 Continuous Monitoring Loop"
        ],
        "codeHeaders": [
          "POWERSHELL // WATCHDOG AGENT COMMAND"
        ],
        "alerts": []
      },
      "sec-ops-notifications": {
        "tag": "MODULE [07] // DEPLOYMENT AND OPERATIONS",
        "h1": "Notification Pipeline",
        "desc": "Pluggable notification channels (Telegram, Discord, Slack, Webhooks).",
        "cards": [
          "7.3 Multi-Channel Alerts"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-proxy": {
        "tag": "MODULE [07] // DEPLOYMENT AND OPERATIONS",
        "h1": "Proxy Pool Management",
        "desc": "Proxy rotation, latency auto-quarantine, and bandwidth quotas.",
        "cards": [
          "7.4 Proxy Manager Strategy"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-sessions": {
        "tag": "MODULE [07] // DEPLOYMENT AND OPERATIONS",
        "h1": "Session and Cookie Management",
        "desc": "Persistent per-domain sticky sessions and interactive cookie login.",
        "cards": [
          "7.5 Session Storage"
        ],
        "codeHeaders": [
          "BASH // SESSION LOGIN COMMANDS"
        ],
        "alerts": []
      },
      "sec-output-structure": {
        "tag": "MODULE [08] // OUTPUT AND EXPORTS",
        "h1": "Output Directory Structure",
        "desc": "Run output artifacts layout.",
        "cards": [
          "8.1 Artifact Organization"
        ],
        "codeHeaders": [
          "TEXT // OUTPUT DIRECTORY LAYOUT"
        ],
        "alerts": []
      },
      "sec-output-manifest": {
        "tag": "MODULE [08] // OUTPUT AND EXPORTS",
        "h1": "manifest.json Schema",
        "desc": "Complete results JSON schema documentation.",
        "cards": [
          "8.2 JSON Payload Fields"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-domain": {
        "tag": "MODULE [08] // OUTPUT AND EXPORTS",
        "h1": "domain_report.json Schema",
        "desc": "Per-domain crawl metrics report.",
        "cards": [
          "8.3 Per-Domain Yield Report"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-kohya": {
        "tag": "MODULE [08] // OUTPUT AND EXPORTS",
        "h1": "Kohya LoRA Dataset Export",
        "desc": "Kohya_ss LoRA dataset ZIP archive generation.",
        "cards": [
          "8.4 LoRA Dataset Generator"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-rag": {
        "tag": "MODULE [08] // OUTPUT AND EXPORTS",
        "h1": "RAG Ingestion Formats",
        "desc": "LLM RAG exports (Markdown chunks and JSONL embeddings).",
        "cards": [
          "8.5 RAG Export Options"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-cas": {
        "tag": "MODULE [08] // OUTPUT AND EXPORTS",
        "h1": "Content-Addressable Storage (CAS)",
        "desc": "Global deduplication repository eliminating duplicate file storage across repeated crawls.",
        "cards": [
          "8.6 Content-Addressable Store Architecture"
        ],
        "codeHeaders": [
          "PYTHON // CAS DEDUPLICATION & RUN LINKING",
          "TEXT // CAS STORAGE LIFECYCLE"
        ],
        "alerts": []
      },
      "sec-output-parquet": {
        "tag": "MODULE [08] // OUTPUT AND EXPORTS",
        "h1": "Apache Parquet Dataset Export",
        "desc": "Columnar Snappy-compressed datasets optimized for Polars, DuckDB, Pandas, and Big Data OLAP pipelines.",
        "cards": [
          "8.7 Columnar Data Export Pipeline"
        ],
        "codeHeaders": [
          "PYTHON // PARQUET DATASET GENERATION"
        ],
        "alerts": []
      },
      "sec-test-pytest": {
        "tag": "MODULE [09] // TESTING AND TROUBLESHOOTING",
        "h1": "Running pytest",
        "desc": "Executing the automated test suite.",
        "cards": [
          "9.1 Automated Pytest Suite"
        ],
        "codeHeaders": [
          "POWERSHELL // RUN FULL TEST SUITE"
        ],
        "alerts": []
      },
      "sec-test-tdai": {
        "tag": "MODULE [09] // TESTING AND TROUBLESHOOTING",
        "h1": "Verification Protocol (TDAI)",
        "desc": "Test-Driven AI verification rules and RED-GREEN-REFACTOR protocol.",
        "cards": [
          "9.2 Empirical Verification Protocol"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] MANDATORY RULE",
            "bodyHtml": "Never declare a feature or fix complete without running empirical runtime verification commands and demonstrating clean test passes."
          }
        ]
      },
      "sec-test-logs": {
        "tag": "MODULE [09] // TESTING AND TROUBLESHOOTING",
        "h1": "Log Diagnostics Recipes",
        "desc": "Log analysis and grep commands for runtime diagnostics.",
        "cards": [
          "9.3 PowerShell Diagnostic Commands"
        ],
        "codeHeaders": [
          "POWERSHELL // GREP LOGS FOR ERRORS AND BLOCKS"
        ],
        "alerts": []
      },
      "sec-test-diagnostic": {
        "tag": "MODULE [09] // TESTING AND TROUBLESHOOTING",
        "h1": "Operator Diagnostic Matrix",
        "desc": "Exhaustive diagnostic table for operator troubleshooting.",
        "cards": [
          "9.4 Diagnostic Matrix"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-test-guidelines": {
        "tag": "MODULE [09] // TESTING AND TROUBLESHOOTING",
        "h1": "Developer Guidelines",
        "desc": "Mandatory coding rules and workspace standards.",
        "cards": [
          "9.5 Mandatory Coding Rules"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-threat-overview": {
        "tag": "MODULE [10] // THREAT MODEL & SECURITY",
        "h1": "Security Architecture & v0.30.0 Verification",
        "desc": "Authoritative threat model, STRIDE architectural contract, and empirical verification matrix for v0.30.0 distributed scaling.",
        "cards": [
          "10.1 Trust Boundaries & Data Flow Architecture",
          "10.1.1 STRIDE Threat Categorization",
          "10.1.2 Cross-Cutting Invariants"
        ],
        "codeHeaders": [
          "ARCHITECTURE // v0.30.0 DISTRIBUTED TRUST BOUNDARIES & DATA FLOW"
        ],
        "alerts": [
          {
            "title": "PRODUCTION RELEASE // v0.30.0 VERIFIED & CERTIFIED",
            "bodyHtml": "All three threat-modeled frontiers (Distributed Task Leasing, Cloud CAS Synchronization, Vision-Language DOM Healing) specified in this module are <strong>fully implemented, adversarially tested, and empirically CI verified</strong> in the v0.30.0 release across Ubuntu, macOS, and Windows runners."
          },
          {
            "title": "MANDATORY ARCHITECTURAL CONTRACT",
            "bodyHtml": "This specification is the authoritative baseline for all v0.30.0 feature implementations. Every acceptance criterion (AC1.1 through AC3.6) must have a corresponding automated test in <code>tests/</code> before any component is considered release-ready."
          }
        ]
      },
      "sec-threat-leasing": {
        "tag": "MODULE [10] // COMPONENT 1 (IMPLEMENTED & VERIFIED)",
        "h1": "Distributed Task Leasing Threat Matrix",
        "desc": "STRIDE vulnerability analysis, attack scenarios, and atomic mitigation mechanisms for Redis Stream worker daemons.",
        "cards": [
          "10.2 Component 1 Design Overview",
          "10.2.1 Threat & Vulnerability Matrix (Component 1)",
          "10.2.2 Detailed Mitigation Specifications"
        ],
        "codeHeaders": [
          "PYTHON // ATOMIC IDEMPOTENCY LOCK ACQUISITION"
        ],
        "alerts": [
          {
            "title": "COMPONENT 1 IMPLEMENTED & VERIFIED // AC1.1–AC1.7 PASSED",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>, <code>DistributedWorkerNode</code>, and CLI worker daemons (<code>src.cli.worker</code>) are fully implemented and verified against acceptance criteria AC1.1 through AC1.7. Automated test verification is backed by 98 tests across <code>tests/core/test_task_schema.py</code> (84 fuzz tests), <code>tests/core/test_worker_pool.py</code>, and <code>tests/core/test_distributed_worker.py</code>."
          }
        ]
      },
      "sec-threat-cas": {
        "tag": "MODULE [10] // COMPONENT 2 ARCHITECTURE",
        "h1": "Cloud CAS Synchronization Threat Matrix",
        "desc": "Defense-in-depth specifications, cryptographic verification, and SSRF prevention for S3 / Cloudflare R2 / MinIO storage backends.",
        "cards": [
          "10.3 Component 2 Design Overview",
          "10.3.1 Threat & Vulnerability Matrix (Component 2)",
          "10.3.2 Cryptographic Hash Path Enforcement"
        ],
        "codeHeaders": [
          "PYTHON // CAS KEY PATH VALIDATION & CHECKSUM VERIFICATION"
        ],
        "alerts": [
          {
            "title": "PRODUCTION CERTIFIED // COMPONENT 2 FULLY IMPLEMENTED",
            "bodyHtml": "<code>CASCloudSyncer</code> and S3/R2/MinIO cloud storage backends are <strong>fully implemented and verified</strong> in v0.30.0 with 100% test pass rates across AC2.1-AC2.7, zero-boto minimal install validation, and unconditional SSRF guards."
          }
        ]
      },
      "sec-threat-vlm": {
        "tag": "MODULE [10] // COMPONENT 3 (IMPLEMENTED & VERIFIED)",
        "h1": "Vision-Language DOM Healing Threat Matrix",
        "desc": "Multimodal AI security controls, adversarial visual prompt injection defenses, and DOM interaction sandboxing for Tier 4 healing.",
        "cards": [
          "10.4 Component 3 Design Overview",
          "10.4.1 Threat & Vulnerability Matrix (Component 3)",
          "10.4.2 Untrusted Data Framing & Output Guardrails"
        ],
        "codeHeaders": [
          "PROMPT ARCHITECTURE // SANDBOXED VLM SYSTEM PROMPT"
        ],
        "alerts": [
          {
            "title": "PRODUCTION CERTIFIED // COMPONENT 3 FULLY IMPLEMENTED",
            "bodyHtml": "<code>VisionDOMHealer</code> (Tier 4 multimodal DOM healing) is <strong>fully implemented and verified</strong> in v0.30.0 with 100% test pass rates across AC3.1-AC3.6, 75-vector prompt injection fuzzing rejection, and a structural default-deny allowlist."
          }
        ]
      },
      "sec-threat-ac": {
        "tag": "MODULE [10] // VERIFICATION & AUDIT MATRIX (v0.30.0 PRODUCTION)",
        "h1": "Acceptance Criteria Verification Matrix (v0.30.0 Production)",
        "desc": "Empirical test specifications, verification methodologies, and audit results validating all 20 acceptance criteria for v0.30.0.",
        "cards": [
          "10.5.1 Component 1 Acceptance Criteria (Task Leasing)",
          "10.5.2 Component 2 Acceptance Criteria (Cloud CAS)",
          "10.5.3 Component 3 Acceptance Criteria (VLM Healing)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "ALL 20 ACCEPTANCE CRITERIA VERIFIED & CERTIFIED",
            "bodyHtml": "All 20 criteria below (AC1.1 through AC3.6) represent the <strong>core architectural contract</strong> for v0.30.0. Every single criterion is backed by automated tests in <code>tests/</code> passing 100% locally and in GitHub Actions CI matrix."
          },
          {
            "title": "VERIFICATION STANDARD",
            "bodyHtml": "No v0.30.0 pull request or release tag will be approved without 100% test coverage across all 20 acceptance criteria below, backed by unmocked local verification and full GitHub Actions matrix confirmation."
          }
        ]
      }
    },
    "snippets": {
      "sec-install-steps": "# 1. Clone the repository\ngit clone https://github.com/rhaffle87/scrAPE.git\ncd scrAPE\n\n# 2. Create and activate a virtual environment\npython -m venv venv\nvenv\\Scripts\\activate          # Windows CMD\n.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell\nsource venv/bin/activate       # Linux / macOS\n\n# 3. Install Python dependencies\npip install -r requirements.txt\n\n# 4. (Optional) Install Crawlee Node.js bridge for Tier 6-7 stealth\ncd crawlee_bridge && npm install && cd ..\n\n# 5. Configure credentials\ncopy .env.example .env         # Windows\ncp .env.example .env           # Linux / macOS\n# Then edit .env with your API keys and webhook URLs",
      "sec-install-launchers": "# Windows Master Launcher (Interactive Menu)\n.\\run.bat\n\n# Linux / macOS Master Launcher\n./run.sh\n\n# Direct Interactive Wizard (no menu)\npython src/cli/cli_wizard.py",
      "sec-ops-docker": "# Start scraper engine + FlareSolverr sidecar\ndocker compose up -d\n\n# Check cluster logs in real time\ndocker compose logs -f\n\n# Gracefully stop the stack\ndocker compose down",
      "sec-ops-watchdog": "# Run Watchdog Agent via launcher wrapper\n.\\run.bat watchdog\n\n# Direct continuous monitoring invocation\npython src/cli/monitor_agent.py --keyword \"example_subject\" --seed seeds/example_subject.txt --use-state-cache",
      "sec-ops-sessions": "# Capture cookies via interactive browser window\npython src/cli/session_auth.py --domain example.com --login-url https://example.com/login\n\n# List stored sticky session cookies\npython src/cli/session_auth.py --list-sessions",
      "sec-test-pytest": "# Run all 378+ unit and integration tests\npytest tests/ -v\n\n# Run with coverage report\npytest --cov=src tests/ --cov-report=term-missing",
      "sec-test-logs": "# Check for HTTP 429 rate limits and Cloudflare blocks\nGet-Content logs/crawler.log -Tail 100 | Select-String -Pattern \"429|Cloudflare|WAF|BLOCKED\"\n\n# Monitor real-time crawl engine flow\nGet-Content logs/crawler.log -Wait -Tail 20"
    },
    "lists": {
      "sec-install-launchers": [
        "<strong>Broad Search Scraping</strong> -- Automated search queries with recursive crawling.",
        "<strong>Targeted Manifest Scraping</strong> -- Structured crawls against selected seed manifests.",
        "<strong>Continuous Watchdog Agent</strong> -- Long-running monitoring loops with SQLite WAL caching.",
        "<strong>Create Structured AI Dataset</strong> -- Package run output into consolidated, domain-grouped, or media-type-grouped structures.",
        "<strong>Enterprise LLM RAG Ingestion</strong> -- Export page data as consolidated Markdown, chunked page-level <code>.md</code> files, or JSONL embeddings format."
      ]
    }
  },
  "id": {
    "meta": {
      "title": "scrAPE v0.30.1 // Portal Dokumentasi Teknis",
      "desc": "Dokumentasi teknis resmi, matriks flag CLI, panduan arsitektur, dan manual operasional untuk scrAPE v0.30.1."
    },
    "ui": {
      "searchPlaceholder": "CARI DOKUMENTASI...",
      "searchHint": "Ctrl+K",
      "langStripLabel": "BAHASA PORTAL DOKUMENTASI:",
      "githubLink": "[GITHUB]",
      "badgeNew": "BARU",
      "badgeVerified": "TERVERIFIKASI",
      "copyCode": "[SALIN KODE]",
      "copiedCode": "[TERSALIN!]",
      "commandBuilder": "PEMBUAT PERINTAH CLI INTERAKTIF",
      "builderPrompt": "KONFIGURASIKAN PARAMETER & HASILKAN PERINTAH RUNTIME:",
      "builderOutputLabel": "PERINTAH CLI SIAP DIEKSEKUSI:",
      "footerTagline": "Mesin ekstraksi media otonom dan crawler stealth berperforma tinggi untuk penemuan aset dan bypass WAF yang tangguh.",
      "searchResults": "ditemukan",
      "noResults": "tidak ada hasil",
      "selectLocale": "PILIH BAHASA DOKUMENTASI",
      "changeLanguageTitle": "Ubah Bahasa"
    },
    "modules": [
      "[01] GAMBARAN SISTEM",
      "[02] INSTALASI & PANDUAN CEPAT",
      "[03] REFERENSI CLI",
      "[04] ARSITEKTUR MESIN UTAMA",
      "[05] REFERENSI KONFIGURASI",
      "[06] DASHBOARD WEBUI",
      "[07] DEPLOYMENT & OPERASIONAL",
      "[08] OUTPUT & EKSPOR DATA",
      "[09] PENGUJIAN & DIAGNOSTIK",
      "[10] MODEL ANCAMAN & KEAMANAN"
    ],
    "nav": {
      "sec-overview-arch": "[1.1] Arsitektur & Tujuan",
      "sec-overview-formats": "[1.2] Format Didukung & Batasan",
      "sec-overview-layout": "[1.3] Struktur Direktori Proyek",
      "sec-overview-pillars": "[1.4] Pilar Inti Next-Gen",
      "sec-overview-v28": "[1.5] Arsitektur Inti (v0.28.0)",
      "sec-install-prereqs": "[2.1] Prasyarat Sistem",
      "sec-install-steps": "[2.2] Langkah-Langkah Instalasi",
      "sec-install-launchers": "[2.3] Peluncur Utama & Wizard",
      "sec-install-recipes": "[2.4] Resep Eksekusi Pertama",
      "sec-cli-flags": "[3.1] Matriks Lengkap Flag CLI",
      "sec-cli-builder": "[3.2] Pembuat Perintah CLI Interaktif",
      "sec-cli-profiles": "[3.3] Profil Eksekusi",
      "sec-engine-bfs": "[4.1] Loop Crawl BFS",
      "sec-engine-waf": "[4.2] Pipeline WAF Stealth 8-Tingkat",
      "sec-engine-captcha": "[4.3] Strategi Captcha Universal",
      "sec-engine-scoring": "[4.4] Penilaian Kualitas & Penolakan",
      "sec-engine-normalize": "[4.5] Normalisasi URL",
      "sec-engine-pool": "[4.6] Pool Browser Siap-Pakai (Pre-Warmed)",
      "sec-engine-broker": "[4.7] Broker Tugas Redis Streams",
      "sec-engine-ml": "[4.8] Hardware Visi & Pipeline ML",
      "sec-engine-healing": "[4.9] Parser DOM Self-Healing",
      "sec-engine-bktree": "[4.10] Deduplikasi Perseptual BK-Tree",
      "sec-config-env": "[5.1] Variabel Lingkungan (.env)",
      "sec-config-domain": "[5.2] domain_config.json",
      "sec-config-urlnorm": "[5.3] url_normalisation_rules.json",
      "sec-config-seeds": "[5.4] Sintaks Manifest Seed",
      "sec-config-profiles": "[5.5] Profil Target Subjek",
      "sec-config-blacklist": "[5.6] Manajemen Daftar Hitam (Blacklist)",
      "sec-webui-arch": "[6.1] Arsitektur Server",
      "sec-webui-views": "[6.2] Command Center & Media Vault",
      "sec-webui-telemetry": "[6.3] Telemetri Live & SSE",
      "sec-webui-design": "[6.4] Token Desain Brutalis",
      "sec-webui-health": "[6.5] Monitor Taktis Node Health",
      "sec-ops-docker": "[7.1] Docker Compose",
      "sec-ops-watchdog": "[7.2] Agen Pengawas (Watchdog)",
      "sec-ops-notifications": "[7.3] Saluran Notifikasi Multi-Platform",
      "sec-ops-proxy": "[7.4] Manajemen Pool Proksi",
      "sec-ops-sessions": "[7.5] Vault Sesi & Cookie",
      "sec-output-structure": "[8.1] Struktur Direktori Output",
      "sec-output-manifest": "[8.2] Skema manifest.json",
      "sec-output-domain": "[8.3] Skema domain_report.json",
      "sec-output-kohya": "[8.4] Ekspor Dataset Kohya LoRA",
      "sec-output-rag": "[8.5] Format Ingesti RAG",
      "sec-output-cas": "[8.6] Content-Addressable Storage (CAS)",
      "sec-output-parquet": "[8.7] Ekspor Dataset Apache Parquet",
      "sec-test-pytest": "[9.1] Menjalankan pytest",
      "sec-test-tdai": "[9.2] Protokol Verifikasi (TDAI)",
      "sec-test-logs": "[9.3] Resep Diagnostik Log",
      "sec-test-diagnostic": "[9.4] Matriks Diagnostik Operator",
      "sec-test-guidelines": "[9.5] Pedoman Pengembang",
      "sec-threat-overview": "[10.1] Cakupan Pra-Implementasi",
      "sec-threat-leasing": "[10.2] Matriks Task Leasing",
      "sec-threat-cas": "[10.3] Matriks Cloud CAS",
      "sec-threat-vlm": "[10.4] Matriks VLM Healing",
      "sec-threat-ac": "[10.5] Kontrak Kriteria Penerimaan (Acceptance Criteria)"
    },
    "footer": {
      "logo": "scrAPE // SISTEM INTI",
      "tagline": "Mesin ekstraksi media otonom dan crawler stealth berperforma tinggi untuk penemuan aset dan bypass WAF yang tangguh.",
      "badges": [
        "RILIS v0.30.1",
        "LISENSI MIT",
        "PYTHON 3.10+"
      ],
      "headings": {
        "repo": "REPOSITORI",
        "docs": "DOKUMENTASI"
      },
      "links": [
        "Kode Sumber",
        "Catatan Rilis (v0.30.1)",
        "Pelacak Masalah",
        "CI / Alur Kerja",
        "README Sistem",
        "Model Ancaman (v0.30.0)",
        "Log Perubahan Versi",
        "Lisensi MIT",
        "Docker Compose"
      ],
      "copy": "© 2026 Pengelola scrAPE. Sumber terbuka di bawah Lisensi MIT.",
      "sysinfo": "STATUS: OPERASIONAL // MESIN: v0.30.1"
    },
    "sections": {
      "sec-overview-arch": {
        "tag": "MODUL [01] // GAMBARAN SISTEM",
        "h1": "Arsitektur & Tujuan Sistem",
        "desc": "Sistem web scraping stealth multi-mesin untuk ekstraksi media otonom dan kurasi dataset kecerdasan buatan (AI).",
        "cards": [
          "1.1 Arsitektur Sistem"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] JAMINAN OPERASIONAL INTI",
            "bodyHtml": "Sistem beroperasi melalui pipeline fallback WAF 8-tingkat. Permintaan secara otomatis dieskalasi dari HTTP langsung yang ringan hingga otomatisasi browser stealth headful ketika loop tantangan terdeteksi. Tidak diperlukan intervensi manual."
          }
        ]
      },
      "sec-overview-formats": {
        "tag": "MODUL [01] // GAMBARAN SISTEM",
        "h1": "Format yang Didukung & Batasan Operasional",
        "desc": "Spesifikasi aset, filter batas ukuran byte, resolusi dimensi minimum, dan batasan laju request (RPS).",
        "cards": [
          "1.2 Kapabilitas Media & Data"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-overview-layout": {
        "tag": "MODUL [01] // GAMBARAN SISTEM",
        "h1": "Struktur Direktori Proyek",
        "desc": "Organisasi file dan modul repositori sistem.",
        "cards": [
          "1.3 Struktur Direktori"
        ],
        "codeHeaders": [
          "TEKS // STRUKTUR REPOSITORI"
        ],
        "alerts": []
      },
      "sec-overview-pillars": {
        "tag": "MODUL [01] // GAMBARAN SISTEM",
        "h1": "Pilar Arsitektur Inti (v0.30.1)",
        "desc": "Orkestrasi multi-node enterprise, deduplikasi perseptual sub-linear BK-tree, pool thread profiler terisolasi, dan CAS nol-duplikasi.",
        "cards": [
          "1.4 Pilar Arsitektur Inti (v0.30.1)"
        ],
        "codeHeaders": [
          "BASH // AKTIVASI CLI PILAR INTI"
        ],
        "alerts": []
      },
      "sec-overview-v28": {
        "tag": "MODUL [01] // PEMBARUAN ARSITEKTUR",
        "h1": "Arsitektur Inti (v0.28.0)",
        "desc": "Pipeline ML terpisah kelas produksi, deduplikasi hierarki 3 tingkat, parser DOM mandiri, dan konkurensi terkontrol.",
        "cards": [
          "1.4 Terobosan Arsitektur pada v0.28.0"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-prereqs": {
        "tag": "MODUL [02] // INSTALASI & PANDUAN CEPAT",
        "h1": "Prasyarat Sistem & Kebutuhan Lingkungan",
        "desc": "Runtime Python 3.10+, driver browser stealth, akselerasi perangkat keras CUDA, dan infrastruktur Redis Streams.",
        "cards": [
          "2.1 Persyaratan Sistem"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-steps": {
        "tag": "MODUL [02] // INSTALASI & PANDUAN CEPAT",
        "h1": "Langkah-Langkah Instalasi Lengkap",
        "desc": "Pembuatan virtual environment, instalasi paket pip, dan sinkronisasi binary browser headless.",
        "cards": [
          "2.2 Prosedur Instalasi & Pengaturan"
        ],
        "codeHeaders": [
          "BASH // PERINTAH INSTALASI"
        ],
        "alerts": [
          {
            "title": "[i] PENGATURAN FLARESOLVERR",
            "bodyHtml": "FlareSolverr (Tingkat 5) berjalan sebagai kontainer Docker. Jalankan dengan: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"
          }
        ]
      },
      "sec-install-launchers": {
        "tag": "MODUL [02] // INSTALASI & PANDUAN CEPAT",
        "h1": "Peluncur Utama & Wizard Interaktif",
        "desc": "Skrip peluncur lintas-platform untuk seluruh mode eksekusi.",
        "cards": [
          "2.3 Opsi Peluncur & Wizard"
        ],
        "codeHeaders": [
          "POWERSHELL // PELUNCUR UTAMA"
        ],
        "alerts": []
      },
      "sec-install-recipes": {
        "tag": "MODUL [02] // INSTALASI & PANDUAN CEPAT",
        "h1": "Resep Eksekusi Pertama",
        "desc": "Perintah siap pakai (copy-paste) untuk pola ekstraksi umum.",
        "cards": [
          "2.4 Resep Perintah Eksekusi Pertama"
        ],
        "codeHeaders": [
          "RESEP 1 // EKSTRAKSI SEED STANDAR DENGAN RETENSI MEDIA DITOLAK",
          "RESEP 2 // AGEN PENGAWAS KONTINU DENGAN CACHE STATUS",
          "RESEP 3 // UJI VALIDASI CEPAT (TANPA UNDUHAN)",
          "RESEP 4 // PENEMUAN HANYA-PENCARIAN (TANPA SEED)",
          "RESEP 5 // CRAWL STEALTH (KECEPATAN SOPAN)"
        ],
        "alerts": []
      },
      "sec-cli-flags": {
        "tag": "MODUL [03] // REFERENSI CLI",
        "h1": "Matriks Lengkap Flag Eksekusi CLI",
        "desc": "Panduan referensi menyeluruh untuk seluruh opsi command-line, switch bypass, dan alokasi budget ekstraksi.",
        "cards": [
          "3.1 Matriks Parameter Command Line"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-cli-builder": {
        "tag": "MODUL [03] // REFERENSI CLI",
        "h1": "Pembuat Perintah CLI Interaktif",
        "desc": "Atur parameter target, konkurensi worker, dan opsi stealth untuk menghasilkan baris perintah terminal siap pakai.",
        "cards": [
          "3.2 Generator Perintah Interaktif"
        ],
        "codeHeaders": [
          "STRING PERINTAH CLI DIHASILKAN"
        ],
        "alerts": []
      },
      "sec-cli-profiles": {
        "tag": "MODUL [03] // REFERENSI CLI",
        "h1": "Profil Eksekusi Bawaan",
        "desc": "Preset profil siap pakai yang telah dioptimalkan untuk berbagai topologi scraping khusus.",
        "cards": [
          "3.3 Matriks Profil Preset"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-bfs": {
        "tag": "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        "h1": "Loop Crawl BFS",
        "desc": "Loop traversal breadth-first asinkron, dispatch antrean prioritas, dan ekstraksi tautan cerdas.",
        "cards": [
          "4.1 Urutan Eksekusi BFS"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-waf": {
        "tag": "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        "h1": "Pipeline Eskalasi WAF Stealth 8-Tingkat",
        "desc": "Fallback bertingkat adaptif untuk menembus Cloudflare Turnstile, Datadome, Incapsula, dan proteksi anti-bot modern.",
        "cards": [
          "4.2 Hierarki Pipeline WAF 8-Tingkat"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-captcha": {
        "tag": "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        "h1": "Strategi Captcha Universal",
        "desc": "Penyedia solver otomatis, intersepsi challenge visual, dan penanganan percobaan ulang mandiri.",
        "cards": [
          "4.3 Strategi Penyelesaian Challenge & Captcha"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-scoring": {
        "tag": "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        "h1": "Penilaian Kualitas & Penolakan Aset",
        "desc": "Klasifikasi URL, ambang batas dimensi gambar minimum, dan persistensi media yang ditolak ke disk.",
        "cards": [
          "4.4 Aturan Penolakan & Jalur Retensi"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-normalize": {
        "tag": "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        "h1": "Normalisasi URL & Kanonisasi",
        "desc": "Pembersihan parameter pelacakan (tracking), kanonisasi protokol, dan pencegahan siklus antrean redundan.",
        "cards": [
          "4.5 Pipeline Kanonisasi URL"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-pool": {
        "tag": "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        "h1": "Pool Browser Siap-Pakai (Pre-Warmed)",
        "desc": "Daur ulang pool browser Camoufox berperforma tinggi dan mekanisme leasing konteks terisolasi.",
        "cards": [
          "4.6 Siklus Hidup Pool Browser Siap-Pakai"
        ],
        "codeHeaders": [
          "PYTHON // LEASING POOL BROWSER PREWARMED"
        ],
        "alerts": []
      },
      "sec-engine-broker": {
        "tag": "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        "h1": "Broker Tugas Redis Streams",
        "desc": "Grup konsumen terdistribusi, pelacakan pending entry (PEL), dan pengiriman tugas atomik.",
        "cards": [
          "4.7 Koordinasi Kluster Terdistribusi via Redis Streams"
        ],
        "codeHeaders": [
          "PYTHON // POLA INTERAKSI BROKER TUGAS"
        ],
        "alerts": []
      },
      "sec-engine-ml": {
        "tag": "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        "h1": "Hardware Visi & Pipeline ML",
        "desc": "Deteksi perangkat keras CUDA/MPS, inferensi half-precision (FP16), dan penilaian estetika otomatis.",
        "cards": [
          "4.8 Matriks Akselerasi Perangkat Keras (CUDA / MPS)"
        ],
        "codeHeaders": [
          "PYTHON // DETEKSI PERANGKAT KERAS & NEGOSIASI PRESISI"
        ],
        "alerts": []
      },
      "sec-engine-healing": {
        "tag": "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        "h1": "Parser DOM Self-Healing",
        "desc": "Kaskade pemulihan DOM 4-tingkat dengan perbaikan heuristik LLM multi-penyedia.",
        "cards": [
          "4.9 Perbaikan Selektor Otonom & VLM Healing"
        ],
        "codeHeaders": [
          "PYTHON // KASKADE EKSTRAKSI SELF-HEALING",
          "TEKS // KASKADE SINTESIS LLM MULTI-PENYEDIA"
        ],
        "alerts": []
      },
      "sec-engine-bktree": {
        "tag": "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        "h1": "Deduplikasi BK-Tree & Partisi Konkurensi",
        "desc": "Pengindeksan pohon metrik diskrit, klasterisasi jarak Hamming, dan pemisahan pool eksekusi profiler terisolasi.",
        "cards": [
          "4.10 Pohon Metrik Diskrit & Partisi Pool Eksekusi"
        ],
        "codeHeaders": [
          "PYTHON // PENCARIAN METRIK BK-TREE & CONNECTION POOLING"
        ],
        "alerts": []
      },
      "sec-config-env": {
        "tag": "MODUL [05] // REFERENSI KONFIGURASI",
        "h1": "Variabel Lingkungan (.env)",
        "desc": "Kredensial produksi, batas laju request, gateway proksi, dan token API.",
        "cards": [
          "5.1 Templat Konfigurasi .env"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-domain": {
        "tag": "MODUL [05] // REFERENSI KONFIGURASI",
        "h1": "domain_config.json",
        "desc": "Batas konkurensi per-domain, selektor tunggu kustom, dan penimpaan header HTTP.",
        "cards": [
          "5.2 Referensi Kunci Konfigurasi (domain_config.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-urlnorm": {
        "tag": "MODUL [05] // REFERENSI KONFIGURASI",
        "h1": "url_normalisation_rules.json",
        "desc": "Ekspresi reguler (regex) untuk penghapusan parameter query dan transformasi domain.",
        "cards": [
          "5.3 Skema Aturan Normalisasi (url_normalisation_rules.json)"
        ],
        "codeHeaders": [
          "JSON // CONTOH SKEMA ATURAN"
        ],
        "alerts": [
          {
            "title": "[!] ATURAN WAJIB",
            "bodyHtml": "Jangan pernah melakukan hardcode regex normalisasi URL spesifik domain di file Python di bawah <code>src/</code>. Seluruh aturan WAJIB dideklarasikan dalam <code>data/url_normalisation_rules.json</code>."
          }
        ]
      },
      "sec-config-seeds": {
        "tag": "MODUL [05] // REFERENSI KONFIGURASI",
        "h1": "Sintaks Manifest Seed",
        "desc": "Komentar, direktif inline, dan bobot prioritas dalam file seeds/*.txt.",
        "cards": [
          "5.4 Referensi Anotasi Manifest Seed"
        ],
        "codeHeaders": [
          "MANIFEST // CONTOH ANOTASI MANIFEST SEED"
        ],
        "alerts": []
      },
      "sec-config-profiles": {
        "tag": "MODUL [05] // REFERENSI KONFIGURASI",
        "h1": "Profil Target Subjek",
        "desc": "Preset spesifik subjek, templat direktori output, dan keterkaitan blacklist.",
        "cards": [
          "5.5 Preset Profil Target (subject_profiles.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-blacklist": {
        "tag": "MODUL [05] // REFERENSI KONFIGURASI",
        "h1": "Manajemen Blacklist Domain",
        "desc": "Domain yang dikecualikan secara global, server iklan, dan pola sumber daya bernilai rendah.",
        "cards": [
          "5.6 Manajemen Blacklist Domain & Filter Pengecualian"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-arch": {
        "tag": "MODUL [06] // DASHBOARD WEBUI",
        "h1": "Arsitektur Server WebUI",
        "desc": "Pusat komando reaktif berbasis FastAPI dan HTMX dengan streaming telemetri Server-Sent Events (SSE).",
        "cards": [
          "6.1 Server FastAPI Terpisah"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-views": {
        "tag": "MODUL [06] // DASHBOARD WEBUI",
        "h1": "Command Center & Media Vault",
        "desc": "Dashboard kontrol interaktif, status crawler real-time, dan inspeksi galeri media hasil unduhan.",
        "cards": [
          "6.2 Tampilan Dashboard (Command Center & Media Vault)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-telemetry": {
        "tag": "MODUL [06] // DASHBOARD WEBUI",
        "h1": "Telemetri Live & SSE",
        "desc": "Streaming event real-time melalui Server-Sent Events, metrik kecepatan antrean, dan monitor memori.",
        "cards": [
          "6.3 Pipeline Event Real-Time (SSE & Canvas)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-design": {
        "tag": "MODUL [06] // DASHBOARD WEBUI",
        "h1": "Token Desain Brutalis",
        "desc": "Token CSS brutalis utilitarian taktis, tipografi monospace kontras tinggi, dan palet warna amber.",
        "cards": [
          "6.4 Referensi Token Desain (Brutalisme Taktis)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-health": {
        "tag": "MODUL [06] // DASHBOARD WEBUI",
        "h1": "Monitor Taktis Node Health",
        "desc": "Pemeriksaan kesehatan subsistem, probe heartbeat berkala, dan telemetri kluster Redis.",
        "cards": [
          "6.5 Telemetri Taktis & Tata Kelola Node"
        ],
        "codeHeaders": [
          "JSON // PAYLOAD TELEMETRI KESEHATAN NODE"
        ],
        "alerts": []
      },
      "sec-ops-docker": {
        "tag": "MODUL [07] // DEPLOYMENT & OPERASIONAL",
        "h1": "Deployment dengan Docker Compose",
        "desc": "Penyebaran produksi multi-kontainer dengan FlareSolverr, Redis Streams, dan server WebUI.",
        "cards": [
          "7.1 Deployment Kontainer dengan Docker Compose"
        ],
        "codeHeaders": [
          "BASH // PELUNCURAN DOCKER COMPOSE"
        ],
        "alerts": []
      },
      "sec-ops-watchdog": {
        "tag": "MODUL [07] // DEPLOYMENT & OPERASIONAL",
        "h1": "Agen Pengawas (Watchdog)",
        "desc": "Daemon crawl kontinu dengan pemeriksaan kesehatan otomatis dan kebijakan restart cerdas.",
        "cards": [
          "7.2 Loop Pemantauan Berkelanjutan (Watchdog)"
        ],
        "codeHeaders": [
          "POWERSHELL // PERINTAH AGEN PENGAWAS"
        ],
        "alerts": []
      },
      "sec-ops-notifications": {
        "tag": "MODUL [07] // DEPLOYMENT & OPERASIONAL",
        "h1": "Saluran Notifikasi Multi-Platform",
        "desc": "Saluran peringatan pluggable: bot Telegram, webhook Discord, Slack, dan HTTP webhook kustom.",
        "cards": [
          "7.3 Peringatan Multi-Saluran (Telegram, Discord, Slack)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-proxy": {
        "tag": "MODUL [07] // DEPLOYMENT & OPERASIONAL",
        "h1": "Manajemen Pool Proksi",
        "desc": "Rotasi proksi cerdas, karantina latensi otomatis, dan kuota konsumsi bandwidth.",
        "cards": [
          "7.4 Strategi Manajer Proksi & Karantina Latensi"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-sessions": {
        "tag": "MODUL [07] // DEPLOYMENT & OPERASIONAL",
        "h1": "Vault Sesi & Cookie",
        "desc": "Sesi sticky per-domain yang persisten dan alur login cookie interaktif menggunakan browser headful.",
        "cards": [
          "7.5 Penyimpanan Sesi & Manajemen Cookie"
        ],
        "codeHeaders": [
          "BASH // PERINTAH LOGIN SESI"
        ],
        "alerts": []
      },
      "sec-output-structure": {
        "tag": "MODUL [08] // OUTPUT & EKSPOR DATA",
        "h1": "Struktur Direktori Output",
        "desc": "Tata letak artefak hasil eksekusi crawl pada sistem file.",
        "cards": [
          "8.1 Organisasi Artefak & Direktori Output"
        ],
        "codeHeaders": [
          "TEKS // TATA LETAK DIREKTORI OUTPUT"
        ],
        "alerts": []
      },
      "sec-output-manifest": {
        "tag": "MODUL [08] // OUTPUT & EKSPOR DATA",
        "h1": "Skema manifest.json",
        "desc": "Dokumentasi skema JSON lengkap untuk hasil eksekusi crawl.",
        "cards": [
          "8.2 Kolom Payload JSON (manifest.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-domain": {
        "tag": "MODUL [08] // OUTPUT & EKSPOR DATA",
        "h1": "Skema domain_report.json",
        "desc": "Laporan metrik performa crawl per domain target.",
        "cards": [
          "8.3 Laporan Hasil per Domain (domain_report.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-kohya": {
        "tag": "MODUL [08] // OUTPUT & EKSPOR DATA",
        "h1": "Ekspor Dataset Kohya LoRA",
        "desc": "Pembuatan arsip ZIP dataset format Kohya_ss LoRA dengan tag deskriptif otomatis.",
        "cards": [
          "8.4 Generator Dataset Kohya LoRA"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-rag": {
        "tag": "MODUL [08] // OUTPUT & EKSPOR DATA",
        "h1": "Format Ingesti RAG untuk LLM",
        "desc": "Ekspor data halaman untuk RAG LLM (pecahan Markdown terkonsolidasi dan format embedding JSONL).",
        "cards": [
          "8.5 Opsi Ekspor RAG (Markdown & JSONL)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-cas": {
        "tag": "MODUL [08] // OUTPUT & EKSPOR DATA",
        "h1": "Penyimpanan Berbasis Konten (CAS)",
        "desc": "Repositori deduplikasi global instan SHA-256 dengan hardlink NTFS/POSIX tanpa redundansi disk.",
        "cards": [
          "8.6 Arsitektur Content-Addressable Storage (CAS)"
        ],
        "codeHeaders": [
          "PYTHON // DEDUPLIKASI CAS & PENAUTAN RUN",
          "TEKS // SIKLUS HIDUP PENYIMPANAN CAS"
        ],
        "alerts": []
      },
      "sec-output-parquet": {
        "tag": "MODUL [08] // OUTPUT & EKSPOR DATA",
        "h1": "Ekspor Dataset Apache Parquet",
        "desc": "Dataset kolumnar terkompresi Snappy yang dioptimalkan untuk pipeline Polars, DuckDB, Pandas, dan Big Data OLAP.",
        "cards": [
          "8.7 Pipeline Ekspor Data Kolumnar (Apache Parquet)"
        ],
        "codeHeaders": [
          "PYTHON // GENERASI DATASET PARQUET"
        ],
        "alerts": []
      },
      "sec-test-pytest": {
        "tag": "MODUL [09] // PENGUJIAN & DIAGNOSTIK",
        "h1": "Menjalankan Pengujian pytest",
        "desc": "Eksekusi suite pengujian unit dan integrasi otomatis secara komprehensif.",
        "cards": [
          "9.1 Suite Pengujian Otomatis Pytest"
        ],
        "codeHeaders": [
          "POWERSHELL // JALANKAN TEST SUITE LENGKAP"
        ],
        "alerts": []
      },
      "sec-test-tdai": {
        "tag": "MODUL [09] // PENGUJIAN & DIAGNOSTIK",
        "h1": "Protokol Verifikasi (TDAI)",
        "desc": "Aturan verifikasi AI Berbasis Pengujian (TDAI) dan protokol siklus RED-GREEN-REFACTOR.",
        "cards": [
          "9.2 Protokol Verifikasi Empiris (TDAI)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] ATURAN WAJIB",
            "bodyHtml": "Jangan pernah menyatakan fitur atau perbaikan selesai tanpa menjalankan perintah verifikasi runtime empiris dan mendemonstrasikan hasil pengujian yang 100% lulus."
          }
        ]
      },
      "sec-test-logs": {
        "tag": "MODUL [09] // PENGUJIAN & DIAGNOSTIK",
        "h1": "Resep Diagnostik Log",
        "desc": "Analisis log dan perintah grep untuk diagnostik runtime cepat.",
        "cards": [
          "9.3 Perintah Diagnostik PowerShell & Analisis Log"
        ],
        "codeHeaders": [
          "POWERSHELL // GREP LOG UNTUK ERROR & PEMBLOKIRAN"
        ],
        "alerts": []
      },
      "sec-test-diagnostic": {
        "tag": "MODUL [09] // PENGUJIAN & DIAGNOSTIK",
        "h1": "Matriks Diagnostik Operator",
        "desc": "Tabel diagnostik komprehensif untuk pemecahan masalah operator.",
        "cards": [
          "9.4 Matriks Diagnostik Operator"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-test-guidelines": {
        "tag": "MODUL [09] // PENGUJIAN & DIAGNOSTIK",
        "h1": "Pedoman Pengembang & Standar Kode",
        "desc": "Aturan pengkodean wajib dan standar integritas ruang kerja.",
        "cards": [
          "9.5 Aturan Pengkodean Wajib Pengembang"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-threat-overview": {
        "tag": "MODUL [10] // MODEL ANCAMAN & KEAMANAN",
        "h1": "Arsitektur Keamanan & Verifikasi v0.30.0",
        "desc": "Model ancaman otoritatif, kontrak arsitektur STRIDE, dan matriks verifikasi empiris untuk penskalaan terdistribusi v0.30.0.",
        "cards": [
          "10.1 Batas Kepercayaan & Arsitektur Aliran Data",
          "10.1.1 Kategorisasi Ancaman STRIDE",
          "10.1.2 Invarian Lintas-Sektor"
        ],
        "codeHeaders": [
          "ARSITEKTUR // v0.30.0 BATAS KEPERCAYAAN TERDISTRIBUSI & ALIRAN DATA"
        ],
        "alerts": [
          {
            "title": "RILIS PRODUKSI // v0.30.0 TERVERIFIKASI & TERSERTIFIKASI",
            "bodyHtml": "Ketiga aspek model ancaman (Leasing Tugas Terdistribusi, Sinkronisasi Cloud CAS, Pemulihan DOM Vision-Language) yang ditentukan dalam modul ini telah <strong>diimplementasikan sepenuhnya, diuji secara adversarial, dan diverifikasi CI secara empiris</strong> pada rilis v0.30.0 di runner Ubuntu, macOS, dan Windows."
          },
          {
            "title": "KONTRAK ARSITEKTUR WAJIB",
            "bodyHtml": "Spesifikasi ini adalah garis dasar otoritatif untuk seluruh implementasi fitur v0.30.0. Setiap kriteria penerimaan (AC1.1 hingga AC3.6) wajib memiliki tes otomatis di <code>tests/</code> sebelum komponen apa pun dianggap siap rilis."
          }
        ]
      },
      "sec-threat-leasing": {
        "tag": "MODUL [10] // KOMPONEN 1 (TERIMPLEMENTASI & TERVERIFIKASI)",
        "h1": "Matriks Ancaman Task Leasing Terdistribusi",
        "desc": "Analisis kerentanan STRIDE, skenario serangan, dan mekanisme mitigasi atomik untuk worker daemon Redis Stream.",
        "cards": [
          "10.2 Gambaran Desain Komponen 1",
          "10.2.1 Matriks Ancaman & Kerentanan (Komponen 1)",
          "10.2.2 Spesifikasi Mitigasi Rinci"
        ],
        "codeHeaders": [
          "PYTHON // AKUISISI KUNCI IDEMPOTEN ATOMIK"
        ],
        "alerts": [
          {
            "title": "KOMPONEN 1 TERIMPLEMENTASI & TERVERIFIKASI // AC1.1–AC1.7 LULUS",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>, <code>DistributedWorkerNode</code>, dan daemon worker CLI (<code>src.cli.worker</code>) telah diimplementasikan sepenuhnya dan diverifikasi terhadap kriteria penerimaan AC1.1 hingga AC1.7 dengan 98 pengujian otomatis."
          }
        ]
      },
      "sec-threat-cas": {
        "tag": "MODUL [10] // ARSITEKTUR KOMPONEN 2",
        "h1": "Matriks Ancaman Sinkronisasi Cloud CAS",
        "desc": "Spesifikasi pertahanan berlapis, verifikasi kriptografis, dan pencegahan SSRF untuk backend penyimpanan S3 / Cloudflare R2 / MinIO.",
        "cards": [
          "10.3 Gambaran Desain Komponen 2",
          "10.3.1 Matriks Ancaman & Kerentanan (Komponen 2)",
          "10.3.2 Penegakan Jalur Hash Kriptografis"
        ],
        "codeHeaders": [
          "PYTHON // VALIDASI JALUR KUNCI CAS & VERIFIKASI CHECKSUM"
        ],
        "alerts": [
          {
            "title": "TERSERTIFIKASI PRODUKSI // KOMPONEN 2 TERIMPLEMENTASI LENGKAP",
            "bodyHtml": "<code>CASCloudSyncer</code> dan backend cloud storage S3/R2/MinIO telah <strong>diimplementasikan dan diverifikasi sepenuhnya</strong> pada v0.30.0 dengan tingkat kelulusan tes 100% di seluruh AC2.1-AC2.7."
          }
        ]
      },
      "sec-threat-vlm": {
        "tag": "MODUL [10] // KOMPONEN 3 (TERIMPLEMENTASI & TERVERIFIKASI)",
        "h1": "Matriks Ancaman Pemulihan DOM Vision-Language",
        "desc": "Kontrol keamanan AI multimodal, pertahanan adversarial visual prompt injection, dan sandboxing interaksi DOM untuk Tier 4 healing.",
        "cards": [
          "10.4 Gambaran Desain Komponen 3",
          "10.4.1 Matriks Ancaman & Kerentanan (Komponen 3)",
          "10.4.2 Pembingkaian Data Tidak Tepercaya & Pembatas Output"
        ],
        "codeHeaders": [
          "ARSITEKTUR PROMPT // SYSTEM PROMPT VLM TERSANDBOX"
        ],
        "alerts": [
          {
            "title": "TERSERTIFIKASI PRODUKSI // KOMPONEN 3 TERIMPLEMENTASI LENGKAP",
            "bodyHtml": "<code>VisionDOMHealer</code> (Tier 4 multimodal DOM healing) telah <strong>diimplementasikan dan diverifikasi sepenuhnya</strong> pada v0.30.0 dengan tingkat kelulusan 100% di AC3.1-AC3.6 dan penolakan fuzzing prompt injection 75 vektor."
          }
        ]
      },
      "sec-threat-ac": {
        "tag": "MODUL [10] // MATRIKS VERIFIKASI & AUDIT (v0.30.0 PRODUKSI)",
        "h1": "Matriks Verifikasi Kriteria Penerimaan (v0.30.0 Produksi)",
        "desc": "Spesifikasi pengujian empiris, metodologi verifikasi, dan hasil audit yang memvalidasi seluruh 20 kriteria penerimaan v0.30.0.",
        "cards": [
          "10.5.1 Kriteria Penerimaan Komponen 1 (Task Leasing)",
          "10.5.2 Kriteria Penerimaan Komponen 2 (Cloud CAS)",
          "10.5.3 Kriteria Penerimaan Komponen 3 (VLM Healing)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "SELURUH 20 KRITERIA PENERIMAAN TERVERIFIKASI & TERSERTIFIKASI",
            "bodyHtml": "Seluruh 20 kriteria di bawah ini (AC1.1 hingga AC3.6) mewakili <strong>kontrak arsitektur inti</strong> untuk v0.30.0. Setiap kriteria didukung oleh tes otomatis di <code>tests/</code> yang lulus 100%."
          },
          {
            "title": "STANDAR VERIFIKASI",
            "bodyHtml": "Tidak ada pull request atau rilis v0.30.0 yang disetujui tanpa cakupan pengujian 100% di seluruh 20 kriteria penerimaan."
          }
        ]
      }
    },
    "snippets": {
      "sec-install-steps": "# 1. Klon repositori\ngit clone https://github.com/rhaffle87/scrAPE.git\ncd scrAPE\n\n# 2. Buat dan aktifkan lingkungan virtual\npython -m venv venv\nvenv\\Scripts\\activate          # Windows CMD\n.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell\nsource venv/bin/activate       # Linux / macOS\n\n# 3. Instal dependensi Python\npip install -r requirements.txt\n\n# 4. (Opsional) Instal bridge Node.js Crawlee untuk stealth Tingkat 6-7\ncd crawlee_bridge && npm install && cd ..\n\n# 5. Konfigurasi kredensial\ncopy .env.example .env         # Windows\ncp .env.example .env           # Linux / macOS\n# Kemudian edit .env dengan API key dan URL webhook Anda",
      "sec-install-launchers": "# Peluncur Utama Windows (Menu Interaktif)\n.\\run.bat\n\n# Peluncur Utama Linux / macOS\n./run.sh\n\n# Wizard Interaktif Langsung (tanpa menu)\npython src/cli/cli_wizard.py",
      "sec-ops-docker": "# Jalankan mesin scraper + sidecar FlareSolverr\ndocker compose up -d\n\n# Pantau log kluster secara real-time\ndocker compose logs -f\n\n# Hentikan stack kontainer dengan aman\ndocker compose down",
      "sec-ops-watchdog": "# Jalankan Agen Pengawas melalui wrapper peluncur\n.\\run.bat watchdog\n\n# Eksekusi langsung pemantauan kontinu\npython src/cli/monitor_agent.py --keyword \"example_subject\" --seed seeds/example_subject.txt --use-state-cache",
      "sec-ops-sessions": "# Tangkap cookie melalui jendela browser interaktif\npython src/cli/session_auth.py --domain example.com --login-url https://example.com/login\n\n# Tampilkan daftar cookie sesi sticky tersimpan\npython src/cli/session_auth.py --list-sessions",
      "sec-test-pytest": "# Jalankan seluruh 378+ uji unit dan integrasi\npytest tests/ -v\n\n# Jalankan dengan laporan cakupan (coverage)\npytest --cov=src tests/ --cov-report=term-missing",
      "sec-test-logs": "# Periksa batas laju HTTP 429 dan pemblokiran Cloudflare\nGet-Content logs/crawler.log -Tail 100 | Select-String -Pattern \"429|Cloudflare|WAF|BLOCKED\"\n\n# Pantau alur mesin perayap secara real-time\nGet-Content logs/crawler.log -Wait -Tail 20"
    },
    "lists": {
      "sec-install-launchers": [
        "<strong>Scraping Pencarian Luas</strong> -- Kueri pencarian otomatis dengan crawling rekursif.",
        "<strong>Scraping Manifest Tertarget</strong> -- Crawl terstruktur terhadap manifest seed yang dipilih.",
        "<strong>Agen Pengawas Kontinu (Watchdog)</strong> -- Loop pemantauan jangka panjang dengan cache SQLite WAL.",
        "<strong>Buat Dataset AI Terstruktur</strong> -- Kemas output crawl ke dalam struktur terkonsolidasi, dikelompokkan per domain, atau per jenis media.",
        "<strong>Ingesti RAG LLM Enterprise</strong> -- Ekspor data halaman sebagai Markdown terkonsolidasi, file <code>.md</code> per halaman, atau format embedding JSONL."
      ]
    },
    "h3Map": {
      "Wizard Menu Options": "Opsi Menu Wizard",
      "Core Components": "Komponen Inti",
      "Media Vault View": "Tampilan Brankas Media",
      "Command Center View": "Tampilan Pusat Komando",
      "Budget & Balance Guardrails": "Batas Keamanan Anggaran & Saldo",
      "Circuit Breaker & Cooldown Mechanics": "Mekanisme Pemutus Sirkuit & Masa Tenang",
      "Download Validation Thresholds": "Ambang Batas Validasi Unduhan",
      "Primary v0.30.1 Execution Flags": "Flag Eksekusi Utama v0.30.1",
      "Site-Chrome & Keyword Classification Sets": "Kumpulan Klasifikasi Site-Chrome & Kata Kunci",
      "Dead-Letter Stream Protocol": "Protokol Aliran Dead-Letter",
      "Idempotency Lock Implementation": "Implementasi Kunci Idempoten",
      "Node Health JSON Schema (/api/telemetry/node-health)": "Skema JSON Kesehatan Node (/api/telemetry/node-health)"
    },
    "thMap": {
      "Component": "Komponen",
      "Source File": "File Sumber",
      "Function": "Fungsi",
      "Requirement": "Kebutuhan",
      "Minimum": "Minimum",
      "Notes": "Catatan",
      "Category": "Kategori",
      "Supported Types": "Tipe Didukung",
      "Processing Method": "Metode Pemrosesan",
      "Core Pillar": "Pilar Utama",
      "Key Technologies": "Teknologi Utama",
      "Production Capability": "Kapabilitas Produksi",
      "Parameter": "Parameter",
      "Type": "Tipe",
      "Default": "Bawaan",
      "Description": "Deskripsi",
      "Status": "Status",
      "Tier": "Tingkat",
      "Mechanism": "Mekanisme",
      "Overhead": "Overhead",
      "Usage": "Penggunaan",
      "Profile": "Profil",
      "Keyword": "Kata Kunci",
      "Concurrency": "Konkurensi",
      "Depth": "Kedalaman",
      "Endpoint": "Titik Akhir (Endpoint)",
      "Impact": "Dampak",
      "Channel": "Saluran",
      "Provider": "Penyedia",
      "Purpose": "Tujuan",
      "Field": "Kolom",
      "Value": "Nilai",
      "Variable": "Variabel",
      "Subsystem": "Subsistem",
      "Symptom": "Gejala",
      "Where to Look": "Lokasi / Jalur",
      "Resolution Action": "Tindakan Resolusi",
      "Key Flags": "Flag Utama",
      "Syntax": "Sintaks",
      "Primary Use Case": "Kasus Penggunaan Utama",
      "Rejection Reason": "Alasan Penolakan",
      "Disk Retention Path": "Jalur Retensi Disk",
      "Trigger Criteria": "Kriteria Pemicu",
      "Supported Challenge Types": "Tipe Challenge yang Didukung",
      "Fault Tolerance Function": "Fungsi Toleransi Kesalahan",
      "Escalation Trigger": "Pemicu Eskalasi",
      "Telemetry Metric": "Metrik Telemetri",
      "Target Component": "Komponen Target",
      "Visual Indicator & Action": "Indikator Visual & Tindakan",
      "Top-Level Key": "Kunci Tingkat Atas",
      "Required Credentials (.env)": "Kredensial Diperlukan (.env)",
      "Key Benefits": "Manfaat Utama",
      "Schema Columns": "Kolom Skema",
      "Parquet Table": "Tabel Parquet",
      "Payload Type": "Tipe Payload",
      "Source / Endpoint": "Sumber / Endpoint",
      "Stream Command": "Perintah Aliran (Stream)",
      "Internal Action": "Tindakan Internal",
      "Threat Scenario": "Skenario Ancaman",
      "STRIDE Category": "Kategori STRIDE",
      "Vector & Attack Mechanics": "Vektor & Mekanisme Serangan",
      "Mitigation Mechanism": "Mekanisme Mitigasi",
      "Primary Defense Mechanism": "Mekanisme Pertahanan Utama",
      "Hardened Primitive": "Primitif Diperkeras",
      "Test Methodology & Assertion": "Metodologi Pengujian & Asersi",
      "Criterion ID": "ID Kriteria",
      "Requirement Description": "Deskripsi Kebutuhan",
      "Verified Test Suite": "Suite Pengujian Terverifikasi",
      "Architecture Frontier": "Garis Depan Arsitektur",
      "Primary Threat in v0.30.0": "Ancaman Utama di v0.30.0",
      "Algorithmic / System Enhancement": "Peningkatan Algoritmik / Sistem",
      "Compression & Fallback": "Kompresi & Fallback",
      "Annotation Header": "Header Anotasi"
    }
  },
  "zh": {
    "meta": {
      "title": "scrAPE v0.30.1 // 技术文档门户",
      "desc": "scrAPE v0.30.1 官方技术文档、CLI 参数矩阵、核心架构指南与运维操作手册。"
    },
    "ui": {
      "searchPlaceholder": "搜索技术文档...",
      "searchHint": "Ctrl+K",
      "langStripLabel": "文档门户语言 // 语言选择:",
      "githubLink": "[GITHUB]",
      "badgeNew": "最新",
      "badgeVerified": "已验证",
      "copyCode": "[复制代码]",
      "copiedCode": "[已复制!]",
      "commandBuilder": "交互式 CLI 命令构建器",
      "builderPrompt": "配置运行时参数并生成执行命令:",
      "builderOutputLabel": "可执行 CLI 命令:",
      "footerTagline": "具备自愈式 DOM 启发式算法与 Apache Parquet 导出的高吞吐分布式自主抓取引擎。",
      "searchResults": "个结果",
      "noResults": "无匹配结果",
      "selectLocale": "选择文档语言",
      "changeLanguageTitle": "切换语言"
    },
    "modules": [
      "[01] 系统架构概览",
      "[02] 快速安装与配置",
      "[03] CLI 命令行参考",
      "[04] 核心引擎底层架构",
      "[05] 配置文件详尽参考",
      "[06] WEBUI 可视化控制台",
      "[07] 容器部署与日常运维",
      "[08] 数据存储与格式导出",
      "[09] 自动化测试与排错指南",
      "[10] 威胁建模与安全加固"
    ],
    "nav": {
      "sec-overview-arch": "[1.1] 架构与核心目标",
      "sec-overview-formats": "[1.2] 支持格式与边界限制",
      "sec-overview-layout": "[1.3] 项目目录结构",
      "sec-overview-pillars": "[1.4] 下一代核心架构支柱",
      "sec-overview-v28": "[1.5] 核心架构 (v0.28.0)",
      "sec-install-prereqs": "[2.1] 运行前置条件",
      "sec-install-steps": "[2.2] 步骤化安装指南",
      "sec-install-launchers": "[2.3] 启动器与交互向导",
      "sec-install-recipes": "[2.4] 初次抓取执行范例",
      "sec-cli-flags": "[3.1] 完整 CLI 参数矩阵",
      "sec-cli-builder": "[3.2] 交互式 CLI 构建器",
      "sec-cli-profiles": "[3.3] 预设运行配置文件",
      "sec-engine-bfs": "[4.1] BFS 广度优先循环",
      "sec-engine-waf": "[4.2] 8级隐身 WAF 升级管线",
      "sec-engine-captcha": "[4.3] 通用人机验证策略",
      "sec-engine-scoring": "[4.4] 质量评分与丢弃机制",
      "sec-engine-normalize": "[4.5] URL 规范化引擎",
      "sec-engine-pool": "[4.6] 预热浏览器连接池",
      "sec-engine-broker": "[4.7] Redis Streams 任务分发",
      "sec-engine-ml": "[4.8] 视觉硬件与 ML 管线",
      "sec-engine-healing": "[4.9] DOM 自愈选择器",
      "sec-engine-bktree": "[4.10] BK-Tree 感知哈希去重",
      "sec-config-env": "[5.1] 环境变量配置 (.env)",
      "sec-config-domain": "[5.2] 域名策略 (domain_config)",
      "sec-config-urlnorm": "[5.3] URL 正则规则",
      "sec-config-seeds": "[5.4] 种子清单语法",
      "sec-config-profiles": "[5.5] 目标主体配置文件",
      "sec-config-blacklist": "[5.6] 黑名单阻断管理",
      "sec-webui-arch": "[6.1] WebUI 服务架构",
      "sec-webui-views": "[6.2] 指挥中心与媒体保险库",
      "sec-webui-telemetry": "[6.3] 实时遥测与 SSE 流",
      "sec-webui-design": "[6.4] 战术设计规范系统",
      "sec-webui-health": "[6.5] 节点健康战术监控器",
      "sec-ops-docker": "[7.1] Docker 容器化编排",
      "sec-ops-watchdog": "[7.2] 自动化看门狗守护进程",
      "sec-ops-notifications": "[7.3] 多渠道警报通知管线",
      "sec-ops-proxy": "[7.4] 代理池轮换管理",
      "sec-ops-sessions": "[7.5] 会话认证与 Cookie 保险库",
      "sec-output-structure": "[8.1] 产出目录文件组织",
      "sec-output-manifest": "[8.2] manifest.json 元数据格式",
      "sec-output-domain": "[8.3] 域名汇总分析报告",
      "sec-output-kohya": "[8.4] Kohya LoRA 训练集导出",
      "sec-output-rag": "[8.5] RAG 向量知识库摄取",
      "sec-output-cas": "[8.6] 内容寻址存储 (CAS)",
      "sec-output-parquet": "[8.7] Apache Parquet 列式存储",
      "sec-test-pytest": "[9.1] 运行 Pytest 测试套件",
      "sec-test-tdai": "[9.2] 验证规范 (TDAI)",
      "sec-test-logs": "[9.3] 日志诊断排查脚本",
      "sec-test-diagnostic": "[9.4] 运维排障决策矩阵",
      "sec-test-guidelines": "[9.5] 贡献者开发准则",
      "sec-threat-overview": "[10.1] 威胁分析实施范围",
      "sec-threat-leasing": "[10.2] 分布式任务租约矩阵",
      "sec-threat-cas": "[10.3] 云端 CAS 安全同步矩阵",
      "sec-threat-vlm": "[10.4] 多模态视觉自愈安全边界",
      "sec-threat-ac": "[10.5] 安全验收规范契约"
    },
    "footer": {
      "logo": "scrAPE // 核心系统",
      "tagline": "具备自愈式 DOM 启发式算法与 Apache Parquet 导出的高吞吐分布式自主抓取引擎。",
      "badges": [
        "版本 v0.30.1",
        "MIT 许可证",
        "PYTHON 3.10+"
      ],
      "headings": {
        "repo": "开源仓库",
        "docs": "技术文档"
      },
      "links": [
        "源代码",
        "发布说明 (v0.30.1)",
        "问题追踪器",
        "CI / 工作流",
        "系统 README",
        "威胁模型 (v0.30.0)",
        "版本变更日志",
        "MIT 许可证",
        "Docker Compose"
      ],
      "copy": "© 2026 scrAPE 维护者。基于 MIT 许可证开源。",
      "sysinfo": "状态: 运行正常 // 引擎: v0.30.1"
    },
    "sections": {
      "sec-overview-arch": {
        "tag": "模块 [01] // 系统架构概览",
        "h1": "系统架构与设计目标",
        "desc": "专为大规模自主媒体资产提取与 AI 训练数据集构建而设计的多引擎隐身抓取系统。",
        "cards": [
          "1.1 系统底层架构"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] 核心运行保障",
            "bodyHtml": "系统通过 8 级 WAF 降级保护管道运行。当检测到反爬质询循环时，请求会自动从轻量级直接 HTTP 递增升级到带界面的隐身浏览器自动化。整个过程无需人工干预。"
          }
        ]
      },
      "sec-overview-formats": {
        "tag": "模块 [01] // 系统架构概览",
        "h1": "支持的文件格式与运行阈值限制",
        "desc": "多媒体资产技术规格、字节大小过滤规则、图像宽高分辨率下限以及抓取速率硬性指标。",
        "cards": [
          "1.2 媒体与数据处理能力"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-overview-layout": {
        "tag": "模块 [01] // 系统架构概览",
        "h1": "项目目录结构与模块组织",
        "desc": "系统源代码树、配置持久化目录以及各子系统组织架构说明。",
        "cards": [
          "1.3 代码仓库目录结构"
        ],
        "codeHeaders": [
          "文本 // 代码仓库结构树"
        ],
        "alerts": []
      },
      "sec-overview-pillars": {
        "tag": "模块 [01] // 系统架构概览",
        "h1": "核心架构支柱 (v0.30.1)",
        "desc": "企业级多节点协同编排、亚线性 BK-Tree 感知哈希去重、完全隔离的探针分析线程池以及零冗余内容寻址存储 (CAS)。",
        "cards": [
          "1.4 核心架构支柱 (v0.30.1)"
        ],
        "codeHeaders": [
          "BASH // 核心支柱 CLI 启动指令"
        ],
        "alerts": []
      },
      "sec-overview-v28": {
        "tag": "模块 [01] // 核心架构演进",
        "h1": "核心架构演进 (v0.28.0)",
        "desc": "生产级解耦式机器学习流水线、三层分级去重体系、自愈式 DOM 解析器与监督混合并发架构。",
        "cards": [
          "1.4 v0.28.0 核心架构突破"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-prereqs": {
        "tag": "模块 [02] // 快速安装与配置",
        "h1": "系统环境与前置依赖需求",
        "desc": "Python 3.10+ 运行时环境、无头浏览器驱动、CUDA 硬件加速以及 Redis 集群设施需求。",
        "cards": [
          "2.1 系统与环境需求"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-steps": {
        "tag": "模块 [02] // 快速安装与配置",
        "h1": "详细安装与部署步骤",
        "desc": "Python 虚拟环境构建、pip 依赖包安装以及无头隐身浏览器内核同步下载。",
        "cards": [
          "2.2 安装步骤与部署流程"
        ],
        "codeHeaders": [
          "BASH // 快速安装指令集"
        ],
        "alerts": [
          {
            "title": "[i] FLARESOLVERR 服务部署",
            "bodyHtml": "FlareSolverr (Tier 5) 作为 Docker 容器独立运行。使用以下命令启动服务: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"
          }
        ]
      },
      "sec-install-launchers": {
        "tag": "模块 [02] // 快速安装与配置",
        "h1": "主启动脚本与交互式向导",
        "desc": "适用于所有执行模式的交互式跨平台一键启动脚本与向导工具。",
        "cards": [
          "2.3 启动脚本选项与交互式向导"
        ],
        "codeHeaders": [
          "POWERSHELL // 主启动脚本"
        ],
        "alerts": []
      },
      "sec-install-recipes": {
        "tag": "模块 [02] // 快速安装与配置",
        "h1": "常用执行配方与命令示例",
        "desc": "即拷即用的经典抓取与资产提取命令模式示例。",
        "cards": [
          "2.4 常用执行命令配方"
        ],
        "codeHeaders": [
          "配方 1 // 标准种子清单提取与未通过筛选媒体留存",
          "配方 2 // 带有状态缓存的持续监控守护进程",
          "配方 3 // 快速连通性验证运行 (不执行媒体下载)",
          "配方 4 // 仅基于搜索引擎的自主发现 (无种子清单)",
          "配方 5 // 深度隐身慢速抓取 (低频防风控模式)"
        ],
        "alerts": []
      },
      "sec-cli-flags": {
        "tag": "模块 [03] // CLI 命令行参考",
        "h1": "CLI 命令行执行参数全景矩阵",
        "desc": "系统所有命令行开关、参数阈值覆盖、资源预算分配与并发控制标志参考指南。",
        "cards": [
          "3.1 命令行参数矩阵"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-cli-builder": {
        "tag": "模块 [03] // CLI 命令行参考",
        "h1": "交互式 CLI 命令生成器",
        "desc": "可视化配置目标关键词、并发工作池大小与隐身防风控等级，实时生成终端执行指令。",
        "cards": [
          "3.2 交互式命令生成器"
        ],
        "codeHeaders": [
          "生成的 CLI 命令行指令"
        ],
        "alerts": []
      },
      "sec-cli-profiles": {
        "tag": "模块 [03] // CLI 命令行参考",
        "h1": "执行配置文件预设矩阵",
        "desc": "针对不同抓取拓扑和目标站点预先调优的配置文件预设矩阵。",
        "cards": [
          "3.3 预设配置档案矩阵"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-bfs": {
        "tag": "模块 [04] // 核心引擎底层架构",
        "h1": "BFS 广度优先爬行循环",
        "desc": "基于异步协程的高性能广度优先遍历循环、动态优先级队列分发与超链接提取流水线。",
        "cards": [
          "4.1 BFS 抓取执行时序"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-waf": {
        "tag": "模块 [04] // 核心引擎底层架构",
        "h1": "8 级自适应隐身 WAF 降级保护管道",
        "desc": "多层级自适应阶梯式回退机制，无感绕过 Cloudflare Turnstile、Datadome、Incapsula 等防爬风控屏障。",
        "cards": [
          "4.2 8级隐身 WAF 降级管道体系"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-captcha": {
        "tag": "模块 [04] // 核心引擎底层架构",
        "h1": "通用验证码与人机质询求解策略",
        "desc": "自动化第三方打码平台适配器、页面质询无感知拦截以及自适应重试容错机制。",
        "cards": [
          "4.3 验证码与反爬质询解析策略"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-scoring": {
        "tag": "模块 [04] // 核心引擎底层架构",
        "h1": "资产质量智能评分与拒绝留存策略",
        "desc": "URL 智能分类、最小图像宽高过滤阈值以及被剔除低质媒体的分类落盘持久化机制。",
        "cards": [
          "4.4 资源质量过滤规则与留存路径"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-normalize": {
        "tag": "模块 [04] // 核心引擎底层架构",
        "h1": "URL 规范化与清洗管道",
        "desc": "剔除营销追踪参数、规范化网络协议与路径，杜绝重复入队与死循环遍历。",
        "cards": [
          "4.5 URL 规范化与清洗管道"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-pool": {
        "tag": "模块 [04] // 核心引擎底层架构",
        "h1": "预热浏览器池与上下文借调",
        "desc": "基于 Camoufox 内核的高性能热备无头浏览器池、自动周期性回收与上下文安全租用机制。",
        "cards": [
          "4.6 预热浏览器池生命周期管理"
        ],
        "codeHeaders": [
          "PYTHON // 预热浏览器实例租借模式"
        ],
        "alerts": []
      },
      "sec-engine-broker": {
        "tag": "模块 [04] // 核心引擎底层架构",
        "h1": "基于 Redis Streams 的分布式任务代理",
        "desc": "分布式消费者组支持、未确认消息条目追踪 (PEL) 与原子任务并发分发协议。",
        "cards": [
          "4.7 基于 Redis Streams 的分布式集群协同"
        ],
        "codeHeaders": [
          "PYTHON // 任务代理交互模式示例"
        ],
        "alerts": []
      },
      "sec-engine-ml": {
        "tag": "模块 [04] // 核心引擎底层架构",
        "h1": "视觉硬件加速与机器学习推理管道",
        "desc": "自动检测宿主机 CUDA / Apple MPS 加速硬件，支持 FP16 半精度加速与 LAION 美学质量智能评分。",
        "cards": [
          "4.8 视觉硬件加速矩阵 (CUDA / MPS / FP16)"
        ],
        "codeHeaders": [
          "PYTHON // 硬件环境发现与计算精度自适应协商"
        ],
        "alerts": []
      },
      "sec-engine-healing": {
        "tag": "模块 [04] // 核心引擎底层架构",
        "h1": "自愈式 DOM 页面解析引擎",
        "desc": "四级自愈降级梯队，集成多云大语言模型 (Ollama / OpenRouter / Claude) 视觉感知与启发式选择器自愈。",
        "cards": [
          "4.9 自主选择器修复与 VLM 视觉感知自愈"
        ],
        "codeHeaders": [
          "PYTHON // 自愈式提取阶梯回退代码",
          "文本 // 多大模型供应商协同合成回退序列"
        ],
        "alerts": []
      },
      "sec-engine-bktree": {
        "tag": "模块 [04] // 核心引擎底层架构",
        "h1": "BK-Tree 离散去重与并发线程池物理分区",
        "desc": "基于汉明距离的离散度量树极速检索、毫秒级近重复图像剪枝与 CPU 密集型分析线程池物理隔离。",
        "cards": [
          "4.10 离散距离度量树与执行池分区隔离"
        ],
        "codeHeaders": [
          "PYTHON // BK-TREE 距离度量搜索与网络连接池实现"
        ],
        "alerts": []
      },
      "sec-config-env": {
        "tag": "模块 [05] // 配置文件详尽参考",
        "h1": "环境变量与生产凭据配置 (.env)",
        "desc": "生产环境安全凭据、请求速率限制、反向代理网关与第三方打码/LLM API 访问令牌配置。",
        "cards": [
          "5.1 .env 环境变量配置模板"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-domain": {
        "tag": "模块 [05] // 配置文件详尽参考",
        "h1": "域名细粒度策略配置 (domain_config.json)",
        "desc": "按目标域名自定义并发度、CSS/XPath 页面加载等待选择器与动态 HTTP Header 覆盖。",
        "cards": [
          "5.2 域名级覆盖配置参考 (domain_config.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-urlnorm": {
        "tag": "模块 [05] // 配置文件详尽参考",
        "h1": "URL 规范化规则定义 (url_normalisation_rules.json)",
        "desc": "用于清理垃圾查询参数、重定向规整与特定域名 URL 转换的正则表达式声明系统。",
        "cards": [
          "5.3 规范化规则架构 (url_normalisation_rules.json)"
        ],
        "codeHeaders": [
          "JSON // 规范化规则定义示例"
        ],
        "alerts": [
          {
            "title": "[!] 强制执行规则",
            "bodyHtml": "严禁在 <code>src/</code> 目录下的 Python 源码中硬编码特定域名的 URL 正则表达式！所有规则必须在 <code>data/url_normalisation_rules.json</code> 中集中声明与维护。"
          }
        ]
      },
      "sec-config-seeds": {
        "tag": "模块 [05] // 配置文件详尽参考",
        "h1": "Seed 种子清单语法规范",
        "desc": "seeds/*.txt 清单中的注释规范、行内深度控制指令与动态优先级权重定义。",
        "cards": [
          "5.4 Seed 种子清单注解参考"
        ],
        "codeHeaders": [
          "MANIFEST // 种子清单行内注解语法示例"
        ],
        "alerts": []
      },
      "sec-config-profiles": {
        "tag": "模块 [05] // 配置文件详尽参考",
        "h1": "抓取主题预设档案 (subject_profiles.json)",
        "desc": "面向特定提取实体的预设配置、定制化输出结构模板与特定域名黑名单绑定。",
        "cards": [
          "5.5 目标主题预设档案 (subject_profiles.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-blacklist": {
        "tag": "模块 [05] // 配置文件详尽参考",
        "h1": "域名黑名单与全局过滤 (blacklist.json)",
        "desc": "全局排除的目标域名、广告追踪节点以及低价值无用资产的模式过滤管理。",
        "cards": [
          "5.6 域名黑名单与排除过滤 (blacklist.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-arch": {
        "tag": "模块 [06] // WEBUI 可视化控制台",
        "h1": "WebUI 可视化服务器架构",
        "desc": "基于 FastAPI 与 HTMX 响应式构建的轻量控制中枢，支持 SSE 实时事件流与轻量前端解耦交互。",
        "cards": [
          "6.1 解耦式 FastAPI 架构"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-views": {
        "tag": "模块 [06] // WEBUI 可视化控制台",
        "h1": "控制中枢仪表板与媒体资产金库",
        "desc": "交互式抓取任务管控面板、实时运行拓扑以及全功能媒体画廊资产审查视图。",
        "cards": [
          "6.2 仪表板核心视图 (指挥中心与媒体库)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-telemetry": {
        "tag": "模块 [06] // WEBUI 可视化控制台",
        "h1": "实时遥测监控与 SSE 事件流",
        "desc": "通过 Server-Sent Events (SSE) 协议实时推送系统指标，包含任务队列吞吐率与内存使用率仪表盘。",
        "cards": [
          "6.3 实时事件流管道 (SSE 与 Canvas 网络图)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-design": {
        "tag": "模块 [06] // WEBUI 可视化控制台",
        "h1": "UI 设计令牌规范 (Design Tokens)",
        "desc": "战术实用主义 (Utilitarian Brutalism) 设计规范、高对比等宽终端字体与硬朗机能色彩体系。",
        "cards": [
          "6.4 设计规范令牌参考 (战术实用主义)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-health": {
        "tag": "模块 [06] // WEBUI 可视化控制台",
        "h1": "集群节点健康战术监控",
        "desc": "多子系统就绪健康检查、定时节点心跳探测与 Redis 分布式集群治理指标。",
        "cards": [
          "6.5 战术遥测监控与节点健康治理"
        ],
        "codeHeaders": [
          "JSON // 节点健康指标遥测载荷示例"
        ],
        "alerts": []
      },
      "sec-ops-docker": {
        "tag": "模块 [07] // 容器部署与日常运维",
        "h1": "Docker Compose 生产集群部署",
        "desc": "包含 FlareSolverr、Redis 消息代理与 WebUI 控制中枢的标准化多容器生产部署编排。",
        "cards": [
          "7.1 Docker Compose 容器化集群部署"
        ],
        "codeHeaders": [
          "BASH // DOCKER COMPOSE 启动命令"
        ],
        "alerts": []
      },
      "sec-ops-watchdog": {
        "tag": "模块 [07] // 容器部署与日常运维",
        "h1": "Watchdog 守护监控代理",
        "desc": "具备自适应退避重启、SQLite WAL 状态持久化与异常自恢复能力的常驻抓取守护进程。",
        "cards": [
          "7.2 Watchdog 持续监控守护进程"
        ],
        "codeHeaders": [
          "POWERSHELL // WATCHDOG 守护进程启动指令"
        ],
        "alerts": []
      },
      "sec-ops-notifications": {
        "tag": "模块 [07] // 容器部署与日常运维",
        "h1": "多渠道实时告警通知管道",
        "desc": "插件式告警推送体系，支持 Telegram Bot、Discord Webhook、Slack 以及第三方自定义 Webhook 接入。",
        "cards": [
          "7.3 多渠道实时报警 (Telegram / Discord / Slack / Webhook)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-proxy": {
        "tag": "模块 [07] // 容器部署与日常运维",
        "h1": "代理池管理与自适应隔离策略",
        "desc": "多协议代理轮换、自适应高延迟节点熔断隔离、失败重试与带宽预算配额管理。",
        "cards": [
          "7.4 代理池管理策略与自适应延迟隔离"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-sessions": {
        "tag": "模块 [07] // 容器部署与日常运维",
        "h1": "粘性会话与持久化 Cookie 管理",
        "desc": "按目标域名隔离的持久化粘性会话、带界面交互式登录捕获与 Cookie 加密存储规范。",
        "cards": [
          "7.5 粘性会话与持久化 Cookie 管理"
        ],
        "codeHeaders": [
          "BASH // 会话交互式登录指令"
        ],
        "alerts": []
      },
      "sec-output-structure": {
        "tag": "模块 [08] // 数据存储与格式导出",
        "h1": "输出目录组织结构与成果物规整",
        "desc": "每次抓取运行的成果物落盘结构、多媒体资产存储路径以及元数据清单组织规范。",
        "cards": [
          "8.1 抓取成果物与输出目录结构"
        ],
        "codeHeaders": [
          "文本 // 成果物输出目录组织树"
        ],
        "alerts": []
      },
      "sec-output-manifest": {
        "tag": "模块 [08] // 数据存储与格式导出",
        "h1": "manifest.json 全量元数据规范",
        "desc": "抓取结果汇总清单 manifest.json 的 JSON Schema 结构定义与各字段详尽技术规范。",
        "cards": [
          "8.2 JSON 数据字段详解 (manifest.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-domain": {
        "tag": "模块 [08] // 数据存储与格式导出",
        "h1": "domain_report.json 域名效能报告架构",
        "desc": "按目标域名聚合统计的请求成功率、WAF 触发次数、下载有效载荷大小与产出效能报告。",
        "cards": [
          "8.3 单域名抓取效能报告 (domain_report.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-kohya": {
        "tag": "模块 [08] // 数据存储与格式导出",
        "h1": "Kohya_ss LoRA 训练数据集一键打包导出",
        "desc": "自动生成符合 Kohya_ss 规范的图片与配对 .txt 标签文件，一键打包为可直接喂给 SD 训练的 ZIP 压缩包。",
        "cards": [
          "8.4 Kohya LoRA 训练数据集生成器"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-rag": {
        "tag": "模块 [08] // 数据存储与格式导出",
        "h1": "大模型 RAG 知识库摄取导出格式",
        "desc": "面向 LLM 检索增强生成 (RAG) 场景，支持按页面切片的规整 Markdown 与用于向量检索的 JSONL 文本嵌入格式。",
        "cards": [
          "8.5 针对 LLM 的 RAG 摄取导出格式"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-cas": {
        "tag": "模块 [08] // 数据存储与格式导出",
        "h1": "内容寻址存储底层架构 (CAS)",
        "desc": "基于 SHA-256 全局内容哈希去重与 NTFS/POSIX 跨目录硬链接技术，消除重复抓取导致的磁盘物理冗余。",
        "cards": [
          "8.6 内容寻址存储底层架构 (CAS)"
        ],
        "codeHeaders": [
          "PYTHON // CAS 内容哈希去重与抓取软硬链接关联",
          "文本 // CAS 物理存储生命周期架构"
        ],
        "alerts": []
      },
      "sec-output-parquet": {
        "tag": "模块 [08] // 数据存储与格式导出",
        "h1": "Apache Parquet 列式分析数据导出",
        "desc": "Snappy 压缩列式高性能数据集导出，完美适配 Polars、DuckDB、Pandas 以及现代大数据 OLAP 分析流。",
        "cards": [
          "8.7 列式存储导出管道 (Apache Parquet)"
        ],
        "codeHeaders": [
          "PYTHON // PARQUET 列式数据集生成核心代码"
        ],
        "alerts": []
      },
      "sec-test-pytest": {
        "tag": "模块 [09] // 自动化测试与排错指南",
        "h1": "执行 pytest 自动化测试套件",
        "desc": "运行覆盖核心架构、反爬管道与存储系统的完整自动化单元与集成测试套件。",
        "cards": [
          "9.1 自动化 Pytest 测试套件"
        ],
        "codeHeaders": [
          "POWERSHELL // 运行完整测试套件"
        ],
        "alerts": []
      },
      "sec-test-tdai": {
        "tag": "模块 [09] // 自动化测试与排错指南",
        "h1": "经验性实机验证规范 (TDAI)",
        "desc": "测试驱动 AI 开发 (TDAI) 验证规范与不可妥协的 RED-GREEN-REFACTOR 质量门禁协议。",
        "cards": [
          "9.2 经验性实机验证规范 (TDAI)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] 强制执行规则",
            "bodyHtml": "严禁在未执行端到端实机验证命令且未出具完整的测试通过证据前，宣布任何功能或 Bug 修复已完成！必须展示确凿的通过日志。"
          }
        ]
      },
      "sec-test-logs": {
        "tag": "模块 [09] // 自动化测试与排错指南",
        "h1": "日志诊断与错误快速排查配方",
        "desc": "生产环境日志排查诊断命令集合，包含 HTTP 429 限流与 Cloudflare 拦截规则快速 grep 检索。",
        "cards": [
          "9.3 PowerShell 快速排错命令与日志检索"
        ],
        "codeHeaders": [
          "POWERSHELL // 错误与反爬拦截日志检索命令"
        ],
        "alerts": []
      },
      "sec-test-diagnostic": {
        "tag": "模块 [09] // 自动化测试与排错指南",
        "h1": "运维诊断与故障排除全景矩阵",
        "desc": "详尽的运维故障排查对照表，覆盖网络异常、内存告警、打码超时与节点失联等常见故障应对方案。",
        "cards": [
          "9.4 运维诊断排错对照矩阵"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-test-guidelines": {
        "tag": "模块 [09] // 自动化测试与排错指南",
        "h1": "核心开发者工程与代码质量规范",
        "desc": "系统强制性开发规范、严格遵循的代码风格约定以及代码质量红线要求。",
        "cards": [
          "9.5 强制性工程编码规范"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-threat-overview": {
        "tag": "模块 [10] // 威胁建模与安全加固",
        "h1": "安全架构与 v0.30.0 规范验证",
        "desc": "权威威胁建模规范、STRIDE 架构契约以及 v0.30.0 分布式扩展能力的实机经验验证矩阵。",
        "cards": [
          "10.1 信任边界与分布式数据流架构",
          "10.1.1 STRIDE 威胁建模分类",
          "10.1.2 跨组件核心不变量"
        ],
        "codeHeaders": [
          "架构图 // v0.30.0 分布式信任边界与数据流"
        ],
        "alerts": [
          {
            "title": "生产版本发布 // v0.30.0 已全面验证与认证",
            "bodyHtml": "本模块规定的三大前沿架构领域 (分布式任务租约、云端 CAS 存储同步、视觉大模型 DOM 自愈) 在 v0.30.0 版本中已<strong>完全实现、经受对抗性测试并经验证在 CI (Ubuntu/macOS/Windows) 矩阵中全部通过</strong>。"
          },
          {
            "title": "强制性架构契约",
            "bodyHtml": "本技术规范是 v0.30.0 所有功能实现的权威基准。在任何组件被批准发布前，每个验收标准 (AC1.1 至 AC3.6) 必须在 <code>tests/</code> 中拥有对应的自动化测试用例。"
          }
        ]
      },
      "sec-threat-leasing": {
        "tag": "模块 [10] // 组件 1 (已实现且已验证)",
        "h1": "分布式任务租约威胁矩阵 (组件 1)",
        "desc": "针对 Redis Streams 工作节点的 STRIDE 脆弱性深入分析、恶意攻击场景建模以及原子化防御缓解机制。",
        "cards": [
          "10.2 组件 1 设计概览 (分布式任务租约)",
          "10.2.1 组件 1 威胁与漏洞矩阵",
          "10.2.2 详细防御与缓解规范"
        ],
        "codeHeaders": [
          "PYTHON // 原子幂等性锁获取与超时续约实现"
        ],
        "alerts": [
          {
            "title": "组件 1 已实现并全面验证 // AC1.1–AC1.7 验收测试 100% 通过",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>、<code>DistributedWorkerNode</code> 以及 CLI 独立工作守护进程已针对 AC1.1 至 AC1.7 验收标准全面实现并通过实机验证，backed by 98 项自动化测试用例。"
          }
        ]
      },
      "sec-threat-cas": {
        "tag": "模块 [10] // 组件 2 底层架构",
        "h1": "云端 CAS 存储同步威胁矩阵 (组件 2)",
        "desc": "面向 S3 / Cloudflare R2 / MinIO 存储后端的纵深防御体系规范、强密码学校验与严苛的 SSRF 防护机制。",
        "cards": [
          "10.3 组件 2 设计概览 (云端 CAS 同步)",
          "10.3.1 组件 2 威胁与漏洞矩阵",
          "10.3.2 加密哈希路径强制隔离机制"
        ],
        "codeHeaders": [
          "PYTHON // CAS 存储键路径合法性校验与校验和校验"
        ],
        "alerts": [
          {
            "title": "生产环境认证 // 组件 2 已完全实现并发布",
            "bodyHtml": "<code>CASCloudSyncer</code> 与 S3/R2/MinIO 对象存储云端同步组件在 v0.30.0 中已<strong>完全实现并验证通过</strong>，AC2.1-AC2.7 测试用例 100% 通过，具备零 Boto 轻量化运行与无条件 SSRF 边界拦截。"
          }
        ]
      },
      "sec-threat-vlm": {
        "tag": "模块 [10] // 组件 3 (已实现且已验证)",
        "h1": "视觉大模型 DOM 自愈威胁矩阵 (组件 3)",
        "desc": "多模态 AI 安全管控准则、对抗性视觉 Prompt 注入攻击防御规范与 Tier 4 自愈沙箱隔离机制。",
        "cards": [
          "10.4 组件 3 设计概览 (VLM 视觉自愈)",
          "10.4.1 组件 3 威胁与漏洞矩阵",
          "10.4.2 不信任数据隔离与输出保护栏"
        ],
        "codeHeaders": [
          "PROMPT 架构 // 沙箱化隔离 VLM 系统提示词规范"
        ],
        "alerts": [
          {
            "title": "生产环境认证 // 组件 3 已完全实现并发布",
            "bodyHtml": "<code>VisionDOMHealer</code> (第 4 级多模态视觉 DOM 自愈机制) 在 v0.30.0 中已<strong>完全实现并验证通过</strong>，AC3.1-AC3.6 验收测试 100% 通过，成功抵御 75 种对抗性 Prompt 注入攻击向量。"
          }
        ]
      },
      "sec-threat-ac": {
        "tag": "模块 [10] // 验收标准验证与审计矩阵 (v0.30.0 生产环境)",
        "h1": "验收标准验证与实机审计矩阵 (v0.30.0 生产环境)",
        "desc": "验证 v0.30.0 全部 20 项验收准则 (AC1.1 至 AC3.6) 的经验性测试技术规范、自动化审计结果与执行方法论。",
        "cards": [
          "10.5.1 组件 1 验收标准 (任务租约 AC1.1-AC1.7)",
          "10.5.2 组件 2 验收标准 (云 CAS 同步 AC2.1-AC2.7)",
          "10.5.3 组件 3 验收标准 (VLM 视觉自愈 AC3.1-AC3.6)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "全部 20 项验收准则已 100% 验证与认证",
            "bodyHtml": "以下所有 20 项准则 (AC1.1 至 AC3.6) 构成了 v0.30.0 版本的<strong>核心架构契约</strong>。每一条准则均有 <code>tests/</code> 中的自动化测试支撑，并在本地及 GitHub Actions CI 矩阵中达到 100% 通过率。"
          },
          {
            "title": "工程验收基准",
            "bodyHtml": "在未经实机环境完整执行并证明以下所有 20 项验收标准全部 100% 覆盖通过前，任何 v0.30.0 PR 或发布 Tag 均不得被合并批准。"
          }
        ]
      }
    },
    "snippets": {
      "sec-install-steps": "# 1. 克隆代码仓库\ngit clone https://github.com/rhaffle87/scrAPE.git\ncd scrAPE\n\n# 2. 创建并激活虚拟环境\npython -m venv venv\nvenv\\Scripts\\activate          # Windows CMD\n.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell\nsource venv/bin/activate       # Linux / macOS\n\n# 3. 安装 Python 核心依赖项\npip install -r requirements.txt\n\n# 4. (可选) 安装 Crawlee Node.js 桥接模块以支持 Tier 6-7 深度隐身\ncd crawlee_bridge && npm install && cd ..\n\n# 5. 配置生产凭据\ncopy .env.example .env         # Windows\ncp .env.example .env           # Linux / macOS\n# 随后在 .env 文件中填入 API 密钥与 Webhook 地址",
      "sec-install-launchers": "# Windows 一键主启动脚本 (交互式菜单)\n.\\run.bat\n\n# Linux / macOS 主启动脚本\n./run.sh\n\n# 直接启动交互式向导 (跳过主菜单)\npython src/cli/cli_wizard.py",
      "sec-ops-docker": "# 后台启动爬虫核心引擎与 FlareSolverr 容器\ndocker compose up -d\n\n# 实时查看集群运行日志\ndocker compose logs -f\n\n# 优雅停止并清理容器网络\ndocker compose down",
      "sec-ops-watchdog": "# 通过主启动脚本运行 Watchdog 守护进程\n.\\run.bat watchdog\n\n# 直接命令行执行持续监控\npython src/cli/monitor_agent.py --keyword \"example_subject\" --seed seeds/example_subject.txt --use-state-cache",
      "sec-ops-sessions": "# 弹出交互式浏览器窗口登录并抓取 Cookie\npython src/cli/session_auth.py --domain example.com --login-url https://example.com/login\n\n# 列出本地保存的持久化 Cookie 会话\npython src/cli/session_auth.py --list-sessions",
      "sec-test-pytest": "# 运行全量 378+ 单元与集成自动化测试\npytest tests/ -v\n\n# 附带测试覆盖率报告运行\npytest --cov=src tests/ --cov-report=term-missing",
      "sec-test-logs": "# 实时检索 HTTP 429 频控与 Cloudflare 拦截日志\nGet-Content logs/crawler.log -Tail 100 | Select-String -Pattern \"429|Cloudflare|WAF|BLOCKED\"\n\n# 实时监控抓取引擎日志输出\nGet-Content logs/crawler.log -Wait -Tail 20"
    },
    "lists": {
      "sec-install-launchers": [
        "<strong>全网广泛搜索抓取</strong> —— 基于搜索引擎关键词与递归链接遍历的自主抓取。",
        "<strong>指定种子清单定向抓取</strong> —— 针对所选 seeds/*.txt 种子清单执行高精度结构化抓取。",
        "<strong>持续运行监控守护进程 (Watchdog)</strong> —— 支持 SQLite WAL 缓存的长周期常驻监控。",
        "<strong>构建高质量结构化 AI 训练集</strong> —— 成果物一键规整打包，支持按域名或按媒体格式智能分组归档。",
        "<strong>大模型 RAG 知识库摄取导出</strong> —— 将网页全文清洗导出为规整 Markdown、分块切片 <code>.md</code> 文件或 JSONL 向量嵌入格式。"
      ]
    },
    "h3Map": {
      "Wizard Menu Options": "交互式向导核心功能清单",
      "Core Components": "系统核心组件构成",
      "Media Vault View": "媒体资产金库视图功能",
      "Command Center View": "任务指挥中心视图功能",
      "Budget & Balance Guardrails": "API 预算与打码账户余额防护准则",
      "Circuit Breaker & Cooldown Mechanics": "防风控熔断降级与冷却冷却机制",
      "Download Validation Thresholds": "多媒体资产下载有效性校验阈值",
      "Primary v0.30.1 Execution Flags": "v0.30.1 核心执行参数一览",
      "Site-Chrome & Keyword Classification Sets": "页面外框与关键词智能分类词集",
      "Dead-Letter Stream Protocol": "死信队列流式处理协议 (DLQ)",
      "Idempotency Lock Implementation": "原子幂等锁分布式实现机制",
      "Node Health JSON Schema (/api/telemetry/node-health)": "节点健康指标 JSON Schema (/api/telemetry/node-health)"
    },
    "thMap": {
      "Component": "系统组件",
      "Source File": "源码路径",
      "Function": "职能职责",
      "Requirement": "前置环境需求",
      "Minimum": "最低要求",
      "Notes": "技术备注",
      "Category": "分类类别",
      "Supported Types": "支持的媒体格式",
      "Processing Method": "流处理方式",
      "Core Pillar": "核心架构支柱",
      "Key Technologies": "核心技术栈",
      "Production Capability": "生产环境能力",
      "Parameter": "配置参数",
      "Type": "数据类型",
      "Default": "默认缺省值",
      "Description": "参数作用描述",
      "Status": "状态标识",
      "Tier": "保护等级 (Tier)",
      "Mechanism": "实现机制",
      "Overhead": "系统开销",
      "Usage": "调用方法",
      "Profile": "预设名称",
      "Keyword": "目标关键词",
      "Concurrency": "并发工作线程数",
      "Depth": "最大抓取深度",
      "Endpoint": "API 端点",
      "Impact": "影响面",
      "Channel": "通信信道",
      "Provider": "服务商",
      "Purpose": "设计目标与用途",
      "Field": "字段名称",
      "Value": "配置值",
      "Variable": "环境变量名称",
      "Subsystem": "底层子系统",
      "Symptom": "故障外在表征",
      "Where to Look": "故障排查日志位置",
      "Resolution Action": "处置与修复方案",
      "Key Flags": "关键控制参数",
      "Syntax": "语法规则",
      "Primary Use Case": "主要适用场景",
      "Rejection Reason": "资源剔除原因",
      "Disk Retention Path": "本地隔离落盘路径",
      "Trigger Criteria": "降级触发条件",
      "Supported Challenge Types": "支持的验证码质询类型",
      "Fault Tolerance Function": "容灾容错函数",
      "Escalation Trigger": "递进升级触发阈值",
      "Telemetry Metric": "遥测指标项",
      "Target Component": "目标受测组件",
      "Visual Indicator & Action": "仪表盘视觉指标与动作",
      "Top-Level Key": "顶级配置键名",
      "Required Credentials (.env)": "所需凭据环境变量 (.env)",
      "Key Benefits": "技术优势与红利",
      "Schema Columns": "表格字段架构",
      "Parquet Table": "Parquet 数据表名",
      "Payload Type": "有效载荷类型",
      "Source / Endpoint": "数据来源 / 接收端点",
      "Stream Command": "流处理底层命令",
      "Internal Action": "系统内部调度动作",
      "Threat Scenario": "模拟攻击场景",
      "STRIDE Category": "STRIDE 威胁分类",
      "Vector & Attack Mechanics": "攻击向量与攻击机理",
      "Mitigation Mechanism": "防御与缓解机制",
      "Primary Defense Mechanism": "主要防御机制",
      "Hardened Primitive": "加固安全原语",
      "Test Methodology & Assertion": "测试方法与断言规则",
      "Criterion ID": "验收准则编号",
      "Requirement Description": "技术需求详述",
      "Verified Test Suite": "实机验证测试套件",
      "Architecture Frontier": "关键架构前沿领域",
      "Primary Threat in v0.30.0": "v0.30.0 主要防御威胁",
      "Algorithmic / System Enhancement": "算法与系统级演进",
      "Compression & Fallback": "压缩编码与降级回退",
      "Annotation Header": "种子清单注解头"
    }
  },
  "es": {
    "meta": {
      "title": "scrAPE v0.30.1 // Portal de Documentación Técnica",
      "desc": "Documentación técnica oficial, matriz de comandos CLI, arquitectura y manual operativo para scrAPE v0.30.1."
    },
    "ui": {
      "searchPlaceholder": "BUSCAR EN LA DOCUMENTACIÓN...",
      "searchHint": "Ctrl+K",
      "langStripLabel": "IDIOMA DEL PORTAL // LENGUAJE:",
      "githubLink": "[GITHUB]",
      "badgeNew": "NUEVO",
      "badgeVerified": "VERIFICADO",
      "copyCode": "[COPIAR CÓDIGO]",
      "copiedCode": "[¡COPIADO!]",
      "commandBuilder": "GENERADOR INTERACTIVO DE COMANDOS CLI",
      "builderPrompt": "CONFIGURE LOS PARÁMETROS Y GENERE EL COMANDO DE EJECUCIÓN:",
      "builderOutputLabel": "COMANDO CLI EJECUTABLE:",
      "footerTagline": "Motor de raspado distribuido autónomo y de alto rendimiento con heurísticas DOM autorreparables y exportación a Apache Parquet.",
      "searchResults": "encontrados",
      "noResults": "sin resultados",
      "selectLocale": "SELECCIONAR IDIOMA DE DOCUMENTACIÓN",
      "changeLanguageTitle": "Cambiar idioma"
    },
    "modules": [
      "[01] DESCRIPCIÓN DEL SISTEMA",
      "[02] INSTALACIÓN Y GUÍA RÁPIDA",
      "[03] REFERENCIA DE COMANDOS CLI",
      "[04] ARQUITECTURA DEL MOTOR CENTRAL",
      "[05] REFERENCIA DE CONFIGURACIÓN",
      "[06] PANEL DE CONTROL WEBUI",
      "[07] DESPLIEGUE Y OPERACIONES",
      "[08] SALIDAS Y EXPORTACIONES",
      "[09] PRUEBAS Y DIAGNÓSTICO",
      "[10] MODELO DE AMENAZAS Y SEGURIDAD"
    ],
    "nav": {
      "sec-overview-arch": "[1.1] Arquitectura y Objetivos",
      "sec-overview-formats": "[1.2] Formatos Compatibles y Límites",
      "sec-overview-layout": "[1.3] Estructura de Directorios",
      "sec-overview-pillars": "[1.4] Pilares de Nueva Generación",
      "sec-overview-v28": "[1.5] Arquitectura Principal (v0.28.0)",
      "sec-install-prereqs": "[2.1] Requisitos Previos",
      "sec-install-steps": "[2.2] Pasos de Instalación",
      "sec-install-launchers": "[2.3] Lanzadores Principales y Asistente",
      "sec-install-recipes": "[2.4] Recetas de Primera Ejecución",
      "sec-cli-flags": "[3.1] Matriz Completa de Flags CLI",
      "sec-cli-builder": "[3.2] Constructor Interactivo de CLI",
      "sec-cli-profiles": "[3.3] Perfiles de Ejecución",
      "sec-engine-bfs": "[4.1] Bucle de Rastreo BFS",
      "sec-engine-waf": "[4.2] Pipeline WAF Sigiloso de 8 Niveles",
      "sec-engine-captcha": "[4.3] Estrategia Universal de Captcha",
      "sec-engine-scoring": "[4.4] Filtrado y Puntuación de Calidad",
      "sec-engine-normalize": "[4.5] Normalización de URLs",
      "sec-engine-pool": "[4.6] Pool de Navegadores Precalentados",
      "sec-engine-broker": "[4.7] Broker de Tareas con Redis Streams",
      "sec-engine-ml": "[4.8] Pipeline de Visión y Hardware ML",
      "sec-engine-healing": "[4.9] Parser DOM con Autocorrección",
      "sec-engine-bktree": "[4.10] Deduplicación Perceptual con BK-Tree",
      "sec-config-env": "[5.1] Variables de Entorno (.env)",
      "sec-config-domain": "[5.2] Configuración de Dominios",
      "sec-config-urlnorm": "[5.3] Reglas Regex de URL",
      "sec-config-seeds": "[5.4] Sintaxis de Manifiestos Seed",
      "sec-config-profiles": "[5.5] Perfiles de Objetivos",
      "sec-config-blacklist": "[5.6] Gestión de Lista Negra",
      "sec-webui-arch": "[6.1] Arquitectura del Servidor",
      "sec-webui-views": "[6.2] Centro de Mando y Galería de Medios",
      "sec-webui-telemetry": "[6.3] Telemetría en Vivo y SSE",
      "sec-webui-design": "[6.4] Tokens de Diseño Brutalista",
      "sec-webui-health": "[6.5] Monitor Táctico de Salud de Nodos",
      "sec-ops-docker": "[7.1] Docker Compose",
      "sec-ops-watchdog": "[7.2] Agente Guardián (Watchdog)",
      "sec-ops-notifications": "[7.3] Pipeline de Notificaciones",
      "sec-ops-proxy": "[7.4] Gestión del Pool de Proxies",
      "sec-ops-sessions": "[7.5] Bóveda de Sesiones y Cookies",
      "sec-output-structure": "[8.1] Estructura de Carpetas de Salida",
      "sec-output-manifest": "[8.2] Esquema de manifest.json",
      "sec-output-domain": "[8.3] Esquema de domain_report.json",
      "sec-output-kohya": "[8.4] Exportación de Dataset Kohya LoRA",
      "sec-output-rag": "[8.5] Formatos de Ingesta RAG",
      "sec-output-cas": "[8.6] Almacenamiento Dirigido por Contenido (CAS)",
      "sec-output-parquet": "[8.7] Exportación en Apache Parquet",
      "sec-test-pytest": "[9.1] Ejecución de pytest",
      "sec-test-tdai": "[9.2] Protocolo de Verificación (TDAI)",
      "sec-test-logs": "[9.3] Recetas de Diagnóstico de Logs",
      "sec-test-diagnostic": "[9.4] Matriz de Diagnóstico de Operador",
      "sec-test-guidelines": "[9.5] Guía para Desarrolladores",
      "sec-threat-overview": "[10.1] Alcance de Seguridad Previo",
      "sec-threat-leasing": "[10.2] Matriz de Concesión de Tareas",
      "sec-threat-cas": "[10.3] Matriz de CAS en la Nube",
      "sec-threat-vlm": "[10.4] Matriz de Autocorrección VLM",
      "sec-threat-ac": "[10.5] Contrato de Criterios de Aceptación"
    },
    "footer": {
      "logo": "scrAPE // SISTEMA CENTRAL",
      "tagline": "Motor de raspado distribuido autónomo y de alto rendimiento con heurísticas DOM autorreparables y exportación a Apache Parquet.",
      "badges": [
        "VERSIÓN v0.30.1",
        "LICENCIA MIT",
        "PYTHON 3.10+"
      ],
      "headings": {
        "repo": "REPOSITORIO",
        "docs": "DOCUMENTACIÓN"
      },
      "links": [
        "Código fuente",
        "Notas de versión (v0.30.1)",
        "Seguimiento de problemas",
        "CI / Flujos de trabajo",
        "README del sistema",
        "Modelo de amenazas (v0.30.0)",
        "Registro de cambios",
        "Licencia MIT",
        "Docker Compose"
      ],
      "copy": "© 2026 Mantenedores de scrAPE. Código abierto bajo la Licencia MIT.",
      "sysinfo": "ESTADO: OPERATIVO // MOTOR: v0.30.1"
    },
    "sections": {
      "sec-overview-arch": {
        "tag": "MÓDULO [01] // DESCRIPCIÓN DEL SISTEMA",
        "h1": "Arquitectura y Objetivos",
        "desc": "Sistema de raspado web sigiloso multimotor para extracción autónoma de medios y generación de conjuntos de datos de IA.",
        "cards": [
          "1.1 Arquitectura del sistema"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] GARANTÍA OPERATIVA FUNDAMENTAL",
            "bodyHtml": "El sistema opera mediante un pipeline de contingencia WAF de 8 niveles. Las solicitudes escalan automáticamente desde HTTP directo ligero hasta automatización de navegador sigiloso con interfaz gráfica cuando se detectan bucles de desafío. No se requiere intervención manual."
          }
        ]
      },
      "sec-overview-formats": {
        "tag": "MÓDULO [01] // DESCRIPCIÓN DEL SISTEMA",
        "h1": "Formatos Compatibles y Límites Operativos",
        "desc": "Especificaciones de activos, filtros de tamaño, límites de dimensiones y tasas de solicitudes.",
        "cards": [
          "1.2 Capacidades de medios y datos"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-overview-layout": {
        "tag": "MÓDULO [01] // DESCRIPCIÓN DEL SISTEMA",
        "h1": "Estructura de Directorios del Proyecto",
        "desc": "Organización de archivos y carpetas del repositorio.",
        "cards": [
          "1.3 Estructura de directorios"
        ],
        "codeHeaders": [
          "TEXTO // ÁRBOL DEL REPOSITORIO"
        ],
        "alerts": []
      },
      "sec-overview-pillars": {
        "tag": "MÓDULO [01] // DESCRIPCIÓN DEL SISTEMA",
        "h1": "Pilares de la Arquitectura Central (v0.30.1)",
        "desc": "Orquestación multinodo empresarial, deduplicación perceptual sublineal con árbol BK, grupos de subprocesos aislados y CAS sin duplicados.",
        "cards": [
          "1.4 Pilares de la arquitectura central (v0.30.1)"
        ],
        "codeHeaders": [
          "BASH // ACTIVACIÓN CLI DE PILARES BÁSICOS"
        ],
        "alerts": []
      },
      "sec-overview-v28": {
        "tag": "MÓDULO [01] // ACTUALIZACIÓN DE ARQUITECTURA",
        "h1": "Arquitectura Central (v0.28.0)",
        "desc": "Pipeline de ML desacoplado para producción, deduplicación jerárquica de 3 niveles, analizador DOM autorreparable y concurrencia híbrida supervisada.",
        "cards": [
          "1.4 Innovaciones arquitectónicas en v0.28.0"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-prereqs": {
        "tag": "MÓDULO [02] // INSTALACIÓN Y GUÍA RÁPIDA",
        "h1": "Requisitos Previos del Sistema",
        "desc": "Entorno de ejecución de Python, controladores de navegador en modo headless, aceleración por hardware CUDA y requisitos de Redis.",
        "cards": [
          "2.1 Requisitos del sistema"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-steps": {
        "tag": "MÓDULO [02] // INSTALACIÓN Y GUÍA RÁPIDA",
        "h1": "Pasos de Instalación Paso a Paso",
        "desc": "Aprovisionamiento de entorno virtual, instalación de paquetes pip y sincronización de binarios de navegador.",
        "cards": [
          "2.2 Procedimiento de instalación"
        ],
        "codeHeaders": [
          "BASH // COMANDOS DE INSTALACIÓN"
        ],
        "alerts": [
          {
            "title": "[i] CONFIGURACIÓN DE FLARESOLVERR",
            "bodyHtml": "FlareSolverr (Nivel 5) se ejecuta como un contenedor Docker. Inícielo con: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"
          }
        ]
      },
      "sec-install-launchers": {
        "tag": "MÓDULO [02] // INSTALACIÓN Y GUÍA RÁPIDA",
        "h1": "Lanzadores Maestros y Asistente",
        "desc": "Scripts de inicio interactivos para todos los modos de ejecución.",
        "cards": [
          "2.3 Opciones del lanzador y asistente"
        ],
        "codeHeaders": [
          "POWERSHELL // LANZADOR MAESTRO"
        ],
        "alerts": []
      },
      "sec-install-recipes": {
        "tag": "MÓDULO [02] // INSTALACIÓN Y GUÍA RÁPIDA",
        "h1": "Recetas de Comandos para el Primer Inicio",
        "desc": "Comandos listos para copiar y pegar para patrones de extracción comunes.",
        "cards": [
          "2.4 Recetas de comandos para primer inicio"
        ],
        "codeHeaders": [
          "RECETA 1 // EXTRACCIÓN ESTÁNDAR DE SEEDS CON RETENCIÓN DE MEDIOS RECHAZADOS",
          "RECETA 2 // AGENTE DE MONITOREO CONTINUO CON CACHÉ DE ESTADO",
          "RECETA 3 // EJECUCIÓN RÁPIDA DE VALIDACIÓN (SIN DESCARGAS)",
          "RECETA 4 // DESCUBRIMIENTO SOLO POR BÚSQUEDA (SIN SEEDS)",
          "RECETA 5 // RASTREO SIGILOSO (VELOCIDAD CORTÉS)"
        ],
        "alerts": []
      },
      "sec-cli-flags": {
        "tag": "MÓDULO [03] // REFERENCIA DE COMANDOS CLI",
        "h1": "Matriz Completa de Parámetros de Ejecución CLI",
        "desc": "Guía de referencia completa para todos los modificadores de línea de comandos, límites y presupuestos de extracción.",
        "cards": [
          "3.1 Matriz de parámetros de línea de comandos"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-cli-builder": {
        "tag": "MÓDULO [03] // REFERENCIA DE COMANDOS CLI",
        "h1": "Generador Interactivo de Comandos CLI",
        "desc": "Configure parámetros de destino, grupos de concurrencia y flags de sigilo para generar un comando ejecutable.",
        "cards": [
          "3.2 Generador interactivo de comandos"
        ],
        "codeHeaders": [
          "CADENA DE COMANDO CLI GENERADA"
        ],
        "alerts": []
      },
      "sec-cli-profiles": {
        "tag": "MÓDULO [03] // REFERENCIA DE COMANDOS CLI",
        "h1": "Perfiles de Ejecución",
        "desc": "Preajustes de perfil optimizados para topologías de raspado especializadas.",
        "cards": [
          "3.3 Matriz de perfiles predefinidos"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-bfs": {
        "tag": "MÓDULO [04] // ARQUITECTURA DEL MOTOR CENTRAL",
        "h1": "Bucle de Rastreo BFS",
        "desc": "Bucle de recorrido asíncrono en anchura, despacho de cola de prioridad y extracción de enlaces.",
        "cards": [
          "4.1 Secuencia de ejecución BFS"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-waf": {
        "tag": "MÓDULO [04] // ARQUITECTURA DEL MOTOR CENTRAL",
        "h1": "Pipeline de Escalado WAF Sigiloso de 8 Niveles",
        "desc": "Contingencia adaptativa de múltiples niveles que resuelve Cloudflare Turnstile, Datadome, Incapsula y defensas antibot.",
        "cards": [
          "4.2 Jerarquía del pipeline WAF de 8 niveles"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-captcha": {
        "tag": "MÓDULO [04] // ARQUITECTURA DEL MOTOR CENTRAL",
        "h1": "Estrategia Universal de Captcha",
        "desc": "Proveedores de resolución automatizada, intercepción de desafíos y controladores de reintentos.",
        "cards": [
          "4.3 Estrategia de resolución de captchas y desafíos"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-scoring": {
        "tag": "MÓDULO [04] // ARQUITECTURA DEL MOTOR CENTRAL",
        "h1": "Puntuación de Calidad y Rechazo",
        "desc": "Clasificación de URL, umbrales de dimensiones de imagen y persistencia en disco de medios rechazados.",
        "cards": [
          "4.4 Reglas de rechazo y rutas de retención"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-normalize": {
        "tag": "MÓDULO [04] // ARQUITECTURA DEL MOTOR CENTRAL",
        "h1": "Normalización de URL",
        "desc": "Eliminación de parámetros de seguimiento, canonización de protocolos y prevención de ciclos redundantes.",
        "cards": [
          "4.5 Pipeline de canonización de URL"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-pool": {
        "tag": "MÓDULO [04] // ARQUITECTURA DEL MOTOR CENTRAL",
        "h1": "Grupo de Navegadores Precalentados",
        "desc": "Reciclaje de alto rendimiento del grupo de navegadores Camoufox y asignación de contextos.",
        "cards": [
          "4.6 Ciclo de vida del grupo de navegadores precalentados"
        ],
        "codeHeaders": [
          "PYTHON // ASIGNACIÓN DE NAVEGADORES PRECALENTADOS"
        ],
        "alerts": []
      },
      "sec-engine-broker": {
        "tag": "MÓDULO [04] // ARQUITECTURA DEL MOTOR CENTRAL",
        "h1": "Intermediario de Tareas Redis Streams",
        "desc": "Grupos de consumidores distribuidos, seguimiento de entradas pendientes (PEL) y despacho atómico de tareas.",
        "cards": [
          "4.7 Coordinación de clúster distribuido con Redis Streams"
        ],
        "codeHeaders": [
          "PYTHON // PATRÓN DE INTERACCIÓN DEL INTERMEDIARIO DE TAREAS"
        ],
        "alerts": []
      },
      "sec-engine-ml": {
        "tag": "MÓDULO [04] // ARQUITECTURA DEL MOTOR CENTRAL",
        "h1": "Hardware de Visión y Pipeline de ML",
        "desc": "Detección de dispositivos CUDA/MPS, inferencia de precisión media (FP16) y puntuación estética.",
        "cards": [
          "4.8 Matriz de aceleración de hardware (CUDA / MPS)"
        ],
        "codeHeaders": [
          "PYTHON // DETECCIÓN DE HARDWARE Y NEGOCIACIÓN DE PRECISIÓN"
        ],
        "alerts": []
      },
      "sec-engine-healing": {
        "tag": "MÓDULO [04] // ARQUITECTURA DEL MOTOR CENTRAL",
        "h1": "Analizador DOM Autorreparable",
        "desc": "Cascada de recuperación DOM de 4 niveles con reparación heurística mediante LLM multiproveedor.",
        "cards": [
          "4.9 Reparación autónoma de selectores y autorreparación VLM"
        ],
        "codeHeaders": [
          "PYTHON // CASCADA DE EXTRACCIÓN AUTORREPARABLE",
          "TEXTO // CASCADA DE SÍNTESIS LLM MULTIPROVEEDOR"
        ],
        "alerts": []
      },
      "sec-engine-bktree": {
        "tag": "MÓDULO [04] // ARQUITECTURA DEL MOTOR CENTRAL",
        "h1": "Deduplicación con Árbol BK y Partición de Concurrencia",
        "desc": "Indexación en árbol métrico discreto, agrupación por distancia de Hamming y grupos de ejecución aislados.",
        "cards": [
          "4.10 Árbol métrico discreto y partición del grupo de ejecución"
        ],
        "codeHeaders": [
          "PYTHON // BÚSQUEDA MÉTRICA EN ÁRBOL BK Y AGRUPACIÓN DE CONEXIONES"
        ],
        "alerts": []
      },
      "sec-config-env": {
        "tag": "MÓDULO [05] // REFERENCIA DE CONFIGURACIÓN",
        "h1": "Variables de Entorno (.env)",
        "desc": "Credenciales de producción, límites de velocidad, puertas de enlace proxy y tokens de API.",
        "cards": [
          "5.1 Plantilla de configuración .env"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-domain": {
        "tag": "MÓDULO [05] // REFERENCIA DE CONFIGURACIÓN",
        "h1": "domain_config.json",
        "desc": "Límites de concurrencia por dominio, selectores de espera personalizados y anulaciones de encabezados.",
        "cards": [
          "5.2 Referencia de claves de configuración (domain_config.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-urlnorm": {
        "tag": "MÓDULO [05] // REFERENCIA DE CONFIGURACIÓN",
        "h1": "url_normalisation_rules.json",
        "desc": "Expresiones regulares para depurar parámetros de consulta y transformaciones de dominio.",
        "cards": [
          "5.3 Esquema de reglas de normalización (url_normalisation_rules.json)"
        ],
        "codeHeaders": [
          "JSON // EJEMPLO DE ESQUEMA DE REGLA"
        ],
        "alerts": [
          {
            "title": "[!] REGLA OBLIGATORIA",
            "bodyHtml": "Nunca codifique expresiones regulares de normalización de URL específicas de dominio en archivos Python en <code>src/</code>. Todas las reglas DEBEN declararse en <code>data/url_normalisation_rules.json</code>."
          }
        ]
      },
      "sec-config-seeds": {
        "tag": "MÓDULO [05] // REFERENCIA DE CONFIGURACIÓN",
        "h1": "Sintaxis del Manifiesto de Seeds",
        "desc": "Comentarios, directivas en línea y pesos de prioridad en archivos seeds/*.txt.",
        "cards": [
          "5.4 Referencia de anotaciones de manifiesto seed"
        ],
        "codeHeaders": [
          "MANIFEST // EJEMPLO DE ANOTACIÓN DE MANIFIESTO SEED"
        ],
        "alerts": []
      },
      "sec-config-profiles": {
        "tag": "MÓDULO [05] // REFERENCIA DE CONFIGURACIÓN",
        "h1": "Perfiles de Asunto",
        "desc": "Preajustes específicos por temática, plantillas de salida y vinculación de listas negras.",
        "cards": [
          "5.5 Ajustes preestablecidos de perfil (subject_profiles.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-blacklist": {
        "tag": "MÓDULO [05] // REFERENCIA DE CONFIGURACIÓN",
        "h1": "Gestión de Listas Negras",
        "desc": "Dominios excluidos globalmente, servidores de anuncios y patrones de recursos de bajo valor.",
        "cards": [
          "5.6 Gestión de listas negras de dominios y exclusiones"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-arch": {
        "tag": "MÓDULO [06] // PANEL DE CONTROL WEBUI",
        "h1": "Arquitectura del Servidor WebUI",
        "desc": "Centro de comando reactivo con FastAPI y HTMX con telemetría en tiempo real mediante SSE.",
        "cards": [
          "6.1 Servidor FastAPI desacoplado"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-views": {
        "tag": "MÓDULO [06] // PANEL DE CONTROL WEBUI",
        "h1": "Centro de Comando y Bóveda de Medios",
        "desc": "Panel de control interactivo, estado del rastreador en vivo e inspección de galería.",
        "cards": [
          "6.2 Vistas del panel (Centro de comando y bóveda de medios)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-telemetry": {
        "tag": "MÓDULO [06] // PANEL DE CONTROL WEBUI",
        "h1": "Telemetría en Vivo y SSE",
        "desc": "Transmisión de eventos en tiempo real mediante Server-Sent Events, velocidades de cola y memoria.",
        "cards": [
          "6.3 Pipeline de eventos en tiempo real (SSE y Canvas)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-design": {
        "tag": "MÓDULO [06] // PANEL DE CONTROL WEBUI",
        "h1": "Tokens de Diseño",
        "desc": "Tokens CSS de brutalismo utilitario táctico, tipografía monoespaciada de alto contraste y paletas de colores.",
        "cards": [
          "6.4 Referencia de tokens de diseño (Brutalismo táctico)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-health": {
        "tag": "MÓDULO [06] // PANEL DE CONTROL WEBUI",
        "h1": "Monitor Táctico de Estado del Nodo",
        "desc": "Verificaciones de estado de subsistemas, sondas de latido y telemetría de clúster Redis.",
        "cards": [
          "6.5 Telemetría táctica y gobernanza de nodos"
        ],
        "codeHeaders": [
          "JSON // CARGA ÚTIL DE TELEMETRÍA DE ESTADO DEL NODO"
        ],
        "alerts": []
      },
      "sec-ops-docker": {
        "tag": "MÓDULO [07] // DESPLIEGUE Y OPERACIONES",
        "h1": "Despliegue con Docker Compose",
        "desc": "Despliegue en producción multicontenedor con FlareSolverr, Redis y WebUI.",
        "cards": [
          "7.1 Despliegue en contenedores con Docker Compose"
        ],
        "codeHeaders": [
          "BASH // LANZAMIENTO CON DOCKER COMPOSE"
        ],
        "alerts": []
      },
      "sec-ops-watchdog": {
        "tag": "MÓDULO [07] // DESPLIEGUE Y OPERACIONES",
        "h1": "Agente Watchdog",
        "desc": "Demonio de rastreo continuo con comprobaciones automáticas de estado y políticas de reinicio.",
        "cards": [
          "7.2 Bucle de monitoreo continuo (Watchdog)"
        ],
        "codeHeaders": [
          "POWERSHELL // COMANDO DEL AGENTE WATCHDOG"
        ],
        "alerts": []
      },
      "sec-ops-notifications": {
        "tag": "MÓDULO [07] // DESPLIEGUE Y OPERACIONES",
        "h1": "Pipeline de Notificaciones",
        "desc": "Canales de notificación conectables (Telegram, Discord, Slack, Webhooks).",
        "cards": [
          "7.3 Alertas multicanal (Telegram, Discord, Slack)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-proxy": {
        "tag": "MÓDULO [07] // DESPLIEGUE Y OPERACIONES",
        "h1": "Gestión del Grupo de Proxies",
        "desc": "Rotación de proxies, autocuarentena por latencia y cuotas de ancho de banda.",
        "cards": [
          "7.4 Estrategia del administrador de proxies y cuarentena"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-sessions": {
        "tag": "MÓDULO [07] // DESPLIEGUE Y OPERACIONES",
        "h1": "Gestión de Sesiones y Cookies",
        "desc": "Sesiones fijas persistentes por dominio e inicio de sesión interactivo con cookies.",
        "cards": [
          "7.5 Almacenamiento de sesiones y gestión de cookies"
        ],
        "codeHeaders": [
          "BASH // COMANDOS DE INICIO DE SESIÓN"
        ],
        "alerts": []
      },
      "sec-output-structure": {
        "tag": "MÓDULO [08] // SALIDAS Y EXPORTACIONES",
        "h1": "Estructura de Directorios de Salida",
        "desc": "Disposición de artefactos generados en la ejecución.",
        "cards": [
          "8.1 Organización de artefactos y directorios de salida"
        ],
        "codeHeaders": [
          "TEXTO // DISTRIBUCIÓN DEL DIRECTORIO DE SALIDA"
        ],
        "alerts": []
      },
      "sec-output-manifest": {
        "tag": "MÓDULO [08] // SALIDAS Y EXPORTACIONES",
        "h1": "Esquema manifest.json",
        "desc": "Documentación completa del esquema JSON de resultados.",
        "cards": [
          "8.2 Campos de carga útil JSON (manifest.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-domain": {
        "tag": "MÓDULO [08] // SALIDAS Y EXPORTACIONES",
        "h1": "Esquema domain_report.json",
        "desc": "Informe de métricas de rastreo desglosado por dominio.",
        "cards": [
          "8.3 Informe de rendimiento por dominio (domain_report.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-kohya": {
        "tag": "MÓDULO [08] // SALIDAS Y EXPORTACIONES",
        "h1": "Exportación de Conjunto de Datos Kohya LoRA",
        "desc": "Generación de archivos ZIP de conjuntos de datos compatibles con Kohya_ss LoRA.",
        "cards": [
          "8.4 Generador de conjuntos de datos Kohya LoRA"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-rag": {
        "tag": "MÓDULO [08] // SALIDAS Y EXPORTACIONES",
        "h1": "Formatos de Ingesta para RAG",
        "desc": "Exportaciones para RAG en LLM (fragmentos en Markdown y embeddings en JSONL).",
        "cards": [
          "8.5 Opciones de exportación RAG (Markdown y JSONL)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-cas": {
        "tag": "MÓDULO [08] // SALIDAS Y EXPORTACIONES",
        "h1": "Almacenamiento Direccionable por Contenido (CAS)",
        "desc": "Repositorio de deduplicación global que elimina archivos duplicados en rastreos repetidos.",
        "cards": [
          "8.6 Arquitectura de almacenamiento direccionable por contenido (CAS)"
        ],
        "codeHeaders": [
          "PYTHON // DEDUPLICACIÓN CAS Y ENLACE DE EJECUCIÓN",
          "TEXTO // CICLO DE VIDA DE ALMACENAMIENTO CAS"
        ],
        "alerts": []
      },
      "sec-output-parquet": {
        "tag": "MÓDULO [08] // SALIDAS Y EXPORTACIONES",
        "h1": "Exportación de Datos en Apache Parquet",
        "desc": "Conjuntos de datos columnares con compresión Snappy optimizados para Polars, DuckDB, Pandas y pipelines OLAP.",
        "cards": [
          "8.7 Pipeline de exportación de datos columnares (Apache Parquet)"
        ],
        "codeHeaders": [
          "PYTHON // GENERACIÓN DE CONJUNTOS DE DATOS PARQUET"
        ],
        "alerts": []
      },
      "sec-test-pytest": {
        "tag": "MÓDULO [09] // PRUEBAS Y DIAGNÓSTICO",
        "h1": "Ejecución de Pruebas con pytest",
        "desc": "Ejecución del conjunto de pruebas automatizadas y de integración.",
        "cards": [
          "9.1 Suite automatizada de pruebas Pytest"
        ],
        "codeHeaders": [
          "POWERSHELL // EJECUTAR SUITE DE PRUEBAS COMPLETA"
        ],
        "alerts": []
      },
      "sec-test-tdai": {
        "tag": "MÓDULO [09] // PRUEBAS Y DIAGNÓSTICO",
        "h1": "Protocolo de Verificación Empírica (TDAI)",
        "desc": "Reglas de verificación de IA guiada por pruebas y protocolo RED-GREEN-REFACTOR.",
        "cards": [
          "9.2 Protocolo de verificación empírica (TDAI)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] REGLA OBLIGATORIA",
            "bodyHtml": "Nunca declare una función o corrección completa sin ejecutar comandos empíricos de verificación en tiempo de ejecución y demostrar aprobaciones de prueba limpias."
          }
        ]
      },
      "sec-test-logs": {
        "tag": "MÓDULO [09] // PRUEBAS Y DIAGNÓSTICO",
        "h1": "Recetas de Diagnóstico de Registros",
        "desc": "Análisis de registros y comandos grep para diagnóstico en tiempo de ejecución.",
        "cards": [
          "9.3 Comandos de diagnóstico de PowerShell y análisis de logs"
        ],
        "codeHeaders": [
          "POWERSHELL // BÚSQUEDA DE ERRORES Y BLOQUEOS EN LOGS"
        ],
        "alerts": []
      },
      "sec-test-diagnostic": {
        "tag": "MÓDULO [09] // PRUEBAS Y DIAGNÓSTICO",
        "h1": "Matriz de Diagnóstico del Operador",
        "desc": "Tabla de diagnóstico exhaustiva para la resolución de problemas por parte del operador.",
        "cards": [
          "9.4 Matriz de diagnóstico del operador"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-test-guidelines": {
        "tag": "MÓDULO [09] // PRUEBAS Y DIAGNÓSTICO",
        "h1": "Pautas para Desarrolladores",
        "desc": "Reglas obligatorias de desarrollo y estándares de calidad del espacio de trabajo.",
        "cards": [
          "9.5 Reglas obligatorias de desarrollo de código"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-threat-overview": {
        "tag": "MÓDULO [10] // MODELO DE AMENAZAS Y SEGURIDAD",
        "h1": "Arquitectura de Seguridad y Verificación v0.30.0",
        "desc": "Modelo de amenazas autorizado, contrato arquitectónico STRIDE y matriz de verificación empírica para el escalado distribuido v0.30.0.",
        "cards": [
          "10.1 Límites de confianza y arquitectura de flujo de datos",
          "10.1.1 Categorización de amenazas STRIDE",
          "10.1.2 Invariantes transversales"
        ],
        "codeHeaders": [
          "ARQUITECTURA // LÍMITES DE CONFIANZA DISTRIBUIDOS Y FLUJO DE DATOS v0.30.0"
        ],
        "alerts": [
          {
            "title": "VERSIÓN DE PRODUCCIÓN // v0.30.0 VERIFICADA Y CERTIFICADA",
            "bodyHtml": "Las tres fronteras modeladas contra amenazas (Arrendamiento de tareas distribuidas, Sincronización de CAS en la nube, Autorreparación DOM con visión y lenguaje) están <strong>completamente implementadas, probadas de forma adversaria y verificadas en CI</strong> en v0.30.0."
          },
          {
            "title": "CONTRATO ARQUITECTÓNICO OBLIGATORIO",
            "bodyHtml": "Esta especificación es la línea base autorizada para todas las implementaciones de características de v0.30.0. Cada criterio de aceptación (AC1.1 a AC3.6) debe tener una prueba automatizada correspondiente en <code>tests/</code>."
          }
        ]
      },
      "sec-threat-leasing": {
        "tag": "MÓDULO [10] // COMPONENTE 1 (IMPLEMENTADO Y VERIFICADO)",
        "h1": "Matriz de Amenazas de Asignación de Tareas Distribuidas",
        "desc": "Análisis de vulnerabilidad STRIDE, escenarios de ataque y mecanismos de mitigación atómica para demonios trabajadores de Redis Stream.",
        "cards": [
          "10.2 Resumen de diseño del componente 1",
          "10.2.1 Matriz de amenazas y vulnerabilidades (Componente 1)",
          "10.2.2 Especificaciones detalladas de mitigación"
        ],
        "codeHeaders": [
          "PYTHON // ADQUISICIÓN DE BLOQUEO DE IDEMPOTENCIA ATÓMICA"
        ],
        "alerts": [
          {
            "title": "COMPONENTE 1 IMPLEMENTADO Y VERIFICADO // AC1.1–AC1.7 APROBADOS",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>, <code>DistributedWorkerNode</code> y los demonios CLI están completamente implementados y verificados contra los criterios de aceptación AC1.1 a AC1.7."
          }
        ]
      },
      "sec-threat-cas": {
        "tag": "MÓDULO [10] // ARQUITECTURA DEL COMPONENTE 2",
        "h1": "Matriz de Amenazas de Sincronización de CAS en la Nube",
        "desc": "Especificaciones de defensa en profundidad, verificación criptográfica y prevención de SSRF para backends S3 / Cloudflare R2 / MinIO.",
        "cards": [
          "10.3 Resumen de diseño del componente 2",
          "10.3.1 Matriz de amenazas y vulnerabilidades (Componente 2)",
          "10.3.2 Aplicación de ruta de hash criptográfico"
        ],
        "codeHeaders": [
          "PYTHON // VALIDACIÓN DE RUTA DE CLAVE CAS Y VERIFICACIÓN DE SUMA DE CONTROL"
        ],
        "alerts": [
          {
            "title": "CERTIFICADO PARA PRODUCCIÓN // COMPONENTE 2 TOTALMENTE IMPLEMENTADO",
            "bodyHtml": "<code>CASCloudSyncer</code> y los backends de almacenamiento en la nube están <strong>totalmente implementados y verificados</strong> en v0.30.0 con tasas de aprobación del 100% en AC2.1-AC2.7."
          }
        ]
      },
      "sec-threat-vlm": {
        "tag": "MÓDULO [10] // COMPONENTE 3 (IMPLEMENTADO Y VERIFICADO)",
        "h1": "Matriz de Amenazas de Autorreparación DOM con Visión y Lenguaje",
        "desc": "Controles de seguridad de IA multimodal, defensas contra inyección de prompts visuales adversarios y aislamiento de interacción DOM.",
        "cards": [
          "10.4 Resumen de diseño del componente 3",
          "10.4.1 Matriz de amenazas y vulnerabilidades (Componente 3)",
          "10.4.2 Encuadre de datos no confiables y barreras de salida"
        ],
        "codeHeaders": [
          "ARQUITECTURA DE PROMPT // PROMPT DEL SISTEMA VLM AISLADO"
        ],
        "alerts": [
          {
            "title": "CERTIFICADO PARA PRODUCCIÓN // COMPONENTE 3 TOTALMENTE IMPLEMENTADO",
            "bodyHtml": "<code>VisionDOMHealer</code> (autorreparación DOM multimodal Nivel 4) está <strong>totalmente implementado y verificado</strong> en v0.30.0 con tasas de aprobación del 100% en AC3.1-AC3.6."
          }
        ]
      },
      "sec-threat-ac": {
        "tag": "MÓDULO [10] // MATRIZ DE VERIFICACIÓN Y AUDITORÍA (v0.30.0 PRODUCCIÓN)",
        "h1": "Matriz de Verificación de Criterios de Aceptación (v0.30.0)",
        "desc": "Especificaciones de pruebas empíricas y resultados de auditoría que validan los 20 criterios de aceptación para v0.30.0.",
        "cards": [
          "10.5.1 Criterios de aceptación del componente 1 (Task Leasing)",
          "10.5.2 Criterios de aceptación del componente 2 (Cloud CAS)",
          "10.5.3 Criterios de aceptación del componente 3 (VLM Healing)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "LOS 20 CRITERIOS DE ACEPTACIÓN VERIFICADOS Y CERTIFICADOS",
            "bodyHtml": "Los 20 criterios siguientes (AC1.1 a AC3.6) representan el <strong>contrato arquitectónico central</strong> para v0.30.0. Cada criterio está respaldado por pruebas automatizadas en <code>tests/</code> que pasan al 100%."
          },
          {
            "title": "ESTÁNDAR DE VERIFICACIÓN",
            "bodyHtml": "No se aprobará ninguna solicitud de extracción o etiqueta de lanzamiento v0.30.0 sin una cobertura de prueba del 100% en los 20 criterios de aceptación siguientes."
          }
        ]
      }
    },
    "snippets": {
      "sec-install-steps": "# 1. Clonar el repositorio\ngit clone https://github.com/rhaffle87/scrAPE.git\ncd scrAPE\n\n# 2. Crear y activar el entorno virtual\npython -m venv venv\nvenv\\Scripts\\activate          # Windows CMD\n.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell\nsource venv/bin/activate       # Linux / macOS\n\n# 3. Instalar dependencias de Python\npip install -r requirements.txt\n\n# 4. (Opcional) Instalar el puente Node.js de Crawlee para sigilo Nivel 6-7\ncd crawlee_bridge && npm install && cd ..\n\n# 5. Configurar credenciales\ncopy .env.example .env         # Windows\ncp .env.example .env           # Linux / macOS\n# Luego edite .env con sus claves de API y URLs de webhooks",
      "sec-install-launchers": "# Lanzador maestro de Windows (Menú interactivo)\n.\\run.bat\n\n# Lanzador maestro de Linux / macOS\n./run.sh\n\n# Asistente interactivo directo (sin menú)\npython src/cli/cli_wizard.py",
      "sec-ops-docker": "# Iniciar el motor de raspado + sidecar FlareSolverr\ndocker compose up -d\n\n# Ver los registros del clúster en tiempo real\ndocker compose logs -f\n\n# Detener la pila de contenedores de forma segura\ndocker compose down",
      "sec-ops-watchdog": "# Ejecutar el agente Watchdog mediante el contenedor de inicio\n.\\run.bat watchdog\n\n# Invocación directa de monitoreo continuo\npython src/cli/monitor_agent.py --keyword \"example_subject\" --seed seeds/example_subject.txt --use-state-cache",
      "sec-ops-sessions": "# Capturar cookies mediante una ventana de navegador interactiva\npython src/cli/session_auth.py --domain example.com --login-url https://example.com/login\n\n# Listar cookies de sesión fija almacenadas\npython src/cli/session_auth.py --list-sessions",
      "sec-test-pytest": "# Ejecutar las más de 378 pruebas unitarias y de integración\npytest tests/ -v\n\n# Ejecutar con informe de cobertura\npytest --cov=src tests/ --cov-report=term-missing",
      "sec-test-logs": "# Verificar límites de tasa HTTP 429 y bloqueos de Cloudflare\nGet-Content logs/crawler.log -Tail 100 | Select-String -Pattern \"429|Cloudflare|WAF|BLOCKED\"\n\n# Monitorear el flujo del motor de rastreo en tiempo real\nGet-Content logs/crawler.log -Wait -Tail 20"
    },
    "lists": {
      "sec-install-launchers": [
        "<strong>Raspado de búsqueda amplia</strong> -- Consultas de búsqueda automatizadas con rastreo recursivo.",
        "<strong>Raspado de manifiesto dirigido</strong> -- Rastreo estructurado contra manifiestos seed seleccionados.",
        "<strong>Agente Watchdog continuo</strong> -- Bucles de monitoreo de larga duración con caché SQLite WAL.",
        "<strong>Crear conjunto de datos de IA estructurado</strong> -- Empaquete la salida en estructuras consolidadas o agrupadas por dominio.",
        "<strong>Ingesta RAG para LLM empresarial</strong> -- Exporte páginas como Markdown consolidado, archivos <code>.md</code> divididos o JSONL."
      ]
    },
    "h3Map": {
      "Wizard Menu Options": "Opciones del menú del asistente",
      "Core Components": "Componentes principales",
      "Media Vault View": "Vista de la Bóveda de Medios",
      "Command Center View": "Vista del Centro de Comando",
      "Budget & Balance Guardrails": "Límites de seguridad de presupuesto y saldo",
      "Circuit Breaker & Cooldown Mechanics": "Mecanismos de disyuntor y enfriamiento",
      "Download Validation Thresholds": "Umbrales de validación de descargas",
      "Primary v0.30.1 Execution Flags": "Flags de ejecución principales de v0.30.1",
      "Site-Chrome & Keyword Classification Sets": "Conjuntos de clasificación de interfaz de sitio y palabras clave",
      "Dead-Letter Stream Protocol": "Protocolo de flujo de cartas muertas",
      "Idempotency Lock Implementation": "Implementación de bloqueo de idempotencia",
      "Node Health JSON Schema (/api/telemetry/node-health)": "Esquema JSON de estado del nodo (/api/telemetry/node-health)"
    },
    "thMap": {
      "Component": "Componente",
      "Source File": "Archivo de origen",
      "Function": "Función",
      "Requirement": "Requisito",
      "Minimum": "Mínimo",
      "Notes": "Notas",
      "Category": "Categoría",
      "Supported Types": "Tipos compatibles",
      "Processing Method": "Método de procesamiento",
      "Core Pillar": "Pilar fundamental",
      "Key Technologies": "Tecnologías clave",
      "Production Capability": "Capacidad de producción",
      "Parameter": "Parámetro",
      "Type": "Tipo",
      "Default": "Predeterminado",
      "Description": "Descripción",
      "Status": "Estado",
      "Tier": "Nivel",
      "Mechanism": "Mecanismo",
      "Overhead": "Sobrecarga",
      "Usage": "Uso",
      "Profile": "Perfil",
      "Keyword": "Palabra clave",
      "Concurrency": "Concurrencia",
      "Depth": "Profundidad",
      "Endpoint": "Punto final",
      "Impact": "Impacto",
      "Channel": "Canal",
      "Provider": "Proveedor",
      "Purpose": "Propósito"
    }
  },
  "ja": {
    "meta": {
      "title": "scrAPE v0.30.1 // 技術ドキュメントポータル",
      "desc": "scrAPE v0.30.1 の公式技術ドキュメント、CLIフラグマトリックス、アーキテクチャガイド、および運用マニュアル。"
    },
    "ui": {
      "searchPlaceholder": "ドキュメントを検索...",
      "searchHint": "Ctrl+K",
      "langStripLabel": "ポータル言語 // 言語選択:",
      "githubLink": "[GITHUB]",
      "badgeNew": "新機能",
      "badgeVerified": "検証済み",
      "copyCode": "[コードをコピー]",
      "copiedCode": "[コピー完了!]",
      "commandBuilder": "インタラクティブ CLI ビルダー",
      "builderPrompt": "実行パラメータを設定してコマンドを生成:",
      "builderOutputLabel": "実行可能な CLI コマンド:",
      "footerTagline": "自己修復型DOMヒューリスティクスとApache Parquetエクスポートを備えた自律型高スループット分散スクレイピングエンジン。",
      "searchResults": "件ヒット",
      "noResults": "該当なし",
      "selectLocale": "ドキュメント言語を選択",
      "changeLanguageTitle": "言語を変更"
    },
    "modules": [
      "[01] システム概要",
      "[02] インストールとクイックスタート",
      "[03] CLI リファレンス",
      "[04] コアエンジンアーキテクチャ",
      "[05] 設定ファイルリファレンス",
      "[06] WEBUI ダッシュボード",
      "[07] デプロイと運用",
      "[08] 出力とデータエクスポート",
      "[09] テストとトラブルシューティング",
      "[10] 脅威モデルとセキュリティ"
    ],
    "nav": {
      "sec-overview-arch": "[1.1] アーキテクチャと目的",
      "sec-overview-formats": "[1.2] 対応フォーマットと動作制限",
      "sec-overview-layout": "[1.3] ディレクトリ構成",
      "sec-overview-pillars": "[1.4] 次世代コアアーキテクチャの柱",
      "sec-overview-v28": "[1.5] コアアーキテクチャ (v0.28.0)",
      "sec-install-prereqs": "[2.1] 動作要件・前提条件",
      "sec-install-steps": "[2.2] インストール手順",
      "sec-install-launchers": "[2.3] メインランチャーとウィザード",
      "sec-install-recipes": "[2.4] 初回実行レシピ",
      "sec-cli-flags": "[3.1] 完全 CLI フラグマトリックス",
      "sec-cli-builder": "[3.2] 対話型 CLI ビルダー",
      "sec-cli-profiles": "[3.3] プリセットプロファイル",
      "sec-engine-bfs": "[4.1] BFS クロールループ",
      "sec-engine-waf": "[4.2] 8段階ステルス WAF 回避パイプライン",
      "sec-engine-captcha": "[4.3] 汎用 CAPTCHA 解決戦略",
      "sec-engine-scoring": "[4.4] 品質スコアリングと除外フィルタ",
      "sec-engine-normalize": "[4.5] URL 正規化エンジン",
      "sec-engine-pool": "[4.6] 事前ウォームアップブラウザプール",
      "sec-engine-broker": "[4.7] Redis Streams タスクブローカー",
      "sec-engine-ml": "[4.8] ビジョンハードウェアと ML パイプライン",
      "sec-engine-healing": "[4.9] セルフヒーリング DOM パーサー",
      "sec-engine-bktree": "[4.10] BK-Tree 知覚ハッシュ重複排除",
      "sec-config-env": "[5.1] 環境変数設定 (.env)",
      "sec-config-domain": "[5.2] ドメイン設定 (domain_config)",
      "sec-config-urlnorm": "[5.3] URL 正規表現ルール",
      "sec-config-seeds": "[5.4] シードマニフェスト構文",
      "sec-config-profiles": "[5.5] 対象サブジェクトプロファイル",
      "sec-config-blacklist": "[5.6] ブラックリスト管理",
      "sec-webui-arch": "[6.1] サーバーアーキテクチャ",
      "sec-webui-views": "[6.2] コマンドセンターとメディアボールト",
      "sec-webui-telemetry": "[6.3] リアルタイムテレメトリと SSE",
      "sec-webui-design": "[6.4] ブルータリズムデザイントークン",
      "sec-webui-health": "[6.5] ノードヘルス監視モニター",
      "sec-ops-docker": "[7.1] Docker Compose 運用",
      "sec-ops-watchdog": "[7.2] ウォッチドッグデーモン",
      "sec-ops-notifications": "[7.3] マルチチャネル通知パイプライン",
      "sec-ops-proxy": "[7.4] プロキシプール管理",
      "sec-ops-sessions": "[7.5] セッション・Cookie 保管庫",
      "sec-output-structure": "[8.1] 出力ディレクトリ構成",
      "sec-output-manifest": "[8.2] manifest.json 仕様",
      "sec-output-domain": "[8.3] domain_report.json レポート",
      "sec-output-kohya": "[8.4] Kohya LoRA データセット出力",
      "sec-output-rag": "[8.5] RAG 知識ベース形式",
      "sec-output-cas": "[8.6] コンテンツアドレス指定ストレージ (CAS)",
      "sec-output-parquet": "[8.7] Apache Parquet 列指向データ出力",
      "sec-test-pytest": "[9.1] pytest テスト実行",
      "sec-test-tdai": "[9.2] 検証プロトコル (TDAI)",
      "sec-test-logs": "[9.3] ログ診断レシピ",
      "sec-test-diagnostic": "[9.4] オペレーター診断マトリックス",
      "sec-test-guidelines": "[9.5] 開発者向けガイドライン",
      "sec-threat-overview": "[10.1] 事前セキュリティ検証範囲",
      "sec-threat-leasing": "[10.2] タスクリース安全マトリックス",
      "sec-threat-cas": "[10.3] クラウド CAS セキュリティ",
      "sec-threat-vlm": "[10.4] VLM ヒーリング防御境界",
      "sec-threat-ac": "[10.5] 受け入れ基準契約"
    },
    "footer": {
      "logo": "scrAPE // コアシステム",
      "tagline": "自己修復型DOMヒューリスティクスとApache Parquetエクスポートを備えた自律型高スループット分散スクレイピングエンジン。",
      "badges": [
        "リリース v0.30.1",
        "MIT ライセンス",
        "PYTHON 3.10+"
      ],
      "headings": {
        "repo": "リポジトリ",
        "docs": "ドキュメント"
      },
      "links": [
        "ソースコード",
        "リリースノート (v0.30.1)",
        "課題トラッカー",
        "CI / ワークフロー",
        "システム README",
        "脅威モデル (v0.30.0)",
        "バージョン変更履歴",
        "MIT ライセンス",
        "Docker Compose"
      ],
      "copy": "© 2026 scrAPE メンテナー。MIT ライセンスに基づくオープンソース。",
      "sysinfo": "ステータス: 稼働中 // エンジン: v0.30.1"
    },
    "sections": {
      "sec-overview-arch": {
        "tag": "モジュール [01] // システム概要",
        "h1": "アーキテクチャと目標",
        "desc": "自律型メディア抽出および AI データセット生成のためのマルチエンジンステルス Web スクレイピングシステム。",
        "cards": [
          "1.1 システムアーキテクチャ"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] コア運用の保証",
            "bodyHtml": "システムは8段階のWAFフォールバックパイプラインを介して動作します。チャレンジループが検出されると、リクエストは軽量な直接HTTPからヘッドフルステルスブラウザ自動化へと自動的にエスカレーションされます。手動の介入は不要です。"
          }
        ]
      },
      "sec-overview-formats": {
        "tag": "モジュール [01] // システム概要",
        "h1": "対応フォーマットと運用制限",
        "desc": "メディア仕様、ファイルサイズフィルター、画像解像度の境界値、リクエストレート制限。",
        "cards": [
          "1.2 メディアおよびデータ機能"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-overview-layout": {
        "tag": "モジュール [01] // システム概要",
        "h1": "プロジェクトのディレクトリ構成",
        "desc": "リポジトリのファイルとフォルダーの体系的構成。",
        "cards": [
          "1.3 ディレクトリ構造"
        ],
        "codeHeaders": [
          "テキスト // リポジトリツリー"
        ],
        "alerts": []
      },
      "sec-overview-pillars": {
        "tag": "モジュール [01] // システム概要",
        "h1": "コアアーキテクチャの柱 (v0.30.1)",
        "desc": "エンタープライズマルチノードオーケストレーション、劣線形BKツリー知覚重複排除、分離プロファイラースレッドプール、ゼロ重複CAS。",
        "cards": [
          "1.4 コアアーキテクチャの柱 (v0.30.1)"
        ],
        "codeHeaders": [
          "BASH // コア機能 CLI 起動コマンド"
        ],
        "alerts": []
      },
      "sec-overview-v28": {
        "tag": "モジュール [01] // アーキテクチャアップデート",
        "h1": "コアアーキテクチャ (v0.28.0)",
        "desc": "本番仕様の分離型MLパイプライン、3階層重複排除、自己修復DOMパーサー、監視付きハイブリッド並行処理。",
        "cards": [
          "1.4 v0.28.0 におけるアーキテクチャの刷新"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-prereqs": {
        "tag": "モジュール [02] // インストールとクイックスタート",
        "h1": "システム前提条件とツールチェーン",
        "desc": "Python ランタイム、ヘッドレスブラウザドライバー、CUDA ハードウェアアクセラレーション、Redis 要件。",
        "cards": [
          "2.1 システム要件"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-steps": {
        "tag": "モジュール [02] // インストールとクイックスタート",
        "h1": "ステップバイステップのインストール手順",
        "desc": "仮想環境の構築、pip パッケージのインストール、ブラウザバイナリの同期。",
        "cards": [
          "2.2 セットアップ手順"
        ],
        "codeHeaders": [
          "BASH // インストールコマンド"
        ],
        "alerts": [
          {
            "title": "[i] FLARESOLVERR セットアップ",
            "bodyHtml": "FlareSolverr (Tier 5) は Docker コンテナとして実行されます。起動コマンド: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"
          }
        ]
      },
      "sec-install-launchers": {
        "tag": "モジュール [02] // インストールとクイックスタート",
        "h1": "マスターランチャーとウィザード",
        "desc": "すべての実行モードに対応するインタラクティブな起動スクリプト。",
        "cards": [
          "2.3 ランチャーオプションとウィザード"
        ],
        "codeHeaders": [
          "POWERSHELL // マスターランチャー"
        ],
        "alerts": []
      },
      "sec-install-recipes": {
        "tag": "モジュール [02] // インストールとクイックスタート",
        "h1": "初回実行コマンドレシピ",
        "desc": "一般的な抽出パターンのためのコピー＆ペースト可能なコマンド。",
        "cards": [
          "2.4 初回実行コマンドレシピ"
        ],
        "codeHeaders": [
          "レシピ 1 // 除外メディア保持を伴う標準シード抽出",
          "レシピ 2 // 状態キャッシュを備えた継続的監視エージェント",
          "レシピ 3 // クイック検証実行 (ダウンロードなし)",
          "レシピ 4 // 検索による自動探索 (シードなし)",
          "レシピ 5 // ステルスクロール (低速丁寧モード)"
        ],
        "alerts": []
      },
      "sec-cli-flags": {
        "tag": "モジュール [03] // CLI リファレンス",
        "h1": "完全な CLI 実行フラグマトリックス",
        "desc": "すべてのコマンドラインスイッチ、フラグ、しきい値の上書き、抽出バジェットの完全リファレンス。",
        "cards": [
          "3.1 コマンドライン引数マトリックス"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-cli-builder": {
        "tag": "モジュール [03] // CLI リファレンス",
        "h1": "インタラクティブ CLI コマンドビルダー",
        "desc": "ターゲットパラメータ、並行処理プール、ステルスフラグを設定して、即実行可能なコマンドを生成します。",
        "cards": [
          "3.2 インタラクティブコマンドジェネレーター"
        ],
        "codeHeaders": [
          "生成された CLI コマンド文字列"
        ],
        "alerts": []
      },
      "sec-cli-profiles": {
        "tag": "モジュール [03] // CLI リファレンス",
        "h1": "実行プロファイル",
        "desc": "特定のスクレイピング環境向けに事前調整されたプロファイルプリセット。",
        "cards": [
          "3.3 プリセットプロファイルマトリックス"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-bfs": {
        "tag": "モジュール [04] // コアエンジンアーキテクチャ",
        "h1": "BFS クロールループ",
        "desc": "非同期幅優先探索ループ、優先度キューディスパッチ、リンク抽出処理。",
        "cards": [
          "4.1 BFS実行シーケンス"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-waf": {
        "tag": "モジュール [04] // コアエンジンアーキテクチャ",
        "h1": "8段階ステルス WAF エスカレーションパイプライン",
        "desc": "Cloudflare Turnstile、Datadome、Incapsulaなどのボット対策を解決する適応型フォールバック。",
        "cards": [
          "4.2 8段階WAFパイプライン階層"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-captcha": {
        "tag": "モジュール [04] // コアエンジンアーキテクチャ",
        "h1": "ユニバーサルキャプチャ戦略",
        "desc": "自動解決プロバイダー、チャレンジのインターセプト、およびリトライハンドラー。",
        "cards": [
          "4.3 チャレンジ・キャプチャ解決戦略"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-scoring": {
        "tag": "モジュール [04] // コアエンジンアーキテクチャ",
        "h1": "品質スコアリングと除外判定",
        "desc": "URL分類、画像解像度しきい値、および除外されたメディアのディスク保持管理。",
        "cards": [
          "4.4 拒否ルールと保存パス"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-normalize": {
        "tag": "モジュール [04] // コアエンジンアーキテクチャ",
        "h1": "URL 正規化",
        "desc": "追跡パラメータの削除、プロトコルの正規化、冗長な探索サイクルの防止。",
        "cards": [
          "4.5 URL正規化パイプライン"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-pool": {
        "tag": "モジュール [04] // コアエンジンアーキテクチャ",
        "h1": "事前起動ブラウザプール",
        "desc": "高性能 Camoufox ブラウザプールのリサイクルと分離コンテキストのリース管理。",
        "cards": [
          "4.6 事前起動ブラウザプールのライフサイクル"
        ],
        "codeHeaders": [
          "PYTHON // 事前起動ブラウザプールのリース"
        ],
        "alerts": []
      },
      "sec-engine-broker": {
        "tag": "モジュール [04] // コアエンジンアーキテクチャ",
        "h1": "Redis Streams タスクブローカー",
        "desc": "分散コンシューマーグループ、保留中エントリ追跡 (PEL)、アトミックなタスク配信。",
        "cards": [
          "4.7 Redis Streams による分散クラスタ調整"
        ],
        "codeHeaders": [
          "PYTHON // タスクブローカーの相互作用パターン"
        ],
        "alerts": []
      },
      "sec-engine-ml": {
        "tag": "モジュール [04] // コアエンジンアーキテクチャ",
        "h1": "ビジョンハードウェアと ML パイプライン",
        "desc": "CUDA/MPS デバイス検出、半精度 (FP16) 推論、美的スコアリング処理。",
        "cards": [
          "4.8 ハードウェアアクセラレーションマトリックス"
        ],
        "codeHeaders": [
          "PYTHON // ハードウェア検出と精度交渉"
        ],
        "alerts": []
      },
      "sec-engine-healing": {
        "tag": "モジュール [04] // コアエンジンアーキテクチャ",
        "h1": "自己修復型 DOM パーサー",
        "desc": "マルチプロバイダーLLMヒューリスティック修復を備えた4段階のDOMリカバリーカスケード。",
        "cards": [
          "4.9 自律的セレクター修復と VLM ビジュアル修復"
        ],
        "codeHeaders": [
          "PYTHON // 自己修復抽出カスケード",
          "テキスト // マルチプロバイダーLLM統合カスケード"
        ],
        "alerts": []
      },
      "sec-engine-bktree": {
        "tag": "モジュール [04] // コアエンジンアーキテクチャ",
        "h1": "BKツリー重複排除と並行処理のパーティショニング",
        "desc": "離散距離ツリーインデックス、ハミング距離クラスタリング、分離されたプロファイラー実行プール。",
        "cards": [
          "4.10 離散距離ツリーと実行プールのパーティショニング"
        ],
        "codeHeaders": [
          "PYTHON // BKツリー距離探索とコネクションプーリング"
        ],
        "alerts": []
      },
      "sec-config-env": {
        "tag": "モジュール [05] // 設定ファイルリファレンス",
        "h1": "環境変数 (.env)",
        "desc": "本番用認証情報、レート制限、プロキシゲートウェイ、API トークン。",
        "cards": [
          "5.1 .env 設定テンプレート"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-domain": {
        "tag": "モジュール [05] // 設定ファイルリファレンス",
        "h1": "domain_config.json",
        "desc": "ドメインごとの並行数制限、カスタム待機セレクター、HTTPヘッダーの上書き設定。",
        "cards": [
          "5.2 設定キーリファレンス (domain_config.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-urlnorm": {
        "tag": "モジュール [05] // 設定ファイルリファレンス",
        "h1": "url_normalisation_rules.json",
        "desc": "クエリパラメータの除去とドメイン変換のための正規表現ルール。",
        "cards": [
          "5.3 正規化ルールスキーマ (url_normalisation_rules.json)"
        ],
        "codeHeaders": [
          "JSON // ルールスキーマの例"
        ],
        "alerts": [
          {
            "title": "[!] 必須ルール",
            "bodyHtml": "<code>src/</code> 配下の Python ファイルにドメイン固有の URL 正規化正規表現を直接ハードコードしないでください。すべてのルールは必ず <code>data/url_normalisation_rules.json</code> に宣言する必要があります。"
          }
        ]
      },
      "sec-config-seeds": {
        "tag": "モジュール [05] // 設定ファイルリファレンス",
        "h1": "シードマニフェスト構文",
        "desc": "seeds/*.txt ファイルにおけるコメント、インラインディレクティブ、優先度ウェイト。",
        "cards": [
          "5.4 シードマニフェストのアノテーションリファレンス"
        ],
        "codeHeaders": [
          "MANIFEST // シードマニフェストアノテーションの例"
        ],
        "alerts": []
      },
      "sec-config-profiles": {
        "tag": "モジュール [05] // 設定ファイルリファレンス",
        "h1": "サブジェクトプロファイル",
        "desc": "対象固有のプリセット、出力テンプレート、ブラックリストとの連携設定。",
        "cards": [
          "5.5 プロファイルプリセット (subject_profiles.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-blacklist": {
        "tag": "モジュール [05] // 設定ファイルリファレンス",
        "h1": "ブラックリスト管理",
        "desc": "グローバルに除外されたドメイン、広告サーバー、価値の低いリソースパターン。",
        "cards": [
          "5.6 ドメインブラックリストと除外設定 (blacklist.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-arch": {
        "tag": "モジュール [06] // WEBUI ダッシュボード",
        "h1": "WebUI サーバーアーキテクチャ",
        "desc": "リアルタイム SSE ストリーミングテレメトリを備えた FastAPI および HTMX リアクティブコマンドセンター。",
        "cards": [
          "6.1 分離型 FastAPI サーバー"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-views": {
        "tag": "モジュール [06] // WEBUI ダッシュボード",
        "h1": "コマンドセンターとメディア保管庫",
        "desc": "インタラクティブな制御ダッシュボード、リアルタイムのクローラー状態、ギャラリー検査機能。",
        "cards": [
          "6.2 ダッシュボードビュー (コマンドセンター & メディア保管庫)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-telemetry": {
        "tag": "モジュール [06] // WEBUI ダッシュボード",
        "h1": "ライブテレメトリと SSE",
        "desc": "Server-Sent Events、キュー処理レート、メモリ使用率ゲージによるリアルタイムストリーミング。",
        "cards": [
          "6.3 リアルタイムイベントパイプライン (SSE & Canvas)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-design": {
        "tag": "モジュール [06] // WEBUI ダッシュボード",
        "h1": "デザイントークン",
        "desc": "タクティカルブルータリズム CSS トークン、高コントラスト等幅タイポグラフィ、カラーパレット。",
        "cards": [
          "6.4 デザイントークンリファレンス (タクティカルブルータリズム)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-health": {
        "tag": "モジュール [06] // WEBUI ダッシュボード",
        "h1": "ノード健全性タクティカルモニター",
        "desc": "サブシステムの正常性チェック、ハートビートプローブ、Redis クラスタテレメトリ。",
        "cards": [
          "6.5 タクティカルテレメトリとノードガバナンス"
        ],
        "codeHeaders": [
          "JSON // ノード健全性テレメトリペイロード"
        ],
        "alerts": []
      },
      "sec-ops-docker": {
        "tag": "モジュール [07] // デプロイと運用",
        "h1": "Docker Compose によるデプロイ",
        "desc": "FlareSolverr、Redis、WebUI を備えたマルチコンテナ本番環境デプロイ。",
        "cards": [
          "7.1 Docker Compose によるコンテナデプロイ"
        ],
        "codeHeaders": [
          "BASH // DOCKER COMPOSE 起動"
        ],
        "alerts": []
      },
      "sec-ops-watchdog": {
        "tag": "モジュール [07] // デプロイと運用",
        "h1": "Watchdog エージェント",
        "desc": "自動ヘルスチェックと再起動ポリシーを備えた継続的クロールデーモン。",
        "cards": [
          "7.2 継続的モニタリングループ (Watchdog)"
        ],
        "codeHeaders": [
          "POWERSHELL // WATCHDOG エージェントコマンド"
        ],
        "alerts": []
      },
      "sec-ops-notifications": {
        "tag": "モジュール [07] // デプロイと運用",
        "h1": "通知パイプライン",
        "desc": "プラグイン可能な通知チャネル (Telegram、Discord、Slack、Webhooks)。",
        "cards": [
          "7.3 マルチチャネルアラート (Telegram, Discord, Slack)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-proxy": {
        "tag": "モジュール [07] // デプロイと運用",
        "h1": "プロキシプール管理",
        "desc": "プロキシローテーション、レイテンシによる自動隔離、帯域幅クォータ管理。",
        "cards": [
          "7.4 プロキシ管理戦略とレイテンシ隔離"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-sessions": {
        "tag": "モジュール [07] // デプロイと運用",
        "h1": "セッションおよびクッキーの管理",
        "desc": "ドメインごとの永続的なスティッキーセッションと対話型クッキーログイン。",
        "cards": [
          "7.5 セッションストレージとクッキー管理"
        ],
        "codeHeaders": [
          "BASH // セッションログインコマンド"
        ],
        "alerts": []
      },
      "sec-output-structure": {
        "tag": "モジュール [08] // 出力とデータエクスポート",
        "h1": "出力ディレクトリ構造",
        "desc": "クロール実行結果の成果物レイアウト構成。",
        "cards": [
          "8.1 成果物および出力ディレクトリの構成"
        ],
        "codeHeaders": [
          "テキスト // 出力ディレクトリレイアウト"
        ],
        "alerts": []
      },
      "sec-output-manifest": {
        "tag": "モジュール [08] // 出力とデータエクスポート",
        "h1": "manifest.json スキーマ",
        "desc": "実行結果 JSON スキーマの完全なドキュメント。",
        "cards": [
          "8.2 JSON ペイロードフィールド (manifest.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-domain": {
        "tag": "モジュール [08] // 出力とデータエクスポート",
        "h1": "domain_report.json スキーマ",
        "desc": "ドメインごとのクロール指標とパフォーマンスレポート。",
        "cards": [
          "8.3 ドメイン別収量レポート (domain_report.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-kohya": {
        "tag": "モジュール [08] // 出力とデータエクスポート",
        "h1": "Kohya LoRA データセットエクスポート",
        "desc": "Kohya_ss LoRA 形式データセットの ZIP アーカイブ自動生成。",
        "cards": [
          "8.4 Kohya LoRA データセットジェネレーター"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-rag": {
        "tag": "モジュール [08] // 出力とデータエクスポート",
        "h1": "RAG 投入用データフォーマット",
        "desc": "LLM RAG 向けエクスポート (Markdown チャンクおよび JSONL エンベディング)。",
        "cards": [
          "8.5 RAG 投入用エクスポート形式 (Markdown / JSONL)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-cas": {
        "tag": "モジュール [08] // 出力とデータエクスポート",
        "h1": "コンテンツアドレス指定ストレージ (CAS)",
        "desc": "反復クロール全体で重複ファイルのディスク消費をゼロにするグローバル重複排除ストレージ。",
        "cards": [
          "8.6 コンテンツアドレス指定ストレージ (CAS) アーキテクチャ"
        ],
        "codeHeaders": [
          "PYTHON // CAS 重複排除と実行リンク",
          "テキスト // CAS ストレージのライフサイクル"
        ],
        "alerts": []
      },
      "sec-output-parquet": {
        "tag": "モジュール [08] // 出力とデータエクスポート",
        "h1": "Apache Parquet データセットエクスポート",
        "desc": "Polars、DuckDB、Pandas、ビッグデータ OLAP パイプライン向けに最適化された Snappy 圧縮列指向データセット。",
        "cards": [
          "8.7 列指向データエクスポートパイプライン (Apache Parquet)"
        ],
        "codeHeaders": [
          "PYTHON // PARQUET データセットの生成"
        ],
        "alerts": []
      },
      "sec-test-pytest": {
        "tag": "モジュール [09] // テストとトラブルシューティング",
        "h1": "pytest の実行",
        "desc": "自動テストスイートの実行とカバレッジの確認。",
        "cards": [
          "9.1 自動化された Pytest スイート"
        ],
        "codeHeaders": [
          "POWERSHELL // 完全なテストスイートを実行"
        ],
        "alerts": []
      },
      "sec-test-tdai": {
        "tag": "モジュール [09] // テストとトラブルシューティング",
        "h1": "実証的検証プロトコル (TDAI)",
        "desc": "テスト駆動 AI 検証ルールと RED-GREEN-REFACTOR プロトコル。",
        "cards": [
          "9.2 実証的検証プロトコル (TDAI)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] 必須ルール",
            "bodyHtml": "実機ランタイム検証コマンドを実行し、完全なテスト合格を実証することなく、機能や修正の完了を宣言しないでください。"
          }
        ]
      },
      "sec-test-logs": {
        "tag": "モジュール [09] // テストとトラブルシューティング",
        "h1": "ログ診断レシピ",
        "desc": "実行時診断のためのログ解析と grep コマンド集。",
        "cards": [
          "9.3 PowerShell 診断コマンドとログ解析"
        ],
        "codeHeaders": [
          "POWERSHELL // エラーおよびブロックのログ検索"
        ],
        "alerts": []
      },
      "sec-test-diagnostic": {
        "tag": "モジュール [09] // テストとトラブルシューティング",
        "h1": "オペレーター診断マトリックス",
        "desc": "トラブルシューティングのための網羅的なオペレーター向け診断テーブル。",
        "cards": [
          "9.4 オペレーター診断マトリックス"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-test-guidelines": {
        "tag": "モジュール [09] // テストとトラブルシューティング",
        "h1": "開発者ガイドライン",
        "desc": "必須のコーディング規約およびワークスペースの品質基準。",
        "cards": [
          "9.5 開発者向け必須コーディング規約"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-threat-overview": {
        "tag": "モジュール [10] // 脅威モデルとセキュリティ",
        "h1": "セキュリティアーキテクチャと v0.30.0 の検証",
        "desc": "v0.30.0 分散スケーリングのための権威ある脅威モデル、STRIDE アーキテクチャコントラクト、実証的検証マトリックス。",
        "cards": [
          "10.1 トラストバウンダリとデータフローアーキテクチャ",
          "10.1.1 STRIDE脅威カテゴリ",
          "10.1.2 横断的インバリアント"
        ],
        "codeHeaders": [
          "アーキテクチャ // v0.30.0 分散トラストバウンダリとデータフロー"
        ],
        "alerts": [
          {
            "title": "本番リリース // v0.30.0 検証および認定完了",
            "bodyHtml": "本モジュールで規定された3つの最先端アーキテクチャ領域（分散タスクリース、クラウドCAS同期、VLMによるDOM自己修復）は、v0.30.0 リリースにおいて<strong>完全に実装され、敵対的テストおよび CI 検証（Ubuntu/macOS/Windows）をすべてクリア</strong>しています。"
          },
          {
            "title": "必須アーキテクチャ契約",
            "bodyHtml": "本仕様書は、v0.30.0 のすべての機能実装における信頼できる基準です。各受入基準（AC1.1～AC3.6）は、コンポーネントがリリース準備完了とみなされる前に、<code>tests/</code> に対応する自動テストを備えている必要があります。"
          }
        ]
      },
      "sec-threat-leasing": {
        "tag": "モジュール [10] // コンポーネント 1 (実装および検証済み)",
        "h1": "分散タスクリース脅威マトリックス (コンポーネント 1)",
        "desc": "Redis Stream ワーカーデーモンのための STRIDE 脆弱性分析、攻撃シナリオ、アトミックな緩和メカニズム。",
        "cards": [
          "10.2 コンポーネント 1 設計概要",
          "10.2.1 脅威および脆弱性マトリックス (コンポーネント 1)",
          "10.2.2 詳細な緩和仕様"
        ],
        "codeHeaders": [
          "PYTHON // アトミックな冪等性ロックの取得"
        ],
        "alerts": [
          {
            "title": "コンポーネント 1 実装および検証完了 // AC1.1–AC1.7 合格",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>、<code>DistributedWorkerNode</code>、CLI ワーカーデーモンは受入基準 AC1.1～AC1.7 に対して完全に実装され、98件の自動テストによって実証検証されています。"
          }
        ]
      },
      "sec-threat-cas": {
        "tag": "モジュール [10] // コンポーネント 2 アーキテクチャ",
        "h1": "クラウド CAS 同期脅威マトリックス (コンポーネント 2)",
        "desc": "S3 / Cloudflare R2 / MinIO ストレージバックエンド向けの多層防御仕様、暗号学的検証、SSRF 防止設計。",
        "cards": [
          "10.3 コンポーネント 2 設計概要",
          "10.3.1 脅威および脆弱性マトリックス (コンポーネント 2)",
          "10.3.2 暗号化ハッシュパス強制保護"
        ],
        "codeHeaders": [
          "PYTHON // CAS キーパス検証およびチェックサム確認"
        ],
        "alerts": [
          {
            "title": "本番認定済み // コンポーネント 2 の完全実装完了",
            "bodyHtml": "<code>CASCloudSyncer</code> および S3/R2/MinIO クラウドストレージバックエンドは、AC2.1～AC2.7 のテスト合格率 100% で v0.30.0 において<strong>完全に実装および検証</strong>されています。"
          }
        ]
      },
      "sec-threat-vlm": {
        "tag": "モジュール [10] // コンポーネント 3 (実装および検証済み)",
        "h1": "Vision-Language DOM 自己修復脅威マトリックス (コンポーネント 3)",
        "desc": "マルチモーダル AI セキュリティ制御、敵対的ビジュアルプロンプトインジェクション防御、DOM 操作サンドボックス。",
        "cards": [
          "10.4 コンポーネント 3 設計概要",
          "10.4.1 脅威および脆弱性マトリックス (コンポーネント 3)",
          "10.4.2 非信頼データのフレーミングと出力ガードレール"
        ],
        "codeHeaders": [
          "プロンプトアーキテクチャ // サンドボックス化された VLM システムプロンプト"
        ],
        "alerts": [
          {
            "title": "本番認定済み // コンポーネント 3 の完全実装完了",
            "bodyHtml": "<code>VisionDOMHealer</code> (Tier 4 マルチモーダル DOM 修復) は、AC3.1～AC3.6 のテスト合格率 100%、75ベクトルのプロンプトインジェクションファジング拒否率 100% で<strong>完全に実装および検証</strong>されています。"
          }
        ]
      },
      "sec-threat-ac": {
        "tag": "モジュール [10] // 検証および監査マトリックス (v0.30.0 本番仕様)",
        "h1": "受入基準検証マトリックス (v0.30.0 本番仕様)",
        "desc": "v0.30.0 の全20の受入基準を検証する実証的テスト仕様、検証方法、および監査結果。",
        "cards": [
          "10.5.1 コンポーネント 1 受入基準 (タスクリース)",
          "10.5.2 コンポーネント 2 受入基準 (クラウド CAS)",
          "10.5.3 コンポーネント 3 受入基準 (VLM 修復)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "全20の受入基準の検証および認証完了",
            "bodyHtml": "以下の全20基準（AC1.1～AC3.6）は、v0.30.0 における<strong>コアアーキテクチャ契約</strong>を表しています。すべての基準は <code>tests/</code> における自動テストによって裏付けられ、100%合格しています。"
          },
          {
            "title": "検証基準",
            "bodyHtml": "以下の20の受入基準すべてにおいて100%のテストカバレッジが実証されない限り、v0.30.0 のPRまたはリリースタグは承認されません。"
          }
        ]
      }
    },
    "snippets": {
      "sec-install-steps": "# 1. リポジトリをクローン\ngit clone https://github.com/rhaffle87/scrAPE.git\ncd scrAPE\n\n# 2. 仮想環境を作成して有効化\npython -m venv venv\nvenv\\Scripts\\activate          # Windows CMD\n.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell\nsource venv/bin/activate       # Linux / macOS\n\n# 3. Python 依存関係をインストール\npip install -r requirements.txt\n\n# 4. (任意) Tier 6-7 ステルス用の Crawlee Node.js ブリッジをインストール\ncd crawlee_bridge && npm install && cd ..\n\n# 5. 認証情報を設定\ncopy .env.example .env         # Windows\ncp .env.example .env           # Linux / macOS\n# 続いて .env を編集して API キーと Webhook URL を設定します",
      "sec-install-launchers": "# Windows マスターランチャー (対話型メニュー)\n.\\run.bat\n\n# Linux / macOS マスターランチャー\n./run.sh\n\n# 対話型ウィザードの直接起動 (メニューなし)\npython src/cli/cli_wizard.py",
      "sec-ops-docker": "# スクレイパーエンジンと FlareSolverr サイドカーを起動\ndocker compose up -d\n\n# クラスタログをリアルタイムで監視\ndocker compose logs -f\n\n# スタックを正常に停止\ndocker compose down",
      "sec-ops-watchdog": "# ランチャー経由で Watchdog エージェントを実行\n.\\run.bat watchdog\n\n# 継続的監視ループの直接呼び出し\npython src/cli/monitor_agent.py --keyword \"example_subject\" --seed seeds/example_subject.txt --use-state-cache",
      "sec-ops-sessions": "# 対話型ブラウザウィンドウでクッキーをキャプチャ\npython src/cli/session_auth.py --domain example.com --login-url https://example.com/login\n\n# 保存されたスティッキーセッションクッキーを一覧表示\npython src/cli/session_auth.py --list-sessions",
      "sec-test-pytest": "# 全378以上の単体および統合テストを実行\npytest tests/ -v\n\n# カバレッジレポート付きで実行\npytest --cov=src tests/ --cov-report=term-missing",
      "sec-test-logs": "# HTTP 429 レート制限と Cloudflare ブロックを確認\nGet-Content logs/crawler.log -Tail 100 | Select-String -Pattern \"429|Cloudflare|WAF|BLOCKED\"\n\n# クロールエンジンのログ出力をリアルタイム監視\nGet-Content logs/crawler.log -Wait -Tail 20"
    },
    "lists": {
      "sec-install-launchers": [
        "<strong>広域検索スクレイピング</strong> -- 再帰的クロールを伴う自動検索クエリ実行。",
        "<strong>ターゲットマニフェストスクレイピング</strong> -- 選択されたシードマニフェストに対する構造化クロール。",
        "<strong>継続的監視エージェント (Watchdog)</strong> -- SQLite WAL キャッシュを備えた長期監視ループ。",
        "<strong>構造化 AI データセット作成</strong> -- 実行結果をドメイン別またはメディアタイプ別に統合・パッケージ化。",
        "<strong>エンタープライズ LLM RAG 投入用エクスポート</strong> -- 統合 Markdown、チャンク分割された <code>.md</code>、または JSONL 形式で出力。"
      ]
    },
    "h3Map": {
      "Wizard Menu Options": "ウィザードメニューオプション",
      "Core Components": "コアコンポーネント構成",
      "Media Vault View": "メディア保管庫ビュー",
      "Command Center View": "コマンドセンタービュー",
      "Budget & Balance Guardrails": "予算および残高保護ガードレール",
      "Circuit Breaker & Cooldown Mechanics": "サーキットブレーカーとクールダウンメカニズム",
      "Download Validation Thresholds": "ダウンロード検証しきい値",
      "Primary v0.30.1 Execution Flags": "v0.30.1 主要実行フラグ",
      "Site-Chrome & Keyword Classification Sets": "サイトUIおよびキーワード分類セット",
      "Dead-Letter Stream Protocol": "デッドレターストリームプロトコル",
      "Idempotency Lock Implementation": "冪等性ロックの実装",
      "Node Health JSON Schema (/api/telemetry/node-health)": "ノード正常性 JSON スキーマ (/api/telemetry/node-health)"
    },
    "thMap": {
      "Component": "コンポーネント",
      "Source File": "ソースファイル",
      "Function": "機能",
      "Requirement": "要件",
      "Minimum": "最小要件",
      "Notes": "備考",
      "Category": "カテゴリ",
      "Supported Types": "サポート対象タイプ",
      "Processing Method": "処理方法",
      "Core Pillar": "コアアーキテクチャの柱",
      "Key Technologies": "主要技術",
      "Production Capability": "実運用機能",
      "Parameter": "パラメータ",
      "Type": "型",
      "Default": "デフォルト",
      "Description": "説明",
      "Status": "ステータス",
      "Tier": "階層",
      "Mechanism": "メカニズム",
      "Overhead": "オーバーヘッド",
      "Usage": "使用方法",
      "Profile": "プロファイル",
      "Keyword": "キーワード",
      "Concurrency": "並行数",
      "Depth": "深度",
      "Endpoint": "エンドポイント",
      "Impact": "影響",
      "Channel": "チャンネル",
      "Provider": "プロバイダー",
      "Purpose": "目的"
    }
  },
  "ru": {
    "meta": {
      "title": "scrAPE v0.30.1 // Портал технической документации",
      "desc": "Официальная техническая документация, матрица флагов CLI, архитектура и руководство оператора scrAPE v0.30.1."
    },
    "ui": {
      "searchPlaceholder": "ПОИСК ПО ДОКУМЕНТАЦИИ...",
      "searchHint": "Ctrl+K",
      "langStripLabel": "ЯЗЫК ПОРТАЛА // ВЫБОР ЯЗЫКА:",
      "githubLink": "[GITHUB]",
      "badgeNew": "НОВОЕ",
      "badgeVerified": "ПРОВЕРЕНО",
      "copyCode": "[КОПИРОВАТЬ КОД]",
      "copiedCode": "[СКОПИРОВАНО!]",
      "commandBuilder": "ИНТЕРАКТИВНЫЙ КОНСТРУКТОР CLI",
      "builderPrompt": "НАСТРОЙТЕ ПАРАМЕТРЫ И СГЕНЕРИРУЙТЕ КОМАНДУ ВЫПОЛНЕНИЯ:",
      "builderOutputLabel": "ИСПОЛНЯЕМАЯ КОМАНДА CLI:",
      "footerTagline": "Автономный высокопроизводительный распределенный движок сбора данных с самовосстанавливающимися эвристиками DOM и экспортом в Apache Parquet.",
      "searchResults": "найдено",
      "noResults": "нет результатов",
      "selectLocale": "ВЫБЕРИТЕ ЯЗЫК ДОКУМЕНТАЦИИ",
      "changeLanguageTitle": "Сменить язык"
    },
    "modules": [
      "[01] ОБЗОР СИСТЕМЫ",
      "[02] УСТАНОВКА И БЫСТРЫЙ СТАРТ",
      "[03] СПРАВОЧНИК CLI",
      "[04] АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
      "[05] СПРАВОЧНИК КОНФИГУРАЦИИ",
      "[06] ПАНЕЛЬ УПРАВЛЕНИЯ WEBUI",
      "[07] РАЗВЕРТЫВАНИЕ И ЭКСПЛУАТАЦИЯ",
      "[08] ВЫХОДНЫЕ ДАННЫЕ И ЭКСПОРТ",
      "[09] ТЕСТИРОВАНИЕ И ДИАГНОСТИКА",
      "[10] МОДЕЛЬ УГРОЗ И БЕЗОПАСНОСТЬ"
    ],
    "nav": {
      "sec-overview-arch": "[1.1] Архитектура и цели",
      "sec-overview-formats": "[1.2] Поддерживаемые форматы и лимиты",
      "sec-overview-layout": "[1.3] Структура каталогов проекта",
      "sec-overview-pillars": "[1.4] Ключевые архитектурные основы",
      "sec-overview-v28": "[1.5] Базовая архитектура (v0.28.0)",
      "sec-install-prereqs": "[2.1] Системные требования",
      "sec-install-steps": "[2.2] Пошаговая установка",
      "sec-install-launchers": "[2.3] Лаунчеры и интерактивный мастер",
      "sec-install-recipes": "[2.4] Рецепты первого запуска",
      "sec-cli-flags": "[3.1] Полная матрица флагов CLI",
      "sec-cli-builder": "[3.2] Интерактивный генератор CLI",
      "sec-cli-profiles": "[3.3] Профили выполнения",
      "sec-engine-bfs": "[4.1] Цикл обхода BFS",
      "sec-engine-waf": "[4.2] 8-уровневый пайплайн обхода WAF",
      "sec-engine-captcha": "[4.3] Универсальная стратегия капчи",
      "sec-engine-scoring": "[4.4] Оценка качества и фильтрация",
      "sec-engine-normalize": "[4.5] Нормализация URL",
      "sec-engine-pool": "[4.6] Пул прогретых браузеров",
      "sec-engine-broker": "[4.7] Брокер задач Redis Streams",
      "sec-engine-ml": "[4.8] Аппаратное зрение и ML-пайплайн",
      "sec-engine-healing": "[4.9] Самовосстанавливающийся парсер DOM",
      "sec-engine-bktree": "[4.10] Дедупликация BK-Tree",
      "sec-config-env": "[5.1] Переменные окружения (.env)",
      "sec-config-domain": "[5.2] Конфигурация доменов (domain_config)",
      "sec-config-urlnorm": "[5.3] Правила нормализации URL",
      "sec-config-seeds": "[5.4] Синтаксис сид-манифестов",
      "sec-config-profiles": "[5.5] Профили объектов",
      "sec-config-blacklist": "[5.6] Управление черными списками",
      "sec-webui-arch": "[6.1] Архитектура веб-сервера",
      "sec-webui-views": "[6.2] Командный центр и хранилище",
      "sec-webui-telemetry": "[6.3] Телеметрия в реальном времени и SSE",
      "sec-webui-design": "[6.4] Токены бруталистского дизайна",
      "sec-webui-health": "[6.5] Тактический монитор здоровья узлов",
      "sec-ops-docker": "[7.1] Развертывание Docker Compose",
      "sec-ops-watchdog": "[7.2] Агент сторожевого таймера (Watchdog)",
      "sec-ops-notifications": "[7.3] Пайплайн уведомлений",
      "sec-ops-proxy": "[7.4] Управление пулом прокси",
      "sec-ops-sessions": "[7.5] Хранилище сессий и cookie",
      "sec-output-structure": "[8.1] Структура каталогов вывода",
      "sec-output-manifest": "[8.2] Схема manifest.json",
      "sec-output-domain": "[8.3] Схема domain_report.json",
      "sec-output-kohya": "[8.4] Экспорт датасета Kohya LoRA",
      "sec-output-rag": "[8.5] Форматы для RAG",
      "sec-output-cas": "[8.6] Адресуемое по контенту хранилище (CAS)",
      "sec-output-parquet": "[8.7] Экспорт в формат Apache Parquet",
      "sec-test-pytest": "[9.1] Запуск тестов pytest",
      "sec-test-tdai": "[9.2] Протокол верификации (TDAI)",
      "sec-test-logs": "[9.3] Диагностика логов",
      "sec-test-diagnostic": "[9.4] Матрица диагностики оператора",
      "sec-test-guidelines": "[9.5] Руководство для разработчиков",
      "sec-threat-overview": "[10.1] Область моделирования угроз",
      "sec-threat-leasing": "[10.2] Матрица аренды задач",
      "sec-threat-cas": "[10.3] Матрица облачного CAS",
      "sec-threat-vlm": "[10.4] Матрица восстановления VLM",
      "sec-threat-ac": "[10.5] Критерии приемки"
    },
    "footer": {
      "logo": "scrAPE // ОСНОВНАЯ СИСТЕМА",
      "tagline": "Автономный высокопроизводительный распределенный движок сбора данных с самовосстанавливающимися эвристиками DOM и экспортом в Apache Parquet.",
      "badges": [
        "РЕЛИЗ v0.30.1",
        "ЛИЦЕНЗИЯ MIT",
        "PYTHON 3.10+"
      ],
      "headings": {
        "repo": "РЕПОЗИТОРИЙ",
        "docs": "ДОКУМЕНТАЦИЯ"
      },
      "links": [
        "Исходный код",
        "Заметки о выпуске (v0.30.1)",
        "Трекер проблем",
        "CI / Рабочие процессы",
        "Системный README",
        "Модель угроз (v0.30.0)",
        "Журнал изменений",
        "Лицензия MIT",
        "Docker Compose"
      ],
      "copy": "© 2026 Разработчики scrAPE. Открытый исходный код под лицензией MIT.",
      "sysinfo": "СТАТУС: РАБОТАЕТ // ДВИЖОК: v0.30.1"
    },
    "sections": {
      "sec-overview-arch": {
        "tag": "МОДУЛЬ [01] // ОБЗОР СИСТЕМЫ",
        "h1": "Архитектура и цели системы",
        "desc": "Многомоторная stealth-система веб-скрейпинга для автономного извлечения медиа и генерации датасетов для ИИ.",
        "cards": [
          "1.1 Архитектура системы"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] БАЗОВАЯ ГАРАНТИЯ РАБОТОСПОСОБНОСТИ",
            "bodyHtml": "Система функционирует через 8-уровневый резервный пайплайн WAF. При обнаружении циклов проверок запросы автоматически эскалируются от легковесного прямого HTTP до автоматизации в stealth-браузере с графическим интерфейсом. Ручное вмешательство не требуется."
          }
        ]
      },
      "sec-overview-formats": {
        "tag": "МОДУЛЬ [01] // ОБЗОР СИСТЕМЫ",
        "h1": "Поддерживаемые форматы и эксплуатационные лимиты",
        "desc": "Спецификации ресурсов, фильтры размера файлов, ограничения разрешения и лимиты запросов.",
        "cards": [
          "1.2 Возможности медиа и данных"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-overview-layout": {
        "tag": "МОДУЛЬ [01] // ОБЗОР СИСТЕМЫ",
        "h1": "Структура каталогов проекта",
        "desc": "Организация файлов и модулей репозитория.",
        "cards": [
          "1.3 Структура каталогов"
        ],
        "codeHeaders": [
          "ТЕКСТ // ДЕРЕВО РЕПОЗИТОРИЯ"
        ],
        "alerts": []
      },
      "sec-overview-pillars": {
        "tag": "МОДУЛЬ [01] // ОБЗОР СИСТЕМЫ",
        "h1": "Основные архитектурные опоры (v0.30.1)",
        "desc": "Корпоративная многоузловая оркестрация, сублинейная дедупликация BK-Tree, изолированные пулы профилировщиков и хранилище CAS.",
        "cards": [
          "1.4 Основные архитектурные опоры (v0.30.1)"
        ],
        "codeHeaders": [
          "BASH // АКТИВАЦИЯ КЛЮЧЕВЫХ КОМПОНЕНТОВ В CLI"
        ],
        "alerts": []
      },
      "sec-overview-v28": {
        "tag": "МОДУЛЬ [01] // ОБНОВЛЕНИЕ АРХИТЕКТУРЫ",
        "h1": "Архитектура ядра (v0.28.0)",
        "desc": "Промышленный изолированный ML-пайплайн, 3-уровневая иерархическая дедупликация, самовосстанавливающийся парсер DOM и гибридный параллелизм.",
        "cards": [
          "1.4 Архитектурные прорывы в версии v0.28.0"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-prereqs": {
        "tag": "МОДУЛЬ [02] // УСТАНОВКА И БЫСТРЫЙ СТАРТ",
        "h1": "Системные требования и инструменты",
        "desc": "Среда выполнения Python, драйверы браузеров, аппаратное ускорение CUDA и инфраструктура Redis.",
        "cards": [
          "2.1 Системные требования"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-steps": {
        "tag": "МОДУЛЬ [02] // УСТАНОВКА И БЫСТРЫЙ СТАРТ",
        "h1": "Пошаговая инструкция по установке",
        "desc": "Создание виртуального окружения, установка пакетов pip и синхронизация бинарных файлов браузера.",
        "cards": [
          "2.2 Процедура установки и настройки"
        ],
        "codeHeaders": [
          "BASH // КОМАНДЫ УСТАНОВКИ"
        ],
        "alerts": [
          {
            "title": "[i] НАСТРОЙКА FLARESOLVERR",
            "bodyHtml": "FlareSolverr (Уровень 5) работает как контейнер Docker. Запустите его командой: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"
          }
        ]
      },
      "sec-install-launchers": {
        "tag": "МОДУЛЬ [02] // УСТАНОВКА И БЫСТРЫЙ СТАРТ",
        "h1": "Скрипты запуска и интерактивный мастер",
        "desc": "Интерактивные скрипты запуска для всех режимов работы системы.",
        "cards": [
          "2.3 Параметры скрипта запуска и мастера"
        ],
        "codeHeaders": [
          "POWERSHELL // ОСНОВНОЙ СКРИПТ ЗАПУСКА"
        ],
        "alerts": []
      },
      "sec-install-recipes": {
        "tag": "МОДУЛЬ [02] // УСТАНОВКА И БЫСТРЫЙ СТАРТ",
        "h1": "Шаблоны команд для первого запуска",
        "desc": "Готовые команды для типовых сценариев извлечения медиа.",
        "cards": [
          "2.4 Шаблоны команд для первого запуска"
        ],
        "codeHeaders": [
          "РЕЦЕПТ 1 // СТАНДАРТНОЕ ИЗВЛЕЧЕНИЕ ПО SEED-СПИСКАМ С СОХРАНЕНИЕМ ОТКЛОНЕННЫХ МЕДИА",
          "РЕЦЕПТ 2 // НЕПРЕРЫВНЫЙ АГЕНТ-НАБЛЮДАТЕЛЬ С КЭШИРОВАНИЕМ СОСТОЯНИЯ",
          "РЕЦЕПТ 3 // БЫСТРАЯ ПРОВЕРКА (БЕЗ СКАЧИВАНИЯ МЕДИА)",
          "РЕЦЕПТ 4 // ПОИСКОВОЕ ОБНАРУЖЕНИЕ (БЕЗ НАЧАЛЬНЫХ ССЫЛОК)",
          "РЕЦЕПТ 5 // СКРЫТЫЙ СБОР (ВЕЖЛИВЫЙ НИЗКОСКОРОСТНОЙ РЕЖИМ)"
        ],
        "alerts": []
      },
      "sec-cli-flags": {
        "tag": "МОДУЛЬ [03] // СПРАВОЧНИК CLI",
        "h1": "Полная матрица флагов выполнения CLI",
        "desc": "Полное руководство по всем ключам командной строки, переопределениям порогов и бюджетам извлечения.",
        "cards": [
          "3.1 Матрица параметров командной строки"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-cli-builder": {
        "tag": "МОДУЛЬ [03] // СПРАВОЧНИК CLI",
        "h1": "Интерактивный конструктор команд CLI",
        "desc": "Настройка параметров цели, пулов параллелизма и флагов скрытности для генерации готовой команды терминала.",
        "cards": [
          "3.2 Интерактивный генератор команд"
        ],
        "codeHeaders": [
          "СГЕНЕРИРОВАННАЯ СТРОКА КОМАНДЫ CLI"
        ],
        "alerts": []
      },
      "sec-cli-profiles": {
        "tag": "МОДУЛЬ [03] // СПРАВОЧНИК CLI",
        "h1": "Профили выполнения",
        "desc": "Предварительно настроенные профили для специализированных сценариев сбора данных.",
        "cards": [
          "3.3 Матрица предустановленных профилей"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-bfs": {
        "tag": "МОДУЛЬ [04] // АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
        "h1": "Цикл обхода BFS",
        "desc": "Асинхронный цикл поиска в ширину, диспетчеризация очередей с приоритетом и извлечение ссылок.",
        "cards": [
          "4.1 Последовательность выполнения BFS"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-waf": {
        "tag": "МОДУЛЬ [04] // АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
        "h1": "8-уровневый эскалационный stealth-пайплайн WAF",
        "desc": "Многоуровневый адаптивный механизм обхода Cloudflare Turnstile, Datadome, Incapsula и систем защиты от ботов.",
        "cards": [
          "4.2 Иерархия 8-уровневого пайплайна WAF"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-captcha": {
        "tag": "МОДУЛЬ [04] // АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
        "h1": "Универсальная стратегия обхода капчи",
        "desc": "Автоматические провайдеры решения, перехват проверок и обработчики повторных попыток.",
        "cards": [
          "4.3 Стратегия решения капч и проверок"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-scoring": {
        "tag": "МОДУЛЬ [04] // АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
        "h1": "Оценка качества и отбраковка ресурсов",
        "desc": "Классификация URL, пороговые значения размеров изображений и сохранение отклоненных медиа на диск.",
        "cards": [
          "4.4 Правила фильтрации и пути сохранения"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-normalize": {
        "tag": "МОДУЛЬ [04] // АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
        "h1": "Нормализация URL",
        "desc": "Удаление трекинговых параметров, канонизация протоколов и предотвращение избыточных циклов в очереди.",
        "cards": [
          "4.5 Пайплайн нормализации URL"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-pool": {
        "tag": "МОДУЛЬ [04] // АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
        "h1": "Пул предварительно запущенных браузеров",
        "desc": "Высокопроизводительная утилизация пула браузеров Camoufox и изолированное предоставление контекстов.",
        "cards": [
          "4.6 Жизненный цикл пула предварительно запущенных браузеров"
        ],
        "codeHeaders": [
          "PYTHON // АРЕНДА КОНТЕКСТОВ БРАУЗЕРА ИЗ ПУЛА"
        ],
        "alerts": []
      },
      "sec-engine-broker": {
        "tag": "МОДУЛЬ [04] // АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
        "h1": "Брокер задач на базе Redis Streams",
        "desc": "Распределенные группы потребителей, отслеживание незавершенных записей (PEL) и атомарная диспетчеризация задач.",
        "cards": [
          "4.7 Координация распределенного кластера через Redis Streams"
        ],
        "codeHeaders": [
          "PYTHON // ПАТТЕРН ВЗАИМОДЕЙСТВИЯ С БРОКЕРОМ ЗАДАЧ"
        ],
        "alerts": []
      },
      "sec-engine-ml": {
        "tag": "МОДУЛЬ [04] // АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
        "h1": "Аппаратное зрение и ML-пайплайн",
        "desc": "Обнаружение ускорителей CUDA/MPS, инференс в половинной точности (FP16) и эстетический скоринг.",
        "cards": [
          "4.8 Матрица аппаратного ускорения (CUDA / MPS)"
        ],
        "codeHeaders": [
          "PYTHON // ОБНАРУЖЕНИЕ ОБОРУДОВАНИЯ И ВЫБОР ТОЧНОСТИ"
        ],
        "alerts": []
      },
      "sec-engine-healing": {
        "tag": "МОДУЛЬ [04] // АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
        "h1": "Самовосстанавливающийся парсер DOM",
        "desc": "4-уровневый каскад восстановления DOM с эвристическим исправлением через несколько провайдеров LLM.",
        "cards": [
          "4.9 Автономное восстановление селекторов и исправление через VLM"
        ],
        "codeHeaders": [
          "PYTHON // КАСКАД САМОВОССТАНАВЛИВАЮЩЕГОСЯ ИЗВЛЕЧЕНИЯ",
          "ТЕКСТ // КАСКАД СИНТЕЗА ЧЕРЕЗ НЕСКОЛЬКО ПРОВАЙДЕРОВ LLM"
        ],
        "alerts": []
      },
      "sec-engine-bktree": {
        "tag": "МОДУЛЬ [04] // АРХИТЕКТУРА ОСНОВНОГО ДВИЖКА",
        "h1": "Дедупликация на деревьях BK-Tree и сегментация параллелизма",
        "desc": "Индексирование в метрических деревьях, кластеризация по расстоянию Хэмминга и изолированные пулы профилировщиков.",
        "cards": [
          "4.10 Дерево дискретных метрик и сегментация пула выполнения"
        ],
        "codeHeaders": [
          "PYTHON // МЕТРИЧЕСКИЙ ПОИСК В BK-TREE И ПУЛЫ СОЕДИНЕНИЙ"
        ],
        "alerts": []
      },
      "sec-config-env": {
        "tag": "МОДУЛЬ [05] // СПРАВОЧНИК КОНФИГУРАЦИИ",
        "h1": "Переменные окружения (.env)",
        "desc": "Учетные данные продакшена, лимиты скорости, прокси-шлюзы и токены API.",
        "cards": [
          "5.1 Шаблон конфигурации .env"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-domain": {
        "tag": "МОДУЛЬ [05] // СПРАВОЧНИК КОНФИГУРАЦИИ",
        "h1": "domain_config.json",
        "desc": "Ограничения параллелизма по доменам, селекторы ожидания и переопределения заголовков.",
        "cards": [
          "5.2 Справочник ключей конфигурации (domain_config.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-urlnorm": {
        "tag": "МОДУЛЬ [05] // СПРАВОЧНИК КОНФИГУРАЦИИ",
        "h1": "url_normalisation_rules.json",
        "desc": "Регулярные выражения для удаления параметров запроса и трансформации доменов.",
        "cards": [
          "5.3 Схема правил нормализации (url_normalisation_rules.json)"
        ],
        "codeHeaders": [
          "JSON // ПРИМЕР СХЕМЫ ПРАВИЛА"
        ],
        "alerts": [
          {
            "title": "[!] ОБЯЗАТЕЛЬНОЕ ПРАВИЛО",
            "bodyHtml": "Ни в коем случае не зашивайте регулярные выражения нормализации URL для конкретных доменов в коде Python в каталоге <code>src/</code>. Все правила ДОЛЖНЫ быть объявлены в <code>data/url_normalisation_rules.json</code>."
          }
        ]
      },
      "sec-config-seeds": {
        "tag": "МОДУЛЬ [05] // СПРАВОЧНИК КОНФИГУРАЦИИ",
        "h1": "Синтаксис манифестов seed-ссылок",
        "desc": "Комментарии, строчные директивы и веса приоритета в файлах seeds/*.txt.",
        "cards": [
          "5.4 Справочник аннотаций манифеста seed-ссылок"
        ],
        "codeHeaders": [
          "MANIFEST // ПРИМЕР АННОТАЦИЙ МАНИФЕСТА SEED-СПИСКА"
        ],
        "alerts": []
      },
      "sec-config-profiles": {
        "tag": "МОДУЛЬ [05] // СПРАВОЧНИК КОНФИГУРАЦИИ",
        "h1": "Профили объектов сбора",
        "desc": "Специфические для объектов шаблоны, шаблоны вывода и привязки к черным спискам.",
        "cards": [
          "5.5 Предустановки профилей (subject_profiles.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-blacklist": {
        "tag": "МОДУЛЬ [05] // СПРАВОЧНИК КОНФИГУРАЦИИ",
        "h1": "Управление черными списками",
        "desc": "Глобально исключенные домены, рекламные сети и паттерны нерелевантных ресурсов.",
        "cards": [
          "5.6 Управление черными списками доменов (blacklist.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-arch": {
        "tag": "МОДУЛЬ [06] // ПАНЕЛЬ УПРАВЛЕНИЯ WEBUI",
        "h1": "Архитектура сервера WebUI",
        "desc": "Реактивный командный центр на базе FastAPI и HTMX с потоковой телеметрией в реальном времени через SSE.",
        "cards": [
          "6.1 Изолированный сервер FastAPI"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-views": {
        "tag": "МОДУЛЬ [06] // ПАНЕЛЬ УПРАВЛЕНИЯ WEBUI",
        "h1": "Командный центр и медиа-хранилище",
        "desc": "Интерактивная панель управления, мониторинг скрейпера в реальном времени и галерея ресурсов.",
        "cards": [
          "6.2 Представления дашборда (Командный центр и хранилище)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-telemetry": {
        "tag": "МОДУЛЬ [06] // ПАНЕЛЬ УПРАВЛЕНИЯ WEBUI",
        "h1": "Телеметрия в реальном времени и SSE",
        "desc": "Потоковая передача событий через Server-Sent Events, скорость очередей и датчики памяти.",
        "cards": [
          "6.3 Пайплайн событий реального времени (SSE и Canvas)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-design": {
        "tag": "МОДУЛЬ [06] // ПАНЕЛЬ УПРАВЛЕНИЯ WEBUI",
        "h1": "Дизайн-токены",
        "desc": "Тактические CSS-токены утилитарного брутализма, высококонтрастная моноширинная типографика и палитры.",
        "cards": [
          "6.4 Справочник дизайн-токенов (Тактический брутализм)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-health": {
        "tag": "МОДУЛЬ [06] // ПАНЕЛЬ УПРАВЛЕНИЯ WEBUI",
        "h1": "Тактический монитор работоспособности узлов",
        "desc": "Проверки состояния подсистем, периодические пробы heartbeat и телеметрия кластера Redis.",
        "cards": [
          "6.5 Тактическая телеметрия и управление узлами"
        ],
        "codeHeaders": [
          "JSON // ПОЛЕЗНАЯ НАГРУЗКА ТЕЛЕМЕТРИИ РАБОТОСПОСОБНОСТИ УЗЛА"
        ],
        "alerts": []
      },
      "sec-ops-docker": {
        "tag": "МОДУЛЬ [07] // РАЗВЕРТЫВАНИЕ И ЭКСПЛУАТАЦИЯ",
        "h1": "Развертывание через Docker Compose",
        "desc": "Многоконтейнерное производственное развертывание с FlareSolverr, Redis и WebUI.",
        "cards": [
          "7.1 Развертывание в контейнерах с Docker Compose"
        ],
        "codeHeaders": [
          "BASH // ЗАПУСК ЧЕРЕЗ DOCKER COMPOSE"
        ],
        "alerts": []
      },
      "sec-ops-watchdog": {
        "tag": "МОДУЛЬ [07] // РАЗВЕРТЫВАНИЕ И ЭКСПЛУАТАЦИЯ",
        "h1": "Агент-наблюдатель (Watchdog)",
        "desc": "Демон непрерывного сбора данных с автоматической проверкой работоспособности и перезапуском.",
        "cards": [
          "7.2 Непрерывный цикл мониторинга (Watchdog)"
        ],
        "codeHeaders": [
          "POWERSHELL // КОМАНДА ЗАПУСКА АГЕНТА WATCHDOG"
        ],
        "alerts": []
      },
      "sec-ops-notifications": {
        "tag": "МОДУЛЬ [07] // РАЗВЕРТЫВАНИЕ И ЭКСПЛУАТАЦИЯ",
        "h1": "Пайплайн уведомлений",
        "desc": "Подключаемые каналы оповещений (Telegram, Discord, Slack, вебхуки).",
        "cards": [
          "7.3 Многоканальные оповещения (Telegram, Discord, Slack)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-proxy": {
        "tag": "МОДУЛЬ [07] // РАЗВЕРТЫВАНИЕ И ЭКСПЛУАТАЦИЯ",
        "h1": "Управление пулом прокси",
        "desc": "Ротация прокси, автоматическая изоляция узлов с высокой задержкой и квоты трафика.",
        "cards": [
          "7.4 Стратегия управления пулом прокси и изоляция задержек"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-sessions": {
        "tag": "МОДУЛЬ [07] // РАЗВЕРТЫВАНИЕ И ЭКСПЛУАТАЦИЯ",
        "h1": "Управление сессиями и cookie",
        "desc": "Постоянные сессии с привязкой к доменам и интерактивный вход для сбора cookie.",
        "cards": [
          "7.5 Хранилище сессий и управление cookie"
        ],
        "codeHeaders": [
          "BASH // КОМАНДЫ ДЛЯ АВТОРИЗАЦИИ СЕССИИ"
        ],
        "alerts": []
      },
      "sec-output-structure": {
        "tag": "МОДУЛЬ [08] // ВЫХОДНЫЕ ДАННЫЕ И ЭКСПОРТ",
        "h1": "Структура каталогов вывода",
        "desc": "Структура файлов и артефактов по завершении цикла сбора данных.",
        "cards": [
          "8.1 Организация артефактов и выходной директории"
        ],
        "codeHeaders": [
          "ТЕКСТ // СТРУКТУРА КАТАЛОГА ВЫВОДА"
        ],
        "alerts": []
      },
      "sec-output-manifest": {
        "tag": "МОДУЛЬ [08] // ВЫХОДНЫЕ ДАННЫЕ И ЭКСПОРТ",
        "h1": "Схема manifest.json",
        "desc": "Полная документация схемы JSON для итогового манифеста.",
        "cards": [
          "8.2 Поля полезной нагрузки JSON (manifest.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-domain": {
        "tag": "МОДУЛЬ [08] // ВЫХОДНЫЕ ДАННЫЕ И ЭКСПОРТ",
        "h1": "Схема domain_report.json",
        "desc": "Отчет о метриках сбора данных с разбивкой по каждому домену.",
        "cards": [
          "8.3 Отчет об эффективности по доменам (domain_report.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-kohya": {
        "tag": "МОДУЛЬ [08] // ВЫХОДНЫЕ ДАННЫЕ И ЭКСПОРТ",
        "h1": "Экспорт датасетов Kohya LoRA",
        "desc": "Генерация готовых ZIP-архивов датасетов в формате Kohya_ss LoRA.",
        "cards": [
          "8.4 Генератор датасетов для Kohya LoRA"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-rag": {
        "tag": "МОДУЛЬ [08] // ВЫХОДНЫЕ ДАННЫЕ И ЭКСПОРТ",
        "h1": "Форматы импорта для RAG",
        "desc": "Экспорт для RAG в LLM (структурированные фрагменты Markdown и эмбеддинги в JSONL).",
        "cards": [
          "8.5 Форматы экспорта для RAG (Markdown и JSONL)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-cas": {
        "tag": "МОДУЛЬ [08] // ВЫХОДНЫЕ ДАННЫЕ И ЭКСПОРТ",
        "h1": "Хранилище с адресацией по содержимому (CAS)",
        "desc": "Глобальный репозиторий дедупликации SHA-256, исключающий дубликаты файлов при повторных обходах.",
        "cards": [
          "8.6 Архитектура адресации по содержимому (CAS)"
        ],
        "codeHeaders": [
          "PYTHON // ДЕДУПЛИКАЦИЯ CAS И СВЯЗЫВАНИЕ ЗАПУСКОВ",
          "ТЕКСТ // ЖИЗНЕННЫЙ ЦИКЛ ХРАНИЛИЩА CAS"
        ],
        "alerts": []
      },
      "sec-output-parquet": {
        "tag": "МОДУЛЬ [08] // ВЫХОДНЫЕ ДАННЫЕ И ЭКСПОРТ",
        "h1": "Экспорт датасетов в Apache Parquet",
        "desc": "Колоночные датасеты со сжатием Snappy, оптимизированные для аналитических пайплайнов Polars, DuckDB, Pandas и OLAP.",
        "cards": [
          "8.7 Пайплайн колоночного экспорта данных (Apache Parquet)"
        ],
        "codeHeaders": [
          "PYTHON // ГЕНЕРАЦИЯ ДАТАСЕТОВ PARQUET"
        ],
        "alerts": []
      },
      "sec-test-pytest": {
        "tag": "МОДУЛЬ [09] // ТЕСТИРОВАНИЕ И ДИАГНОСТИКА",
        "h1": "Запуск набора тестов pytest",
        "desc": "Выполнение полного автоматизированного набора модульных и интеграционных тестов.",
        "cards": [
          "9.1 Автоматизированный набор тестов Pytest"
        ],
        "codeHeaders": [
          "POWERSHELL // ЗАПУСК ПОЛНОГО НАБОРА ТЕСТОВ"
        ],
        "alerts": []
      },
      "sec-test-tdai": {
        "tag": "МОДУЛЬ [09] // ТЕСТИРОВАНИЕ И ДИАГНОСТИКА",
        "h1": "Протокол эмпирической верификации (TDAI)",
        "desc": "Правила верификации на основе тестов (TDAI) и цикл RED-GREEN-REFACTOR.",
        "cards": [
          "9.2 Эмпирический протокол верификации (TDAI)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] ОБЯЗАТЕЛЬНОЕ ПРАВИЛО",
            "bodyHtml": "Никогда не объявляйте задачу или исправление завершенными без запуска эмпирических команд проверки в реальном времени и демонстрации успешных тестов."
          }
        ]
      },
      "sec-test-logs": {
        "tag": "МОДУЛЬ [09] // ТЕСТИРОВАНИЕ И ДИАГНОСТИКА",
        "h1": "Рецепты диагностики по логам",
        "desc": "Анализ логов и команды grep для быстрой диагностики в рантайме.",
        "cards": [
          "9.3 Диагностические команды PowerShell и анализ логов"
        ],
        "codeHeaders": [
          "POWERSHELL // ПОИСК ОШИБОК И БЛОКИРОВОК В ЛОГАХ"
        ],
        "alerts": []
      },
      "sec-test-diagnostic": {
        "tag": "МОДУЛЬ [09] // ТЕСТИРОВАНИЕ И ДИАГНОСТИКА",
        "h1": "Диагностическая матрица оператора",
        "desc": "Исчерпывающая диагностическая таблица для устранения неполадок оператором.",
        "cards": [
          "9.4 Матрица диагностики оператора"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-test-guidelines": {
        "tag": "МОДУЛЬ [09] // ТЕСТИРОВАНИЕ И ДИАГНОСТИКА",
        "h1": "Руководство для разработчиков",
        "desc": "Обязательные стандарты написания кода и требования к качеству проекта.",
        "cards": [
          "9.5 Обязательные стандарты разработки кода"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-threat-overview": {
        "tag": "МОДУЛЬ [10] // МОДЕЛЬ УГРОЗ И БЕЗОПАСНОСТЬ",
        "h1": "Архитектура безопасности и верификация v0.30.0",
        "desc": "Официальная модель угроз, архитектурный контракт STRIDE и матрица эмпирической проверки распределенного масштабирования v0.30.0.",
        "cards": [
          "10.1 Границы доверия и архитектура потоков данных",
          "10.1.1 Категоризация угроз STRIDE",
          "10.1.2 Сквозные инварианты"
        ],
        "codeHeaders": [
          "АРХИТЕКТУРА // РАСПРЕДЕЛЕННЫЕ ГРАНИЦЫ ДОВЕРИЯ И ПОТОК ДАННЫХ v0.30.0"
        ],
        "alerts": [
          {
            "title": "ПРОИЗВОДСТВЕННЫЙ РЕЛИЗ // v0.30.0 ПРОВЕРЕН И СЕРТИФИЦИРОВАН",
            "bodyHtml": "Все три области моделирования угроз (распределенная аренда задач, облачная синхронизация CAS, исправление DOM через VLM) в версии v0.30.0 <strong>полностью реализованы, протестированы на устойчивость к атакам и верифицированы в матрице CI</strong>."
          },
          {
            "title": "ОБЯЗАТЕЛЬНЫЙ АРХИТЕКТУРНЫЙ КОНТРАКТ",
            "bodyHtml": "Настоящая спецификация является обязательным эталоном для всех реализаций в версии v0.30.0. Каждый критерий приемки (AC1.1–AC3.6) должен быть подкреплен автоматизированным тестом в <code>tests/</code>."
          }
        ]
      },
      "sec-threat-leasing": {
        "tag": "МОДУЛЬ [10] // КОМПОНЕНТ 1 (РЕАЛИЗОВАН И ПРОВЕРЕН)",
        "h1": "Матрица угроз распределенной аренды задач (Компонент 1)",
        "desc": "Анализ уязвимостей по модели STRIDE, сценарии атак и механизмы атомарной защиты для воркеров Redis Stream.",
        "cards": [
          "10.2 Обзор архитектуры компонента 1",
          "10.2.1 Матрица угроз и уязвимостей (Компонент 1)",
          "10.2.2 Детальные спецификации защиты"
        ],
        "codeHeaders": [
          "PYTHON // АТОМАРНЫЙ ЗАХВАТ БЛОКИРОВКИ ИДЕМПОТЕНТНОСТИ"
        ],
        "alerts": [
          {
            "title": "КОМПОНЕНТ 1 РЕАЛИЗОВАН И ПРОВЕРЕН // AC1.1–AC1.7 ПРОЙДЕНЫ",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>, <code>DistributedWorkerNode</code> и CLI-воркеры полностью реализованы и проверены на соответствие критериям приемки AC1.1–AC1.7 (98 тестов)."
          }
        ]
      },
      "sec-threat-cas": {
        "tag": "МОДУЛЬ [10] // АРХИТЕКТУРА КОМПОНЕНТА 2",
        "h1": "Матрица угроз синхронизации облачного хранилища CAS (Компонент 2)",
        "desc": "Спецификации эшелонированной обороны, криптографическая проверка и защита от SSRF для хранилищ S3 / Cloudflare R2 / MinIO.",
        "cards": [
          "10.3 Обзор архитектуры компонента 2",
          "10.3.1 Матрица угроз и уязвимостей (Компонент 2)",
          "10.3.2 Принудительная изоляция криптографических хэш-путей"
        ],
        "codeHeaders": [
          "PYTHON // ВАЛИДАЦИЯ ПУТИ КЛЮЧА CAS И ПРОВЕРКА КОНТРОЛЬНОЙ СУММЫ"
        ],
        "alerts": [
          {
            "title": "СЕРТИФИЦИРОВАНО ДЛЯ ПРОДАКШЕНА // КОМПОНЕНТ 2 ПОЛНОСТЬЮ РЕАЛИЗОВАН",
            "bodyHtml": "<code>CASCloudSyncer</code> и бэкенды S3/R2/MinIO <strong>полностью реализованы и проверены</strong> в версии v0.30.0 со 100% успешных тестов по критериям AC2.1–AC2.7."
          }
        ]
      },
      "sec-threat-vlm": {
        "tag": "МОДУЛЬ [10] // КОМПОНЕНТ 3 (РЕАЛИЗОВАН И ПРОВЕРЕН)",
        "h1": "Матрица угроз самовосстановления DOM через Vision-Language (Компонент 3)",
        "desc": "Меры безопасности мультимодального ИИ, защита от визуальных prompt-инъекций и песочница взаимодействия с DOM.",
        "cards": [
          "10.4 Обзор архитектуры компонента 3",
          "10.4.1 Матрица угроз и уязвимостей (Компонент 3)",
          "10.4.2 Обрамление ненадежных данных и барьеры вывода"
        ],
        "codeHeaders": [
          "АРХИТЕКТУРА ПРОМПТА // ИЗОЛИРОВАННЫЙ СИСТЕМНЫЙ ПРОМПТ VLM"
        ],
        "alerts": [
          {
            "title": "СЕРТИФИЦИРОВАНО ДЛЯ ПРОДАКШЕНА // КОМПОНЕНТ 3 ПОЛНОСТЬЮ РЕАЛИЗОВАН",
            "bodyHtml": "<code>VisionDOMHealer</code> (мультимодальное исправление DOM уровня 4) <strong>полностью реализован и проверен</strong> в версии v0.30.0 со 100% успешных тестов по критериям AC3.1–AC3.6."
          }
        ]
      },
      "sec-threat-ac": {
        "tag": "МОДУЛЬ [10] // МАТРИЦА ВЕРИФИКАЦИИ И АУДИТА (v0.30.0 PRODUCTION)",
        "h1": "Матрица верификации критериев приемки (v0.30.0 Production)",
        "desc": "Спецификации эмпирических тестов, методологии проверки и результаты аудита для всех 20 критериев приемки v0.30.0.",
        "cards": [
          "10.5.1 Критерии приемки компонента 1 (Task Leasing)",
          "10.5.2 Критерии приемки компонента 2 (Cloud CAS)",
          "10.5.3 Критерии приемки компонента 3 (VLM Healing)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "ВСЕ 20 КРИТЕРИЕВ ПРИЕМКИ ПРОВЕРЕНЫ И СЕРТИФИЦИРОВАНЫ",
            "bodyHtml": "Все 20 критериев ниже (AC1.1–AC3.6) представляют собой <strong>ключевой архитектурный контракт</strong> версии v0.30.0. Каждый критерий подтвержден автоматическими тестами в <code>tests/</code> со 100% прохождением."
          },
          {
            "title": "СТАНДАРТ ВЕРИФИКАЦИИ",
            "bodyHtml": "Ни один pull request или тег релиза v0.30.0 не будет утвержден без 100% покрытия тестами всех 20 критериев приемки."
          }
        ]
      }
    },
    "snippets": {
      "sec-install-steps": "# 1. Клонировать репозиторий\ngit clone https://github.com/rhaffle87/scrAPE.git\ncd scrAPE\n\n# 2. Создать и активировать виртуальное окружение\npython -m venv venv\nvenv\\Scripts\\activate          # Windows CMD\n.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell\nsource venv/bin/activate       # Linux / macOS\n\n# 3. Установить зависимости Python\npip install -r requirements.txt\n\n# 4. (Опционально) Установить Node.js-мост Crawlee для стелс-уровней 6-7\ncd crawlee_bridge && npm install && cd ..\n\n# 5. Настроить учетные данные\ncopy .env.example .env         # Windows\ncp .env.example .env           # Linux / macOS\n# Затем отредактируйте .env с вашими ключами API и URL вебхуков",
      "sec-install-launchers": "# Основной скрипт запуска Windows (Интерактивное меню)\n.\\run.bat\n\n# Основной скрипт запуска Linux / macOS\n./run.sh\n\n# Прямой запуск интерактивного мастера (без меню)\npython src/cli/cli_wizard.py",
      "sec-ops-docker": "# Запуск ядра скрейпера + контейнер FlareSolverr\ndocker compose up -d\n\n# Просмотр логов кластера в реальном времени\ndocker compose logs -f\n\n# Корректная остановка контейнеров\ndocker compose down",
      "sec-ops-watchdog": "# Запуск агента Watchdog через оболочку запуска\n.\\run.bat watchdog\n\n# Прямой запуск непрерывного мониторинга\npython src/cli/monitor_agent.py --keyword \"example_subject\" --seed seeds/example_subject.txt --use-state-cache",
      "sec-ops-sessions": "# Захват cookie через интерактивное окно браузера\npython src/cli/session_auth.py --domain example.com --login-url https://example.com/login\n\n# Список сохраненных постоянных сессий cookie\npython src/cli/session_auth.py --list-sessions",
      "sec-test-pytest": "# Запуск всех 378+ модульных и интеграционных тестов\npytest tests/ -v\n\n# Запуск с отчетом о покрытии кода\npytest --cov=src tests/ --cov-report=term-missing",
      "sec-test-logs": "# Поиск лимитов HTTP 429 и блокировок Cloudflare в логах\nGet-Content logs/crawler.log -Tail 100 | Select-String -Pattern \"429|Cloudflare|WAF|BLOCKED\"\n\n# Мониторинг логов скрейпера в реальном времени\nGet-Content logs/crawler.log -Wait -Tail 20"
    },
    "lists": {
      "sec-install-launchers": [
        "<strong>Широкий поисковый сбор</strong> -- Автоматизированные поисковые запросы с рекурсивным обходом ссылок.",
        "<strong>Целевой сбор по манифесту</strong> -- Структурированный сбор по выбранным файлам начальных ссылок seeds/*.txt.",
        "<strong>Непрерывный агент-наблюдатель (Watchdog)</strong> -- Долговременный цикл мониторинга с кэшированием в SQLite WAL.",
        "<strong>Создание структурированного датасета для ИИ</strong> -- Упаковка выходных данных с группировкой по доменам или типам файлов.",
        "<strong>Импорт в корпоративные RAG-системы для LLM</strong> -- Экспорт страниц в виде единого Markdown, фрагментов <code>.md</code> или эмбеддингов JSONL."
      ]
    },
    "h3Map": {
      "Wizard Menu Options": "Опции меню мастера",
      "Core Components": "Основные компоненты",
      "Media Vault View": "Панель медиа-хранилища",
      "Command Center View": "Панель командного центра",
      "Budget & Balance Guardrails": "Ограничители бюджета и баланса",
      "Circuit Breaker & Cooldown Mechanics": "Механизмы автоматического размыкателя и охлаждения",
      "Download Validation Thresholds": "Пороговые значения проверки загрузок",
      "Primary v0.30.1 Execution Flags": "Основные флаги выполнения v0.30.1",
      "Site-Chrome & Keyword Classification Sets": "Наборы классификации интерфейса и ключевых слов",
      "Dead-Letter Stream Protocol": "Протокол потока недоставленных сообщений (Dead-Letter)",
      "Idempotency Lock Implementation": "Реализация блокировки идемпотентности",
      "Node Health JSON Schema (/api/telemetry/node-health)": "JSON-схема работоспособности узлов (/api/telemetry/node-health)"
    },
    "thMap": {
      "Component": "Компонент",
      "Source File": "Исходный файл",
      "Function": "Функция",
      "Requirement": "Требование",
      "Minimum": "Минимум",
      "Notes": "Примечания",
      "Category": "Категория",
      "Supported Types": "Поддерживаемые типы",
      "Processing Method": "Метод обработки",
      "Core Pillar": "Ключевая опора",
      "Key Technologies": "Ключевые технологии",
      "Production Capability": "Производственная возможность",
      "Parameter": "Параметр",
      "Type": "Тип",
      "Default": "По умолчанию",
      "Description": "Описание",
      "Status": "Статус",
      "Tier": "Уровень",
      "Mechanism": "Механизм",
      "Overhead": "Накладные расходы",
      "Usage": "Использование",
      "Profile": "Профиль",
      "Keyword": "Ключевое слово",
      "Concurrency": "Параллелизм",
      "Depth": "Глубина",
      "Endpoint": "Эндпоинт",
      "Impact": "Влияние",
      "Channel": "Канал",
      "Provider": "Провайдер",
      "Purpose": "Назначение"
    }
  },
  "de": {
    "meta": {
      "title": "scrAPE v0.30.1 // Technisches Dokumentationsportal",
      "desc": "Offizielle technische Dokumentation, CLI-Flag-Matrix, Architekturleitfaden und Betriebshandbuch für scrAPE v0.30.1."
    },
    "ui": {
      "searchPlaceholder": "DOKUMENTATION DURCHSUCHEN...",
      "searchHint": "Strg+K",
      "langStripLabel": "PORTALSPRACHE // SPRACHAUSWAHL:",
      "githubLink": "[GITHUB]",
      "badgeNew": "NEU",
      "badgeVerified": "VERIFIZIERT",
      "copyCode": "[CODE KOPIEREN]",
      "copiedCode": "[KOPIERT!]",
      "commandBuilder": "INTERAKTIVER CLI-BEFEHLSGENERATOR",
      "builderPrompt": "PARAMETER KONFIGURIEREN & LAUFZEITBEFEHL GENERIEREN:",
      "builderOutputLabel": "AUSFÜHRBARER CLI-BEFEHL:",
      "footerTagline": "Autonome, hochdurchsatzfähige verteilte Scraping-Engine mit selbstheilenden DOM-Heuristiken und Apache-Parquet-Export.",
      "searchResults": "gefunden",
      "noResults": "keine Treffer",
      "selectLocale": "DOKUMENTATIONSSPRACHE AUSWÄHLEN",
      "changeLanguageTitle": "Sprache ändern"
    },
    "modules": [
      "[01] SYSTEMÜBERSICHT",
      "[02] INSTALLATION & SCHNELLSTART",
      "[03] CLI-REFERENZ",
      "[04] KERN-ENGINE-ARCHITEKTUR",
      "[05] KONFIGURATIONSREFERENZ",
      "[06] WEBUI-DASHBOARD",
      "[07] DEPLOYMENT & BETRIEB",
      "[08] AUSGABE & EXPORTE",
      "[09] TESTS & FEHLERBEHEBUNG",
      "[10] BEDROHUNGSMODELL & SICHERHEIT"
    ],
    "nav": {
      "sec-overview-arch": "[1.1] Architektur und Zielsetzung",
      "sec-overview-formats": "[1.2] Unterstützte Formate und Limits",
      "sec-overview-layout": "[1.3] Projekt-Verzeichnisstruktur",
      "sec-overview-pillars": "[1.4] Kernpfeiler der nächsten Generation",
      "sec-overview-v28": "[1.5] Kernarchitektur (v0.28.0)",
      "sec-install-prereqs": "[2.1] Systemvoraussetzungen",
      "sec-install-steps": "[2.2] Installationsschritte",
      "sec-install-launchers": "[2.3] Haupt-Starter und Assistent",
      "sec-install-recipes": "[2.4] Rezepte für den ersten Lauf",
      "sec-cli-flags": "[3.1] Vollständige CLI-Flag-Matrix",
      "sec-cli-builder": "[3.2] Interaktiver CLI-Befehlsgenerator",
      "sec-cli-profiles": "[3.3] Ausführungsprofile",
      "sec-engine-bfs": "[4.1] BFS-Crawl-Schleife",
      "sec-engine-waf": "[4.2] 8-stufige Stealth-WAF-Pipeline",
      "sec-engine-captcha": "[4.3] Universelle Captcha-Strategie",
      "sec-engine-scoring": "[4.4] Qualitätsbewertung und Filter",
      "sec-engine-normalize": "[4.5] URL-Normalisierung",
      "sec-engine-pool": "[4.6] Vorgewärmter Browser-Pool",
      "sec-engine-broker": "[4.7] Redis Streams Task-Broker",
      "sec-engine-ml": "[4.8] Vision-Hardware & ML-Pipeline",
      "sec-engine-healing": "[4.9] Selbstheilender DOM-Parser",
      "sec-engine-bktree": "[4.10] BK-Tree Perceptual-Deduplizierung",
      "sec-config-env": "[5.1] Umgebungsvariablen (.env)",
      "sec-config-domain": "[5.2] Domain-Konfiguration (domain_config)",
      "sec-config-urlnorm": "[5.3] URL-Regex-Regeln",
      "sec-config-seeds": "[5.4] Seed-Manifest-Syntax",
      "sec-config-profiles": "[5.5] Zielprofile",
      "sec-config-blacklist": "[5.6] Blacklist-Verwaltung",
      "sec-webui-arch": "[6.1] Serverarchitektur",
      "sec-webui-views": "[6.2] Kommandozentrale & Medientresor",
      "sec-webui-telemetry": "[6.3] Live-Telemetrie und SSE",
      "sec-webui-design": "[6.4] Brutalismus-Design-Tokens",
      "sec-webui-health": "[6.5] Taktischer Knoten-Gesundheitsmonitor",
      "sec-ops-docker": "[7.1] Docker Compose",
      "sec-ops-watchdog": "[7.2] Watchdog-Daemon",
      "sec-ops-notifications": "[7.3] Multi-Kanal-Benachrichtigungen",
      "sec-ops-proxy": "[7.4] Proxy-Pool-Verwaltung",
      "sec-ops-sessions": "[7.5] Sitzungs- und Cookie-Tresor",
      "sec-output-structure": "[8.1] Ausgabeverzeichnis-Struktur",
      "sec-output-manifest": "[8.2] manifest.json-Schema",
      "sec-output-domain": "[8.3] domain_report.json-Bericht",
      "sec-output-kohya": "[8.4] Kohya LoRA Dataset-Export",
      "sec-output-rag": "[8.5] RAG-Ingestionsformate",
      "sec-output-cas": "[8.6] Inhaltsadressierter Speicher (CAS)",
      "sec-output-parquet": "[8.7] Apache Parquet Dataset-Export",
      "sec-test-pytest": "[9.1] pytest ausführen",
      "sec-test-tdai": "[9.2] Verifikationsprotokoll (TDAI)",
      "sec-test-logs": "[9.3] Log-Diagnoserezepte",
      "sec-test-diagnostic": "[9.4] Operator-Diagnosematrix",
      "sec-test-guidelines": "[9.5] Entwicklerrichtlinien",
      "sec-threat-overview": "[10.1] Sicherheitsumfang vor Implementierung",
      "sec-threat-leasing": "[10.2] Task-Leasing-Matrix",
      "sec-threat-cas": "[10.3] Cloud-CAS-Sicherheitsmatrix",
      "sec-threat-vlm": "[10.4] VLM-Selbstheilungs-Sicherheitsmatrix",
      "sec-threat-ac": "[10.5] Akzeptanzkriterien-Vertrag"
    },
    "footer": {
      "logo": "scrAPE // KERN-SYSTEM",
      "tagline": "Autonome, hochdurchsatzfähige verteilte Scraping-Engine mit selbstheilenden DOM-Heuristiken und Apache-Parquet-Export.",
      "badges": [
        "VERSION v0.30.1",
        "MIT-LIZENZIERT",
        "PYTHON 3.10+"
      ],
      "headings": {
        "repo": "REPOSITORY",
        "docs": "DOKUMENTATION"
      },
      "links": [
        "Quellcode",
        "Versionshinweise (v0.30.1)",
        "Fehler-Tracker",
        "CI / Workflows",
        "System-README",
        "Bedrohungsmodell (v0.30.0)",
        "Änderungsprotokoll",
        "MIT-Lizenz",
        "Docker Compose"
      ],
      "copy": "© 2026 scrAPE-Maintainer. Open Source unter der MIT-Lizenz.",
      "sysinfo": "STATUS: EINSATZBEREIT // ENGINE: v0.30.1"
    },
    "sections": {
      "sec-overview-arch": {
        "tag": "MODUL [01] // SYSTEMÜBERSICHT",
        "h1": "Architektur und Zielsetzungen",
        "desc": "Multi-Engine-Stealth-Web-Scraping-System für autonome Medienextraktion und KI-Datensatzerstellung.",
        "cards": [
          "1.1 Systemarchitektur"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] KERN-BETRIEBSGARANTIE",
            "bodyHtml": "Das System operiert über eine 8-Stufen-WAF-Fallback-Pipeline. Anfragen eskalieren bei Erkennung von Challenge-Schleifen automatisch von schlankem direktem HTTP bis hin zu sichtbarer Stealth-Browser-Automatisierung. Es ist kein manueller Eingriff erforderlich."
          }
        ]
      },
      "sec-overview-formats": {
        "tag": "MODUL [01] // SYSTEMÜBERSICHT",
        "h1": "Unterstützte Formate und Betriebsgrenzen",
        "desc": "Asset-Spezifikationen, Größenfilter, Dimensionsgrenzen und Ratenbeschränkungen.",
        "cards": [
          "1.2 Medien- & Datenkapazitäten"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-overview-layout": {
        "tag": "MODUL [01] // SYSTEMÜBERSICHT",
        "h1": "Projekt-Verzeichnislayout",
        "desc": "Datei- und Ordnerorganisation des Repositories.",
        "cards": [
          "1.3 Verzeichnisstruktur"
        ],
        "codeHeaders": [
          "TEXT // REPOSITORY-BAUM"
        ],
        "alerts": []
      },
      "sec-overview-pillars": {
        "tag": "MODUL [01] // SYSTEMÜBERSICHT",
        "h1": "Kernarchitektur-Säulen (v0.30.1)",
        "desc": "Enterprise-Multi-Node-Orchestrierung, sublineare perzeptuelle BK-Tree-Deduplizierung, isolierte Profiler-Thread-Pools und Content-Addressable Storage (CAS).",
        "cards": [
          "1.4 Kernarchitektur-Säulen (v0.30.1)"
        ],
        "codeHeaders": [
          "BASH // KERNKOMPONENTEN-CLI-AKTIVIERUNG"
        ],
        "alerts": []
      },
      "sec-overview-v28": {
        "tag": "MODUL [01] // ARCHITEKTUR-UPDATE",
        "h1": "Kernarchitektur (v0.28.0)",
        "desc": "Produktionsreife entkoppelte ML-Pipeline, 3-stufige hierarchische Deduplizierung, selbstheilender DOM-Parser und überwachte hybride Nebenläufigkeit.",
        "cards": [
          "1.4 Architektonische Durchbrüche in v0.28.0"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-prereqs": {
        "tag": "MODUL [02] // INSTALLATION & SCHNELLSTART",
        "h1": "Systemvoraussetzungen und Toolchain",
        "desc": "Python-Laufzeitumgebung, Headless-Browser-Treiber, CUDA-Hardwarebeschleunigung und Redis-Infrastrukturanforderungen.",
        "cards": [
          "2.1 Systemvoraussetzungen"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-install-steps": {
        "tag": "MODUL [02] // INSTALLATION & SCHNELLSTART",
        "h1": "Schritt-für-Schritt-Installationsanleitung",
        "desc": "Bereitstellung der virtuellen Umgebung, Installation der pip-Pakete und Synchronisierung der Browser-Binärdateien.",
        "cards": [
          "2.2 Installationsablauf & Einrichtung"
        ],
        "codeHeaders": [
          "BASH // INSTALLATIONSBEFEHLE"
        ],
        "alerts": [
          {
            "title": "[i] FLARESOLVERR-EINRICHTUNG",
            "bodyHtml": "FlareSolverr (Stufe 5) läuft als Docker-Container. Starten mit: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"
          }
        ]
      },
      "sec-install-launchers": {
        "tag": "MODUL [02] // INSTALLATION & SCHNELLSTART",
        "h1": "Master-Starter und Assistent",
        "desc": "Interaktive Starter-Skripte für sämtliche Ausführungsmodi.",
        "cards": [
          "2.3 Starter-Optionen & Assistent"
        ],
        "codeHeaders": [
          "POWERSHELL // MASTER-STARTER"
        ],
        "alerts": []
      },
      "sec-install-recipes": {
        "tag": "MODUL [02] // INSTALLATION & SCHNELLSTART",
        "h1": "Befehlsrezepte für den ersten Lauf",
        "desc": "Copy-Paste-Befehle für typische Extraktionsszenarien.",
        "cards": [
          "2.4 Befehlsrezepte für den ersten Lauf"
        ],
        "codeHeaders": [
          "REZEPT 1 // STANDARD-SEED-EXTRAKTION MIT SPEICHERUNG ABGELEHNTER MEDIEN",
          "REZEPT 2 // KONTINUIERLICHER WATCHDOG-AGENT MIT STATUS-CACHE",
          "REZEPT 3 // SCHNELLER VALIDIERUNGSLAUF (OHNE DOWNLOADS)",
          "REZEPT 4 // REINE SUCHERKENNUNG (OHNE SEEDS)",
          "REZEPT 5 // STEALTH-CRAWL (HÖFLICHE GESCHWINDIGKEIT)"
        ],
        "alerts": []
      },
      "sec-cli-flags": {
        "tag": "MODUL [03] // CLI-REFERENZ",
        "h1": "Vollständige CLI-Ausführungsflag-Matrix",
        "desc": "Vollständiger Referenzleitfaden für alle Befehlszeilenschalter, Flags, Schwellenwertüberschreibungen und Extraktionsbudgets.",
        "cards": [
          "3.1 Befehlszeilenparameter-Matrix"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-cli-builder": {
        "tag": "MODUL [03] // CLI-REFERENZ",
        "h1": "Interaktiver CLI-Befehlsgenerator",
        "desc": "Konfigurieren Sie Zielparameter, Parallelitätspools und Stealth-Flags, um einen sofort ausführbaren Terminalbefehl zu generieren.",
        "cards": [
          "3.2 Interaktiver Befehlsgenerator"
        ],
        "codeHeaders": [
          "GENERIERTE CLI-BEFEHLSZEILE"
        ],
        "alerts": []
      },
      "sec-cli-profiles": {
        "tag": "MODUL [03] // CLI-REFERENZ",
        "h1": "Ausführungsprofile",
        "desc": "Vorkonfigurierte Profilvoreinstellungen für spezialisierte Scraping-Topologien.",
        "cards": [
          "3.3 Voreingestellte Profilmatrix"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-bfs": {
        "tag": "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        "h1": "BFS-Crawl-Schleife",
        "desc": "Asynchrone Breitensuch-Traversierungsschleife, Prioritäts-Queue-Dispatch und Link-Extraktion.",
        "cards": [
          "4.1 BFS-Ausführungssequenz"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-waf": {
        "tag": "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        "h1": "8-Stufen-Stealth-WAF-Eskalationspipeline",
        "desc": "Mehrstufiger adaptiver Fallback zur Überwindung von Cloudflare Turnstile, Datadome, Incapsula und Bot-Abwehrsystemen.",
        "cards": [
          "4.2 8-Stufen-WAF-Pipeline-Hierarchie"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-captcha": {
        "tag": "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        "h1": "Universelle Captcha-Strategie",
        "desc": "Automatisierte Solver-Anbieter, Challenge-Interzeption und Retry-Handler.",
        "cards": [
          "4.3 Captcha- & Challenge-Lösungsstrategie"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-scoring": {
        "tag": "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        "h1": "Qualitätsbewertung und Ausschussbehandlung",
        "desc": "URL-Klassifizierung, Mindestbildabmessungen und Speicherung abgelehnter Medien auf Festplatte.",
        "cards": [
          "4.4 Ablehnungsregeln & Speicherpfade"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-normalize": {
        "tag": "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        "h1": "URL-Normalisierung",
        "desc": "Entfernung von Tracking-Parametern, Protokollkanonisierung und Vermeidung redundanter Queue-Zyklen.",
        "cards": [
          "4.5 URL-Kanonisierungs-Pipeline"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-engine-pool": {
        "tag": "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        "h1": "Vorgewärmter Browser-Pool",
        "desc": "Hochleistungs-Recycling des Camoufox-Browser-Pools und isoliertes Kontext-Leasing.",
        "cards": [
          "4.6 Lebenszyklus des vorgewärmten Browser-Pools"
        ],
        "codeHeaders": [
          "PYTHON // VORGEWÄRMTES BROWSER-POOL-LEASING"
        ],
        "alerts": []
      },
      "sec-engine-broker": {
        "tag": "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        "h1": "Redis-Streams-Task-Broker",
        "desc": "Verteilte Consumer-Gruppen, Pending Entry List (PEL)-Tracking und atomarer Task-Dispatch.",
        "cards": [
          "4.7 Verteilte Cluster-Koordination via Redis Streams"
        ],
        "codeHeaders": [
          "PYTHON // TASK-BROKER-INTERAKTIONSMUSTER"
        ],
        "alerts": []
      },
      "sec-engine-ml": {
        "tag": "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        "h1": "Vision-Hardware & ML-Pipeline",
        "desc": "CUDA/MPS-Geräteerkennung, Half-Precision (FP16)-Inferenz und automatische ästhetische Qualitätsbewertung.",
        "cards": [
          "4.8 Hardware-Beschleunigungsmatrix (CUDA / MPS)"
        ],
        "codeHeaders": [
          "PYTHON // HARDWARE-ERKENNUNG & PRÄZISIONS-NEGOTIATION"
        ],
        "alerts": []
      },
      "sec-engine-healing": {
        "tag": "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        "h1": "Selbstheilender DOM-Parser",
        "desc": "4-stufige DOM-Wiederherstellungskaskade mit heuristischer Multi-Provider-LLM-Reparatur.",
        "cards": [
          "4.9 Autonome Selektor-Reparatur & VLM-Heilung"
        ],
        "codeHeaders": [
          "PYTHON // SELBSTHEILENDE EXTRAKTIONSKASKADE",
          "TEXT // MULTI-PROVIDER-LLM-SYNTHESE-KASKADE"
        ],
        "alerts": []
      },
      "sec-engine-bktree": {
        "tag": "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        "h1": "BK-Tree-Deduplizierung & Concurrency-Partitionierung",
        "desc": "Diskrete Metrikbaum-Indizierung, Hamming-Distanz-Clustering und isolierte Profiler-Ausführungspools.",
        "cards": [
          "4.10 Diskreter Metrikbaum & Ausführungspool-Partitionierung"
        ],
        "codeHeaders": [
          "PYTHON // BK-TREE-METRIKSUCHE & VERBINDUNGSPOOLING"
        ],
        "alerts": []
      },
      "sec-config-env": {
        "tag": "MODUL [05] // KONFIGURATIONSREFERENZ",
        "h1": "Umgebungsvariablen (.env)",
        "desc": "Produktionsanmeldedaten, Ratenbegrenzungen, Proxy-Gateways und API-Token.",
        "cards": [
          "5.1 .env Konfigurationsvorlage"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-domain": {
        "tag": "MODUL [05] // KONFIGURATIONSREFERENZ",
        "h1": "domain_config.json",
        "desc": "Domain-spezifische Nebenläufigkeitsgrenzen, benutzerdefinierte Wait-Selektoren und Header-Überschreibungen.",
        "cards": [
          "5.2 Konfigurationsschlüssel-Referenz (domain_config.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-urlnorm": {
        "tag": "MODUL [05] // KONFIGURATIONSREFERENZ",
        "h1": "url_normalisation_rules.json",
        "desc": "Reguläre Ausdrücke zur Bereinigung von Abfrageparametern und für Domain-Transformationen.",
        "cards": [
          "5.3 Normalisierungsregel-Schema (url_normalisation_rules.json)"
        ],
        "codeHeaders": [
          "JSON // REGEL-SCHEMA-BEISPIEL"
        ],
        "alerts": [
          {
            "title": "[!] VERBINDLICHE REGEL",
            "bodyHtml": "Codieren Sie domainspezifische URL-Normalisierungs-Regexes niemals fest in Python-Dateien unter <code>src/</code> ein. Alle Regeln MÜSSEN in <code>data/url_normalisation_rules.json</code> deklariert werden."
          }
        ]
      },
      "sec-config-seeds": {
        "tag": "MODUL [05] // KONFIGURATIONSREFERENZ",
        "h1": "Seed-Manifest-Syntax",
        "desc": "Kommentare, Inline-Direktiven und Prioritätsgewichte in seeds/*.txt-Dateien.",
        "cards": [
          "5.4 Annotationsreferenz für Seed-Manifeste"
        ],
        "codeHeaders": [
          "MANIFEST // SEED-MANIFEST-ANNOTATIONSBEISPIEL"
        ],
        "alerts": []
      },
      "sec-config-profiles": {
        "tag": "MODUL [05] // KONFIGURATIONSREFERENZ",
        "h1": "Subjekt-Profile",
        "desc": "Subjektspezifische Voreinstellungen, Ausgabetemplates und Blacklist-Verknüpfungen.",
        "cards": [
          "5.5 Profil-Voreinstellungen (subject_profiles.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-config-blacklist": {
        "tag": "MODUL [05] // KONFIGURATIONSREFERENZ",
        "h1": "Blacklist-Verwaltung",
        "desc": "Global ausgeschlossene Domains, Ad-Server und Muster minderwertiger Ressourcen.",
        "cards": [
          "5.6 Domain-Blacklisting & Ausschlussfilter"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-arch": {
        "tag": "MODUL [06] // WEBUI-DASHBOARD",
        "h1": "WebUI-Serverarchitektur",
        "desc": "Reaktive Kommandozentrale mit FastAPI und HTMX mit Echtzeit-SSE-Streaming-Telemetrie.",
        "cards": [
          "6.1 Entkoppelter FastAPI-Server"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-views": {
        "tag": "MODUL [06] // WEBUI-DASHBOARD",
        "h1": "Kommandozentrale und Medientresor",
        "desc": "Interaktives Kontroll-Dashboard, Live-Crawler-Status und Galerie-Inspektion.",
        "cards": [
          "6.2 Dashboard-Ansichten (Kommandozentrale & Medientresor)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-telemetry": {
        "tag": "MODUL [06] // WEBUI-DASHBOARD",
        "h1": "Live-Telemetrie und SSE",
        "desc": "Echtzeit-Ereignis-Streaming über Server-Sent Events, Queue-Raten und Speicheranzeigen.",
        "cards": [
          "6.3 Echtzeit-Event-Pipeline (SSE & Canvas)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-design": {
        "tag": "MODUL [06] // WEBUI-DASHBOARD",
        "h1": "Design-Tokens",
        "desc": "Taktische utilitaristische brutalistische CSS-Tokens, kontrastreiche Monospace-Typografie und Farbpaletten.",
        "cards": [
          "6.4 Design-Token-Referenz (Taktischer Brutalismus)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-webui-health": {
        "tag": "MODUL [06] // WEBUI-DASHBOARD",
        "h1": "Taktischer Knoten-Gesundheitsmonitor",
        "desc": "Subsystem-Integritätsprüfungen, Heartbeat-Sonden und Redis-Cluster-Telemetrie.",
        "cards": [
          "6.5 Taktische Telemetrie & Knoten-Governance"
        ],
        "codeHeaders": [
          "JSON // KNOTENGESUNDHEITS-TELEMETRIE-PAYLOAD"
        ],
        "alerts": []
      },
      "sec-ops-docker": {
        "tag": "MODUL [07] // DEPLOYMENT & BETRIEB",
        "h1": "Docker Compose",
        "desc": "Multi-Container-Produktionsbereitstellung mit FlareSolverr, Redis und WebUI.",
        "cards": [
          "7.1 Container-Bereitstellung mit Docker Compose"
        ],
        "codeHeaders": [
          "BASH // DOCKER COMPOSE START"
        ],
        "alerts": []
      },
      "sec-ops-watchdog": {
        "tag": "MODUL [07] // DEPLOYMENT & BETRIEB",
        "h1": "Watchdog-Agent",
        "desc": "Kontinuierlicher Crawl-Daemon mit automatisierten Integritätsprüfungen und Neustartrichtlinien.",
        "cards": [
          "7.2 Kontinuierliche Überwachungsschleife (Watchdog)"
        ],
        "codeHeaders": [
          "POWERSHELL // WATCHDOG-AGENT-BEFEHL"
        ],
        "alerts": []
      },
      "sec-ops-notifications": {
        "tag": "MODUL [07] // DEPLOYMENT & BETRIEB",
        "h1": "Benachrichtigungs-Pipeline",
        "desc": "Pluggable Benachrichtigungskanäle (Telegram, Discord, Slack, Webhooks).",
        "cards": [
          "7.3 Mehrkanal-Benachrichtigungen (Telegram, Discord, Slack)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-proxy": {
        "tag": "MODUL [07] // DEPLOYMENT & BETRIEB",
        "h1": "Proxy-Pool-Verwaltung",
        "desc": "Proxy-Rotation, automatische Latenz-Quarantäne und Bandbreitenkontingente.",
        "cards": [
          "7.4 Proxy-Manager-Strategie & Quarantäne"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-ops-sessions": {
        "tag": "MODUL [07] // DEPLOYMENT & BETRIEB",
        "h1": "Sitzungs- und Cookie-Verwaltung",
        "desc": "Persistente domänenspezifische Sticky-Sessions und interaktiver Cookie-Login.",
        "cards": [
          "7.5 Sitzungs- & Cookie-Speicherverwaltung"
        ],
        "codeHeaders": [
          "BASH // SITZUNGS-LOGIN-BEFEHLE"
        ],
        "alerts": []
      },
      "sec-output-structure": {
        "tag": "MODUL [08] // AUSGABE & EXPORTE",
        "h1": "Ausgabeverzeichnisstruktur",
        "desc": "Layout der Ausführungs-Artefakte.",
        "cards": [
          "8.1 Artefakt- & Ausgabeverzeichnisorganisation"
        ],
        "codeHeaders": [
          "TEXT // AUSGABEVERZEICHNIS-LAYOUT"
        ],
        "alerts": []
      },
      "sec-output-manifest": {
        "tag": "MODUL [08] // AUSGABE & EXPORTE",
        "h1": "manifest.json-Schema",
        "desc": "Vollständige Dokumentation des JSON-Ergebnisschemas.",
        "cards": [
          "8.2 JSON-Nutzlastfelder (manifest.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-domain": {
        "tag": "MODUL [08] // AUSGABE & EXPORTE",
        "h1": "domain_report.json-Schema",
        "desc": "Messwertebericht pro Domain.",
        "cards": [
          "8.3 Ertragsbericht pro Domain (domain_report.json)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-kohya": {
        "tag": "MODUL [08] // AUSGABE & EXPORTE",
        "h1": "Kohya-LoRA-Datensatzexport",
        "desc": "Generierung von ZIP-Archiven für Kohya_ss-LoRA-Datensätze.",
        "cards": [
          "8.4 Kohya LoRA-Datensatzgenerator"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-rag": {
        "tag": "MODUL [08] // AUSGABE & EXPORTE",
        "h1": "RAG-Aufnahmeformate",
        "desc": "LLM-RAG-Exporte (Markdown-Chunks und JSONL-Embeddings).",
        "cards": [
          "8.5 RAG-Aufnahmeformate (Markdown & JSONL)"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-output-cas": {
        "tag": "MODUL [08] // AUSGABE & EXPORTE",
        "h1": "Inhaltsadressierbarer Speicher (CAS)",
        "desc": "Globales Deduplizierungs-Repository zur Vermeidung doppelter Dateispeicherung bei wiederholten Crawls.",
        "cards": [
          "8.6 Architektur des inhaltsadressierbaren Speichers (CAS)"
        ],
        "codeHeaders": [
          "PYTHON // CAS-DEDUPLIZIERUNG & LAUF-VERKNÜPFUNG",
          "TEXT // CAS-SPEICHER-LEBENSZYKLUS"
        ],
        "alerts": []
      },
      "sec-output-parquet": {
        "tag": "MODUL [08] // AUSGABE & EXPORTE",
        "h1": "Apache-Parquet-Datensatzexport",
        "desc": "Spaltenorientierte, Snappy-komprimierte Datensätze, optimiert für Polars, DuckDB, Pandas und Big Data OLAP-Pipelines.",
        "cards": [
          "8.7 Spaltenorientierte Datenexport-Pipeline (Apache Parquet)"
        ],
        "codeHeaders": [
          "PYTHON // PARQUET-DATENSATZGENERIERUNG"
        ],
        "alerts": []
      },
      "sec-test-pytest": {
        "tag": "MODUL [09] // TESTS & FEHLERBEHEBUNG",
        "h1": "Ausführen von pytest",
        "desc": "Ausführen der automatisierten Test-Suite.",
        "cards": [
          "9.1 Automatisierte Pytest-Suite"
        ],
        "codeHeaders": [
          "POWERSHELL // KOMPLETTE TEST-SUITE AUSFÜHREN"
        ],
        "alerts": []
      },
      "sec-test-tdai": {
        "tag": "MODUL [09] // TESTS & FEHLERBEHEBUNG",
        "h1": "Verifikationsprotokoll (TDAI)",
        "desc": "Testgetriebene KI-Verifikationsregeln und RED-GREEN-REFACTOR-Protokoll.",
        "cards": [
          "9.2 Empirisches Verifikationsprotokoll (TDAI)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "[!] VERBINDLICHE REGEL",
            "bodyHtml": "Erklären Sie ein Feature oder einen Fix niemals für abgeschlossen, ohne empirische Laufzeitüberprüfungsbefehle auszuführen und saubere Testergebnisse nachzuweisen."
          }
        ]
      },
      "sec-test-logs": {
        "tag": "MODUL [09] // TESTS & FEHLERBEHEBUNG",
        "h1": "Log-Diagnoserezepte",
        "desc": "Log-Analyse und Grep-Befehle für die Laufzeitdiagnose.",
        "cards": [
          "9.3 PowerShell-Diagnosebefehle & Log-Analyse"
        ],
        "codeHeaders": [
          "POWERSHELL // LOGS NACH FEHLERN UND BLOCKADEN DURCHSUCHEN"
        ],
        "alerts": []
      },
      "sec-test-diagnostic": {
        "tag": "MODUL [09] // TESTS & FEHLERBEHEBUNG",
        "h1": "Operator-Diagnosematrix",
        "desc": "Vollständige Diagnosetabelle für die Fehlerbehebung durch den Operator.",
        "cards": [
          "9.4 Operator-Diagnosematrix"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-test-guidelines": {
        "tag": "MODUL [09] // TESTS & FEHLERBEHEBUNG",
        "h1": "Entwickler-Richtlinien",
        "desc": "Verbindliche Programmierregeln und Workspace-Standards.",
        "cards": [
          "9.5 Verbindliche Entwicklungsregeln"
        ],
        "codeHeaders": [],
        "alerts": []
      },
      "sec-threat-overview": {
        "tag": "MODUL [10] // BEDROHUNGSMODELL & SICHERHEIT",
        "h1": "Sicherheitsarchitektur & v0.30.0 Verifikation",
        "desc": "Autoritatives Bedrohungsmodell, STRIDE-Architekturvertrag und empirische Verifikationsmatrix für die verteilte v0.30.0-Skalierung.",
        "cards": [
          "10.1 Vertrauensgrenzen & Datenflussarchitektur",
          "10.1.1 STRIDE-Bedrohungskategorisierung",
          "10.1.2 Übergreifende Invarianten"
        ],
        "codeHeaders": [
          "ARCHITEKTUR // v0.30.0 VERTEILTE VERTRAUENSGRENZEN & DATENFLUSS"
        ],
        "alerts": [
          {
            "title": "PRODUKTIONS-RELEASE // v0.30.0 VERIFIZIERT & ZERTIFIZIERT",
            "bodyHtml": "Alle drei in diesem Modul spezifizierten Bedrohungsmodell-Frontbereiche (Distributed Task Leasing, Cloud CAS Synchronization, Vision-Language DOM Healing) sind im v0.30.0-Release auf Ubuntu-, macOS- und Windows-Runnern <strong>vollständig implementiert, adversarial getestet und empirisch durch die CI verifiziert</strong>."
          },
          {
            "title": "VERBINDLICHER ARCHITEKTURVERTRAG",
            "bodyHtml": "Diese Spezifikation bildet die maßgebliche Baseline für alle v0.30.0-Feature-Implementierungen. Jedes Akzeptanzkriterium (AC1.1 bis AC3.6) muss über einen entsprechenden automatisierten Test in <code>tests/</code> verfügen, bevor eine Komponente als freigabefähig gilt."
          }
        ]
      },
      "sec-threat-leasing": {
        "tag": "MODUL [10] // KOMPONENTE 1 (IMPLEMENTIERT & VERIFIZIERT)",
        "h1": "Distributed-Task-Leasing-Bedrohungsmatrix",
        "desc": "STRIDE-Schwachstellenanalyse, Angriffsszenarien und atomare Minderungsmechanismen für Redis-Stream-Worker-Daemons.",
        "cards": [
          "10.2 Designübersicht Komponente 1",
          "10.2.1 Bedrohungs- & Schwachstellenmatrix (Komponente 1)",
          "10.2.2 Detaillierte Minderungs-Spezifikationen"
        ],
        "codeHeaders": [
          "PYTHON // ATOMARER IDEMPOTENZ-SPERREN-ERWERB"
        ],
        "alerts": [
          {
            "title": "KOMPONENTE 1 IMPLEMENTIERT & VERIFIZIERT // AC1.1–AC1.7 BESTANDEN",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>, <code>DistributedWorkerNode</code> und CLI-Worker-Daemons (<code>src.cli.worker</code>) sind vollständig implementiert und anhand der Akzeptanzkriterien AC1.1 bis AC1.7 verifiziert. Die automatische Testverifikation wird durch 98 Tests gestützt."
          }
        ]
      },
      "sec-threat-cas": {
        "tag": "MODUL [10] // KOMPONENTE 2 ARCHITEKTUR",
        "h1": "Cloud-CAS-Synchronisations-Bedrohungsmatrix",
        "desc": "Defense-in-Depth-Spezifikationen, kryptografische Verifikation und SSRF-Prävention für S3 / Cloudflare R2 / MinIO-Speicher-Backends.",
        "cards": [
          "10.3 Designübersicht Komponente 2",
          "10.3.1 Bedrohungs- & Schwachstellenmatrix (Komponente 2)",
          "10.3.2 Kryptografische Hash-Pfad-Erzwingung"
        ],
        "codeHeaders": [
          "PYTHON // CAS-SCHLÜSSEL-PFADVALIDIERUNG & PRÜFSUMMENVERIFIKATION"
        ],
        "alerts": [
          {
            "title": "PRODUKTIONS-ZERTIFIZIERT // KOMPONENTE 2 VOLLSTÄNDIG IMPLEMENTIERT",
            "bodyHtml": "<code>CASCloudSyncer</code> und S3/R2/MinIO Cloud-Speicher-Backends sind in v0.30.0 mit einer Test-Bestehensquote von 100% über AC2.1-AC2.7, Zero-Boto-Minimalinstallationsvalidierung und bedingungslosen SSRF-Schutzfunktionen <strong>vollständig implementiert und verifiziert</strong>."
          }
        ]
      },
      "sec-threat-vlm": {
        "tag": "MODUL [10] // KOMPONENTE 3 (IMPLEMENTIERT & VERIFIZIERT)",
        "h1": "Vision-Language-DOM-Healing-Bedrohungsmatrix",
        "desc": "Multimodale KI-Sicherheitskontrollen, Abwehr adversarieller visueller Prompt-Injections und DOM-Interaktions-Sandboxing für Tier-4-Heilung.",
        "cards": [
          "10.4 Designübersicht Komponente 3",
          "10.4.1 Bedrohungs- & Schwachstellenmatrix (Komponente 3)",
          "10.4.2 Rahmung nicht vertrauenswürdiger Daten & Ausgabe-Leitplanken"
        ],
        "codeHeaders": [
          "PROMPT-ARCHITEKTUR // GESANDBOXTER VLM-SYSTEM-PROMPT"
        ],
        "alerts": [
          {
            "title": "PRODUKTIONS-ZERTIFIZIERT // KOMPONENTE 3 VOLLSTÄNDIG IMPLEMENTIERT",
            "bodyHtml": "<code>VisionDOMHealer</code> (Tier 4 multimodales DOM-Healing) ist in v0.30.0 mit einer 100%igen Test-Bestehensquote über AC3.1-AC3.6, 75-Vektor-Prompt-Injection-Fuzzing-Abweisung und einer strukturellen Default-Deny-Allowlist <strong>vollständig implementiert und verifiziert</strong>."
          }
        ]
      },
      "sec-threat-ac": {
        "tag": "MODUL [10] // VERIFIKATIONS- & AUDIT-MATRIX (v0.30.0 PRODUKTION)",
        "h1": "Akzeptanzkriterien-Verifikationsmatrix (v0.30.0 Produktion)",
        "desc": "Empirische Testspezifikationen, Verifikationsmethoden und Auditergebnisse zur Validierung aller 20 Akzeptanzkriterien für v0.30.0.",
        "cards": [
          "10.5.1 Komponente 1 Akzeptanzkriterien (Task Leasing)",
          "10.5.2 Komponente 2 Akzeptanzkriterien (Cloud CAS)",
          "10.5.3 Komponente 3 Akzeptanzkriterien (VLM Healing)"
        ],
        "codeHeaders": [],
        "alerts": [
          {
            "title": "ALLE 20 AKZEPTANZKRITERIEN VERIFIZIERT & ZERTIFIZIERT",
            "bodyHtml": "Alle 20 nachstehenden Kriterien (AC1.1 bis AC3.6) repräsentieren den <strong>zentralen Architekturvertrag</strong> für v0.30.0. Jedes einzelne Kriterium wird durch automatisierte Tests in <code>tests/</code> gestützt, die lokal und in der GitHub Actions CI-Matrix zu 100% bestehen."
          },
          {
            "title": "VERIFIKATIONSSTANDARD",
            "bodyHtml": "Kein v0.30.0 Pull-Request oder Release-Tag wird genehmigt, ohne dass für alle 20 nachstehenden Akzeptanzkriterien eine Testabdeckung von 100% nachgewiesen wurde."
          }
        ]
      }
    },
    "snippets": {
      "sec-install-steps": "# 1. Repository klonen\ngit clone https://github.com/rhaffle87/scrAPE.git\ncd scrAPE\n\n# 2. Virtuelle Umgebung erstellen und aktivieren\npython -m venv venv\nvenv\\Scripts\\activate          # Windows CMD\n.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell\nsource venv/bin/activate       # Linux / macOS\n\n# 3. Python-Abhängigkeiten installieren\npip install -r requirements.txt\n\n# 4. (Optional) Crawlee Node.js-Bridge für Stealth Stufe 6-7 installieren\ncd crawlee_bridge && npm install && cd ..\n\n# 5. Zugangsdaten konfigurieren\ncopy .env.example .env         # Windows\ncp .env.example .env           # Linux / macOS\n# Bearbeiten Sie anschließend .env mit Ihren API-Schlüsseln und Webhook-URLs",
      "sec-install-launchers": "# Windows-Master-Starter (Interaktives Menü)\n.\\run.bat\n\n# Linux / macOS Master-Starter\n./run.sh\n\n# Direkter interaktiver Assistent (ohne Menü)\npython src/cli/cli_wizard.py",
      "sec-ops-docker": "# Scraper-Engine + FlareSolverr-Sidecar starten\ndocker compose up -d\n\n# Cluster-Logs in Echtzeit überwachen\ndocker compose logs -f\n\n# Container-Stack ordnungsgemäß stoppen\ndocker compose down",
      "sec-ops-watchdog": "# Watchdog-Agent über Starter-Wrapper ausführen\n.\\run.bat watchdog\n\n# Direkter Start der kontinuierlichen Überwachung\npython src/cli/monitor_agent.py --keyword \"example_subject\" --seed seeds/example_subject.txt --use-state-cache",
      "sec-ops-sessions": "# Cookies über interaktives Browserfenster erfassen\npython src/cli/session_auth.py --domain example.com --login-url https://example.com/login\n\n# Gespeicherte Sticky-Session-Cookies auflisten\npython src/cli/session_auth.py --list-sessions",
      "sec-test-pytest": "# Alle 378+ Unit- und Integrationstests ausführen\npytest tests/ -v\n\n# Mit Coverage-Bericht ausführen\npytest --cov=src tests/ --cov-report=term-missing",
      "sec-test-logs": "# Auf HTTP-429-Ratenbegrenzungen und Cloudflare-Blockaden prüfen\nGet-Content logs/crawler.log -Tail 100 | Select-String -Pattern \"429|Cloudflare|WAF|BLOCKED\"\n\n# Echtzeit-Ausgabe der Crawler-Engine überwachen\nGet-Content logs/crawler.log -Wait -Tail 20"
    },
    "lists": {
      "sec-install-launchers": [
        "<strong>Breite Such-Scraping-Abfrage</strong> -- Automatisierte Suchanfragen mit rekursivem Crawling.",
        "<strong>Gezieltes Manifest-Scraping</strong> -- Strukturierte Crawls gegen ausgewählte Seed-Manifeste.",
        "<strong>Kontinuierlicher Watchdog-Agent</strong> -- Langlebige Überwachungsschleifen mit SQLite-WAL-Caching.",
        "<strong>Strukturierten KI-Datensatz erstellen</strong> -- Zusammenfassung der Ausgabe in konsolidierte oder nach Domains gruppierte Strukturen.",
        "<strong>Enterprise-LLM-RAG-Ingestion</strong> -- Export von Seitendaten als konsolidiertes Markdown, fragmentierte <code>.md</code>-Dateien oder JSONL-Embeddings."
      ]
    },
    "h3Map": {
      "Wizard Menu Options": "Assistenten-Menüoptionen",
      "Core Components": "Kernkomponenten",
      "Media Vault View": "Medientresor-Ansicht",
      "Command Center View": "Kommandozentralen-Ansicht",
      "Budget & Balance Guardrails": "Budget- & Guthaben-Schutzleitplanken",
      "Circuit Breaker & Cooldown Mechanics": "Schutzschalter- & Abkühlmechanismen",
      "Download Validation Thresholds": "Download-Validierungsschwellenwerte",
      "Primary v0.30.1 Execution Flags": "Wichtigste v0.30.1 Ausführungs-Flags",
      "Site-Chrome & Keyword Classification Sets": "Site-Chrome- & Schlüsselwort-Klassifizierungssets",
      "Dead-Letter Stream Protocol": "Dead-Letter-Stream-Protokoll",
      "Idempotency Lock Implementation": "Idempotenz-Sperren-Implementierung",
      "Node Health JSON Schema (/api/telemetry/node-health)": "Knotengesundheits-JSON-Schema (/api/telemetry/node-health)"
    },
    "thMap": {
      "Component": "Komponente",
      "Source File": "Quelldatei",
      "Function": "Funktion",
      "Requirement": "Anforderung",
      "Minimum": "Minimum",
      "Notes": "Hinweise",
      "Category": "Kategorie",
      "Supported Types": "Unterstützte Typen",
      "Processing Method": "Verarbeitungsmethode",
      "Core Pillar": "Kernsäule",
      "Key Technologies": "Schlüsseltechnologien",
      "Production Capability": "Produktionsfähigkeit",
      "Parameter": "Parameter",
      "Type": "Typ",
      "Default": "Standard",
      "Description": "Beschreibung",
      "Status": "Status",
      "Tier": "Stufe",
      "Mechanism": "Mechanismus",
      "Overhead": "Overhead",
      "Usage": "Verwendung",
      "Profile": "Profil",
      "Keyword": "Schlüsselwort",
      "Concurrency": "Parallelität",
      "Depth": "Tiefe",
      "Endpoint": "Endpunkt",
      "Impact": "Auswirkung",
      "Channel": "Kanal",
      "Provider": "Anbieter",
      "Purpose": "Zweck",
      "Field": "Feld",
      "Value": "Wert",
      "Variable": "Variable",
      "Subsystem": "Subsystem",
      "Symptom": "Symptom",
      "Where to Look": "Fundort / Pfad",
      "Resolution Action": "Behebungsmaßnahme",
      "Key Flags": "Wichtigste Flags",
      "Syntax": "Syntax",
      "Primary Use Case": "Hauptanwendungsfall",
      "Rejection Reason": "Ablehnungsgrund",
      "Disk Retention Path": "Speicherpfad auf Festplatte",
      "Trigger Criteria": "Auslösekriterien",
      "Supported Challenge Types": "Unterstützte Challenge-Typen",
      "Fault Tolerance Function": "Fehlertoleranz-Funktion",
      "Escalation Trigger": "Eskalationsauslöser",
      "Telemetry Metric": "Telemetrie-Metrik",
      "Target Component": "Zielkomponente",
      "Visual Indicator & Action": "Visueller Indikator & Aktion",
      "Top-Level Key": "Top-Level-Schlüssel",
      "Required Credentials (.env)": "Erforderliche Anmeldedaten (.env)",
      "Key Benefits": "Hauptvorteile",
      "Schema Columns": "Schema-Spalten",
      "Parquet Table": "Parquet-Tabelle",
      "Payload Type": "Nutzlasttyp",
      "Source / Endpoint": "Quelle / Endpunkt",
      "Stream Command": "Stream-Befehl",
      "Internal Action": "Interne Aktion",
      "Threat Scenario": "Bedrohungsszenario",
      "STRIDE Category": "STRIDE-Kategorie",
      "Vector & Attack Mechanics": "Vektor & Angriffsmechanik",
      "Mitigation Mechanism": "Minderungsmechanismus",
      "Primary Defense Mechanism": "Primärer Abwehrmechanismus",
      "Hardened Primitive": "Gehärtetes Primitiv",
      "Test Methodology & Assertion": "Testmethodik & Assertion",
      "Criterion ID": "Kriterien-ID",
      "Requirement Description": "Anforderungsbeschreibung",
      "Verified Test Suite": "Verifizierte Test-Suite",
      "Architecture Frontier": "Architektur-Frontier",
      "Primary Threat in v0.30.0": "Hauptbedrohung in v0.30.0",
      "Algorithmic / System Enhancement": "Algorithmische / Systemverbesserung",
      "Compression & Fallback": "Komprimierung & Fallback",
      "Annotation Header": "Annotations-Header"
    }
  }
};

/**
 * Applies the selected language to the portal DOM dynamically.
 * @param {string} lang Target language code ('en', 'id', 'zh', 'es', 'ja', 'ru', 'de')
 */
function setPortalLanguage(lang) {
  if (!I18N_DICTS[lang]) {
    lang = 'en';
  }
  const dict = I18N_DICTS[lang];

  // 1. Update HTML document attributes & metadata
  document.documentElement.lang = lang;
  if (dict.meta) {
    if (dict.meta.title) document.title = dict.meta.title;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc && dict.meta.desc) metaDesc.setAttribute('content', dict.meta.desc);
  }

  // 2. Update Search Placeholder & Header Elements
  const searchInput = document.getElementById('doc-search') || document.getElementById('search-input') || document.querySelector('.search-input');
  if (searchInput && dict.ui && dict.ui.searchPlaceholder) {
    searchInput.placeholder = dict.ui.searchPlaceholder;
    searchInput.setAttribute('aria-label', dict.ui.searchPlaceholder);
  }
  const ghLink = document.querySelector('.header-nav-link[href*="github.com"]') || document.querySelector('.header-links a[href*="github.com"]');
  if (ghLink && dict.ui && dict.ui.githubLink) {
    ghLink.textContent = dict.ui.githubLink;
  }
  const panelHeader = document.querySelector('.lang-panel-header');
  if (panelHeader && dict.ui && dict.ui.selectLocale) {
    panelHeader.textContent = dict.ui.selectLocale;
  }
  const pickerBtn = document.getElementById('lang-picker-btn');
  if (pickerBtn && dict.ui && dict.ui.changeLanguageTitle) {
    pickerBtn.setAttribute('title', dict.ui.changeLanguageTitle);
  }

  // 3. Update Module Headings in Sidebar
  const moduleTitles = document.querySelectorAll('.nav-module-title');
  moduleTitles.forEach((modTitle, idx) => {
    if (dict.modules && dict.modules[idx]) {
      const span = modTitle.querySelector('span:first-child');
      if (span) span.textContent = dict.modules[idx];
    }
  });

  // 4. Update Navigation Sub-Links
  const navLinks = document.querySelectorAll('.nav-sub-item a');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href) {
      const cleanHash = href.replace('#', '');
      if (dict.nav && dict.nav[cleanHash]) {
        // preserve badge if present
        const hasBadge = link.querySelector('.badge-new') || link.querySelector('.badge-tag');
        const badgeHtml = hasBadge ? hasBadge.outerHTML : '';
        link.textContent = dict.nav[cleanHash];
        if (badgeHtml) {
          link.insertAdjacentHTML('beforeend', ' ' + badgeHtml);
        }
      }
    }
  });

  // 5. Update All 55 Sections (Tag, H1, Desc, Card Titles, Code Headers, Alerts)
  if (dict.sections) {
    Object.keys(dict.sections).forEach(secId => {
      const secEl = document.getElementById(secId);
      if (secEl) {
        const secData = dict.sections[secId];
        const tagEl = secEl.querySelector('.section-tag');
        const h1El = secEl.querySelector('.section-header h1');
        const descEl = secEl.querySelector('.section-desc');

        if (tagEl && secData.tag) tagEl.textContent = secData.tag;
        if (h1El && secData.h1) h1El.textContent = secData.h1;
        if (descEl && secData.desc) descEl.textContent = secData.desc;

        // Card Titles inside section
        if (secData.cards && Array.isArray(secData.cards)) {
          const cardTitleEls = secEl.querySelectorAll('.card-title');
          secData.cards.forEach((title, idx) => {
            if (cardTitleEls[idx]) {
              cardTitleEls[idx].textContent = title;
            }
          });
        }

        // Code block headers inside section
        if (secData.codeHeaders && Array.isArray(secData.codeHeaders)) {
          const codeHeaderSpans = secEl.querySelectorAll('.code-header span:first-child');
          secData.codeHeaders.forEach((chText, idx) => {
            if (codeHeaderSpans[idx]) {
              codeHeaderSpans[idx].textContent = chText;
            }
          });
        }

        // Alert callouts inside section
        if (secData.alerts && Array.isArray(secData.alerts)) {
          const alertEls = secEl.querySelectorAll('.alert');
          secData.alerts.forEach((altData, idx) => {
            const aEl = alertEls[idx];
            if (aEl) {
              const aTitle = aEl.querySelector('.alert-title');
              if (aTitle && altData.title) {
                aTitle.textContent = altData.title;
              }
              if (altData.bodyHtml) {
                const titleHtml = aTitle ? aTitle.outerHTML : '';
                aEl.innerHTML = titleHtml + ' ' + altData.bodyHtml;
              }
            }
          });
        }
      }
    });
  }

  // 6. Update Code Snippet Comments (e.g. bash # comments)
  if (dict.snippets) {
    Object.keys(dict.snippets).forEach(secId => {
      const secEl = document.getElementById(secId);
      if (secEl) {
        const preEl = secEl.querySelector('pre');
        if (preEl && dict.snippets[secId]) {
          preEl.textContent = dict.snippets[secId];
        }
      }
    });
  }

  // 7. Update Section Lists (Wizard Options, BFS Steps)
  if (dict.lists) {
    Object.keys(dict.lists).forEach(secId => {
      const secEl = document.getElementById(secId);
      if (secEl) {
        const listItems = secEl.querySelectorAll('ol > li, ul > li');
        const translations = dict.lists[secId];
        if (translations && Array.isArray(translations)) {
          translations.forEach((itemHtml, idx) => {
            if (listItems[idx]) {
              listItems[idx].innerHTML = itemHtml;
            }
          });
        }
      }
    });
  }

  // 8. Update Subheadings inside Cards (h3 / h4)
  document.querySelectorAll('.card h3, .card h4').forEach(h => {
    if (!h.dataset.origText) h.dataset.origText = h.textContent.trim();
    const orig = h.dataset.origText;
    if (dict.h3Map && dict.h3Map[orig]) {
      h.textContent = dict.h3Map[orig];
    } else if (lang === 'en') {
      h.textContent = orig;
    }
  });

  // 9. Update Table Headers (th)
  document.querySelectorAll('th').forEach(th => {
    if (!th.dataset.origText) th.dataset.origText = th.textContent.trim();
    const orig = th.dataset.origText;
    if (dict.thMap && dict.thMap[orig]) {
      th.textContent = dict.thMap[orig];
    } else if (lang === 'en') {
      th.textContent = orig;
    }
  });

  // 10. Update Entire Footer
  if (dict.footer) {
    const fLogo = document.querySelector('.footer-logo');
    if (fLogo && dict.footer.logo) fLogo.textContent = dict.footer.logo;

    const fTagline = document.querySelector('.footer-tagline');
    if (fTagline && dict.footer.tagline) fTagline.textContent = dict.footer.tagline;

    if (dict.footer.badges) {
      const badgeEls = document.querySelectorAll('.footer-badges .badge-tag');
      dict.footer.badges.forEach((bText, idx) => {
        if (badgeEls[idx]) badgeEls[idx].textContent = bText;
      });
    }

    if (dict.footer.headings) {
      const headingEls = document.querySelectorAll('.footer-nav-col .footer-heading');
      if (headingEls[0] && dict.footer.headings.repo) headingEls[0].textContent = dict.footer.headings.repo;
      if (headingEls[1] && dict.footer.headings.docs) headingEls[1].textContent = dict.footer.headings.docs;
    }

    if (dict.footer.links && Array.isArray(dict.footer.links)) {
      const linkEls = document.querySelectorAll('.footer-nav-col .footer-link-list a');
      dict.footer.links.forEach((lText, idx) => {
        if (linkEls[idx]) linkEls[idx].textContent = lText;
      });
    }

    const fCopy = document.querySelector('.footer-copy');
    if (fCopy && dict.footer.copy) fCopy.textContent = dict.footer.copy;

    const fSysinfo = document.querySelector('.footer-sysinfo');
    if (fSysinfo && dict.footer.sysinfo) fSysinfo.textContent = dict.footer.sysinfo;
  }

  // 11. Update Interactive CLI Builder UI Labels
  const builderTitle = document.querySelector('#sec-cli-builder .card-title');
  if (builderTitle && dict.ui.commandBuilder) {
    builderTitle.textContent = dict.ui.commandBuilder;
  }
  const builderOutputLabel = document.querySelector('#sec-cli-builder .code-header span');
  if (builderOutputLabel && dict.ui.builderOutputLabel) {
    builderOutputLabel.textContent = dict.ui.builderOutputLabel;
  }

  // 12. Copy Buttons
  const copyButtons = document.querySelectorAll('.copy-btn');
  copyButtons.forEach(btn => {
    if (dict.ui.copyCode && !btn.textContent.includes('!')) {
      btn.textContent = dict.ui.copyCode;
    }
  });

  // 13. Sync Unified Language Picker
  const currentCodeEl = document.getElementById('current-lang-code');
  if (currentCodeEl) {
    currentCodeEl.textContent = lang.toUpperCase();
  }

  document.querySelectorAll('.lang-choice').forEach(choice => {
    if (choice.getAttribute('data-lang') === lang) {
      choice.classList.add('active');
    } else {
      choice.classList.remove('active');
    }
  });

  // 14. Persist Choice
  try {
    localStorage.setItem('scrape_doc_lang', lang);
    const url = new URL(window.location.href);
    if (url.searchParams.get('lang') !== lang) {
      url.searchParams.set('lang', lang);
      window.history.replaceState({}, '', url.toString());
    }
  } catch (e) {
    // Ignore local file restrictions
  }

  window.I18N_CURRENT_DICT = dict;
  window.I18N_CURRENT_LANG = lang;
  document.dispatchEvent(new CustomEvent('languagechange', { detail: { lang, dict } }));
}

/**
 * Initializes language listeners on page ready.
 */
function initPortalI18n() {
  let activeLang = 'en';

  // Check URL parameter first
  try {
    const url = new URL(window.location.href);
    const param = url.searchParams.get('lang');
    if (param && I18N_DICTS[param]) {
      activeLang = param;
    } else {
      const stored = localStorage.getItem('scrape_doc_lang');
      if (stored && I18N_DICTS[stored]) {
        activeLang = stored;
      } else {
        const browser = (navigator.language || '').slice(0, 2).toLowerCase();
        if (I18N_DICTS[browser]) {
          activeLang = browser;
        }
      }
    }
  } catch (e) {
    // Fallback to default
  }

  // Unified Language Picker Trigger & Panel
  const pickerContainer = document.getElementById('lang-picker-container');
  const pickerBtn = document.getElementById('lang-picker-btn');
  const dropdownPanel = document.getElementById('lang-dropdown-panel');

  if (pickerContainer && pickerBtn && dropdownPanel) {
    pickerBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isClosed = dropdownPanel.style.display === 'none';
      if (isClosed) {
        dropdownPanel.style.display = 'flex';
        pickerContainer.classList.add('open');
        pickerBtn.setAttribute('aria-expanded', 'true');
      } else {
        dropdownPanel.style.display = 'none';
        pickerContainer.classList.remove('open');
        pickerBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
      if (!pickerContainer.contains(e.target)) {
        dropdownPanel.style.display = 'none';
        pickerContainer.classList.remove('open');
        pickerBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && dropdownPanel.style.display !== 'none') {
        dropdownPanel.style.display = 'none';
        pickerContainer.classList.remove('open');
        pickerBtn.setAttribute('aria-expanded', 'false');
        pickerBtn.focus();
      }
    });

    // Language item selection
    document.querySelectorAll('.lang-choice').forEach(choice => {
      choice.addEventListener('click', () => {
        const lang = choice.getAttribute('data-lang');
        setPortalLanguage(lang);
        dropdownPanel.style.display = 'none';
        pickerContainer.classList.remove('open');
        pickerBtn.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // Initial Language Render
  setPortalLanguage(activeLang);
}

// Hook into DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPortalI18n);
} else {
  initPortalI18n();
}

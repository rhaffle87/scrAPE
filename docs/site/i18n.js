/**
 * scrAPE v0.30.1 — Technical Documentation Portal
 * Tactical Multilingual Internationalization (i18n) Engine
 * Supported Languages: English (EN), Indonesian (ID), Chinese (ZH), Spanish (ES), Japanese (JA), Russian (RU), German (DE)
 */

const I18N_DICTS = {
  en: {
    meta: {
      title: "scrAPE v0.30.1 // Technical Documentation Portal",
      desc: "Official technical documentation, CLI flag matrix, architecture guide, and operational manual for scrAPE v0.30.1."
    },
    ui: {
      searchPlaceholder: "SEARCH DOCS...",
      searchHint: "Ctrl+K",
      langStripLabel: "PORTAL LANGUAGE // BAHASA:",
      githubLink: "[GITHUB]",
      badgeNew: "NEW",
      badgeVerified: "VERIFIED",
      copyCode: "[COPY CODE]",
      copiedCode: "[COPIED!]",
      commandBuilder: "INTERACTIVE CLI BUILDER",
      builderPrompt: "CONFIGURE PARAMETERS & GENERATE RUNTIME COMMAND:",
      builderOutputLabel: "EXECUTABLE CLI COMMAND:",
      footerTagline: "Autonomous media extraction and stealth crawl engine engineered for high-throughput asset discovery and resilient WAF bypass.",
      searchResults: "found",
      noResults: "no results"
    },
    modules: [
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
    nav: {
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
    sections: {
      "sec-overview-arch": {
        tag: "MODULE [01] // SYSTEM OVERVIEW",
        h1: "Architecture and Objectives",
        desc: "Multi-engine stealth web scraping system for autonomous media extraction and AI dataset generation."
      },
      "sec-overview-formats": {
        tag: "MODULE [01] // SYSTEM OVERVIEW",
        h1: "Supported Formats and Operating Limits",
        desc: "Asset specifications, size filters, dimension boundaries, and rate bounds."
      },
      "sec-overview-pillars": {
        tag: "MODULE [01] // SYSTEM OVERVIEW",
        h1: "Next-Gen Core Architectural Pillars",
        desc: "Sub-linear BK-tree deduplication, profiler thread isolation, enterprise HTTP pooling, and VLM visual healing."
      },
      "sec-overview-v28": {
        tag: "MODULE [01] // ARCHITECTURAL UPDATE",
        h1: "Core Architecture (v0.28.0)",
        desc: "Production-grade decoupled ML pipeline, 3-tier hierarchical deduplication, self-healing DOM parser, and supervised hybrid concurrency."
      },
      "sec-install-prereqs": {
        tag: "MODULE [02] // INSTALLATION AND QUICKSTART",
        h1: "System Prerequisites and Toolchain",
        desc: "Python runtime, headless browser drivers, CUDA hardware acceleration, and Redis infrastructure requirements."
      },
      "sec-install-steps": {
        tag: "MODULE [02] // INSTALLATION AND QUICKSTART",
        h1: "Step-by-Step Installation",
        desc: "Virtual environment provisioning, pip package installation, and browser binary synchronization."
      },
      "sec-cli-flags": {
        tag: "MODULE [03] // CLI REFERENCE",
        h1: "Complete CLI Execution Flag Matrix",
        desc: "Full reference guide for all command-line switches, flags, threshold overrides, and extraction budgets."
      },
      "sec-cli-builder": {
        tag: "MODULE [03] // CLI REFERENCE",
        h1: "Interactive CLI Command Builder",
        desc: "Configure target parameters, concurrency pools, and stealth escalation flags to generate a ready-to-run terminal command."
      },
      "sec-engine-waf": {
        tag: "MODULE [04] // CORE ENGINE ARCHITECTURE",
        h1: "8-Tier Stealth WAF Escalation Pipeline",
        desc: "Multi-tiered adaptive fallback resolving Cloudflare Turnstile, Datadome, Incapsula, and bot mitigation barriers."
      },
      "sec-webui-arch": {
        tag: "MODULE [06] // WEBUI DASHBOARD",
        h1: "WebUI Server Architecture",
        desc: "FastAPI and HTMX reactive command center with real-time SSE streaming telemetry."
      },
      "sec-output-cas": {
        tag: "MODULE [08] // OUTPUT AND EXPORTS",
        h1: "Content-Addressable Storage (CAS)",
        desc: "SHA-256 deduplication and zero-byte NTFS/POSIX hardlink asset management."
      },
      "sec-threat-overview": {
        tag: "MODULE [10] // THREAT MODEL & SECURITY",
        h1: "Threat Model & Security Hardening",
        desc: "Formal defense specifications: SSRF mitigation, task lease isolation, CAS traversal defense, and prompt injection immunity."
      }
    }
  },

  id: {
    meta: {
      title: "scrAPE v0.30.1 // Portal Dokumentasi Teknis",
      desc: "Dokumentasi teknis resmi, matriks flag CLI, panduan arsitektur, dan manual operasional untuk scrAPE v0.30.1."
    },
    ui: {
      searchPlaceholder: "CARI DOKUMENTASI...",
      searchHint: "Ctrl+K",
      langStripLabel: "BAHASA PORTAL DOKUMENTASI:",
      githubLink: "[GITHUB]",
      badgeNew: "BARU",
      badgeVerified: "TERVERIFIKASI",
      copyCode: "[SALIN KODE]",
      copiedCode: "[TERSALIN!]",
      commandBuilder: "PEMBUAT PERINTAH CLI INTERAKTIF",
      builderPrompt: "KONFIGURASIKAN PARAMETER & HASILKAN PERINTAH RUNTIME:",
      builderOutputLabel: "PERINTAH CLI SIAP DIEKSEKUSI:",
      footerTagline: "Mesin ekstraksi media otonom dan crawler stealth berperforma tinggi untuk penemuan aset dan bypass WAF yang tangguh.",
      searchResults: "ditemukan",
      noResults: "tidak ada hasil"
    },
    modules: [
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
    nav: {
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
    sections: {
      "sec-overview-arch": {
        tag: "MODUL [01] // GAMBARAN SISTEM",
        h1: "Arsitektur & Tujuan Sistem",
        desc: "Sistem web scraping stealth multi-mesin untuk ekstraksi media otonom dan kurasi dataset kecerdasan buatan (AI)."
      },
      "sec-overview-formats": {
        tag: "MODUL [01] // GAMBARAN SISTEM",
        h1: "Format yang Didukung & Batasan Operasional",
        desc: "Spesifikasi aset, batas ukuran byte, resolusi dimensi minimum, dan batasan laju request (RPS)."
      },
      "sec-overview-pillars": {
        tag: "MODUL [01] // GAMBARAN SISTEM",
        h1: "Pilar Arsitektur Inti Next-Gen",
        desc: "Deduplikasi sub-linear BK-tree, partisi thread profiler terisolasi, connection pooling HTTP, dan self-healing visual VLM."
      },
      "sec-overview-v28": {
        tag: "MODUL [01] // PEMBARUAN ARSITEKTUR",
        h1: "Arsitektur Inti (v0.28.0)",
        desc: "Pipeline ML terpisah kelas produksi, deduplikasi hierarki 3 tingkat, parser DOM mandiri, dan konkurensi terkontrol."
      },
      "sec-install-prereqs": {
        tag: "MODUL [02] // INSTALASI & PANDUAN CEPAT",
        h1: "Prasyarat Sistem & Kebutuhan Lingkungan",
        desc: "Runtime Python 3.10+, driver browser stealth, akselerasi perangkat keras CUDA, dan infrastruktur Redis Streams."
      },
      "sec-install-steps": {
        tag: "MODUL [02] // INSTALASI & PANDUAN CEPAT",
        h1: "Langkah-Langkah Instalasi Lengkap",
        desc: "Pembuatan virtual environment, instalasi paket pip, dan sinkronisasi binary browser headless."
      },
      "sec-cli-flags": {
        tag: "MODUL [03] // REFERENSI CLI",
        h1: "Matriks Lengkap Flag Eksekusi CLI",
        desc: "Panduan referensi menyeluruh untuk seluruh opsi command-line, switch bypass, dan alokasi budget ekstraksi."
      },
      "sec-cli-builder": {
        tag: "MODUL [03] // REFERENSI CLI",
        h1: "Pembuat Perintah CLI Interaktif",
        desc: "Atur parameter target, konkurensi worker, dan opsi stealth untuk menghasilkan baris perintah terminal siap pakai."
      },
      "sec-engine-waf": {
        tag: "MODUL [04] // ARSITEKTUR MESIN UTAMA",
        h1: "Pipeline Eskalasi WAF Stealth 8-Tingkat",
        desc: "Fallback bertingkat adaptif untuk menembus Cloudflare Turnstile, Datadome, Incapsula, dan proteksi anti-bot modern."
      },
      "sec-webui-arch": {
        tag: "MODUL [06] // DASHBOARD WEBUI",
        h1: "Arsitektur Server WebUI",
        desc: "Pusat komando reaktif berbasis FastAPI dan HTMX dengan streaming telemetri Server-Sent Events (SSE)."
      },
      "sec-output-cas": {
        tag: "MODUL [08] // OUTPUT & EKSPOR DATA",
        h1: "Penyimpanan Berbasis Konten (CAS)",
        desc: "Deduplikasi instan SHA-256 dengan hardlink NTFS/POSIX tanpa konsumsi ruang penyimpanan disk tambahan."
      },
      "sec-threat-overview": {
        tag: "MODUL [10] // MODEL ANCAMAN & KEAMANAN",
        h1: "Pemodelan Ancaman & Penguatan Keamanan",
        desc: "Spesifikasi pertahanan formal: mitigasi SSRF, isolasi leasing tugas, pertahanan path traversal CAS, dan imunitas prompt injection."
      }
    }
  },

  zh: {
    meta: {
      title: "scrAPE v0.30.1 // 技术文档门户",
      desc: "scrAPE v0.30.1 官方技术文档、CLI 参数矩阵、核心架构指南与运维操作手册。"
    },
    ui: {
      searchPlaceholder: "搜索文档内容...",
      searchHint: "Ctrl+K",
      langStripLabel: "文档语言 // 语言选择:",
      githubLink: "[GITHUB 仓库]",
      badgeNew: "最新",
      badgeVerified: "已验证",
      copyCode: "[复制代码]",
      copiedCode: "[已复制!]",
      commandBuilder: "交互式 CLI 命令构建器",
      builderPrompt: "配置抓取参数并实时生成命令行脚本:",
      builderOutputLabel: "可执行 CLI 终端命令:",
      footerTagline: "面向高通量媒体资产发现与高韧性 WAF 绕过的自主化隐身网络爬虫引擎。",
      searchResults: "条结果",
      noResults: "无匹配结果"
    },
    modules: [
      "[01] 系统概览",
      "[02] 安装与快速开始",
      "[03] CLI 命令行参考",
      "[04] 核心爬虫引擎架构",
      "[05] 规则配置参考",
      "[06] WEBUI 控制面板",
      "[07] 生产部署与自动化运维",
      "[08] 数据产出与导出格式",
      "[09] 测试与故障排查",
      "[10] 威胁模型与安全架构"
    ],
    nav: {
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
    sections: {
      "sec-overview-arch": {
        tag: "模块 [01] // 系统概览",
        h1: "系统架构与工程目标",
        desc: "用于高通量媒体抽取与 AI 训练集构建的多引擎隐身网络爬虫系统。"
      },
      "sec-overview-formats": {
        tag: "模块 [01] // 系统概览",
        h1: "媒体支持格式与运行限制",
        desc: "资产格式规范、文件尺寸过滤、图像分辨率边界以及请求速率限制。"
      },
      "sec-overview-pillars": {
        tag: "模块 [01] // 系统概览",
        h1: "下一代核心架构支柱",
        desc: "次线性 BK-tree 空间去重、分析器线程隔离、企业级 HTTP 连接池与多模态 VLM 视觉自愈。"
      },
      "sec-overview-v28": {
        tag: "模块 [01] // 架构更新",
        h1: "核心架构 (v0.28.0)",
        desc: "生产级解耦 ML 管道、三层分级去重体系、DOM 自愈解析器与受控并发。"
      },
      "sec-install-prereqs": {
        tag: "模块 [02] // 安装与快速开始",
        h1: "系统环境前置依赖",
        desc: "Python 3.10+ 运行时环境、无头隐身浏览器驱动、CUDA 算力加速与 Redis Streams 基础设施。"
      },
      "sec-install-steps": {
        tag: "模块 [02] // 安装与快速开始",
        h1: "分步安装部署流程",
        desc: "隔离虚拟环境创建、依赖库 pip 安装与无头浏览器底层二进制包同步。"
      },
      "sec-cli-flags": {
        tag: "模块 [03] // CLI 命令行参考",
        h1: "全量 CLI 运行参数矩阵",
        desc: "详尽覆盖所有控制开关、网络阈值覆写与抓取配额预算的完整技术手册。"
      },
      "sec-cli-builder": {
        tag: "模块 [03] // CLI 命令行参考",
        h1: "交互式 CLI 命令生成器",
        desc: "可视化调整目标参数、工作线程数量与防御升级策略，一键生成终端执行命令。"
      },
      "sec-engine-waf": {
        tag: "模块 [04] // 核心爬虫引擎架构",
        h1: "8级阶梯式 WAF 穿透防御管线",
        desc: "自适应升级链路，平滑突破 Cloudflare Turnstile、Datadome 等主流反爬盾牌。"
      },
      "sec-webui-arch": {
        tag: "模块 [06] // WEBUI 控制面板",
        h1: "WebUI 响应式服务端架构",
        desc: "基于 FastAPI 与 HTMX 构建的高性能战术控制中心，支持实时 SSE 遥测流。"
      },
      "sec-output-cas": {
        tag: "模块 [08] // 数据产出与导出格式",
        h1: "内容寻址存储架构 (CAS)",
        desc: "SHA-256 哈希校验结合 NTFS/POSIX 硬链接实现零冗余空间占用的跨批次资产去重。"
      },
      "sec-threat-overview": {
        tag: "模块 [10] // 威胁模型与安全架构",
        h1: "系统威胁建模与防御加固",
        desc: "形式化安全验证：SSRF 全面防御、任务租约防抢占、跨目录穿透阻断与提示词注入免疫。"
      }
    }
  },

  es: {
    meta: {
      title: "scrAPE v0.30.1 // Portal de Documentación Técnica",
      desc: "Documentación técnica oficial, matriz de comandos CLI, arquitectura y manual operativo para scrAPE v0.30.1."
    },
    ui: {
      searchPlaceholder: "BUSCAR EN LA DOCUMENTACIÓN...",
      searchHint: "Ctrl+K",
      langStripLabel: "IDIOMA DEL PORTAL // LANGUAGE:",
      githubLink: "[GITHUB]",
      badgeNew: "NUEVO",
      badgeVerified: "VERIFICADO",
      copyCode: "[COPIAR CÓDIGO]",
      copiedCode: "[¡COPIADO!]",
      commandBuilder: "CONSTRUCTOR CLI INTERACTIVO",
      builderPrompt: "CONFIGURE LOS PARÁMETROS Y GENERE EL COMANDO:",
      builderOutputLabel: "COMANDO CLI EJECUTABLE:",
      footerTagline: "Motor autónomo de extracción de medios y rastreo sigiloso diseñado para alta capacidad de captura y evasión robusta de WAF.",
      searchResults: "encontrados",
      noResults: "sin resultados"
    },
    modules: [
      "[01] VISIÓN GENERAL DEL SISTEMA",
      "[02] INSTALACIÓN Y GUÍA RÁPIDA",
      "[03] REFERENCIA DE COMANDOS CLI",
      "[04] ARQUITECTURA DEL MOTOR PRINCIPAL",
      "[05] REFERENCIA DE CONFIGURACIÓN",
      "[06] PANEL DE CONTROL WEBUI",
      "[07] DESPLIEGUE Y OPERACIONES",
      "[08] FORMATOS DE SALIDA Y EXPORTACIÓN",
      "[09] PRUEBAS Y DIAGNÓSTICO",
      "[10] MODELO DE AMENAZAS Y SEGURIDAD"
    ],
    nav: {
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
    sections: {
      "sec-overview-arch": {
        tag: "MÓDULO [01] // VISIÓN GENERAL DEL SISTEMA",
        h1: "Arquitectura y Objetivos del Sistema",
        desc: "Sistema multimotor de web scraping sigiloso para extracción de medios y generación de datasets de IA."
      },
      "sec-overview-formats": {
        tag: "MÓDULO [01] // VISIÓN GENERAL DEL SISTEMA",
        h1: "Formatos Compatibles y Límites de Operación",
        desc: "Especificaciones de activos, filtros por tamaño de archivo, dimensiones mínimas y límites de tasa (RPS)."
      },
      "sec-overview-pillars": {
        tag: "MÓDULO [01] // VISIÓN GENERAL DEL SISTEMA",
        h1: "Pilares de Arquitectura de Nueva Generación",
        desc: "Deduplicación sublineal BK-tree, aislamiento de hilos de análisis, pooling HTTP empresarial y autocorrección visual VLM."
      },
      "sec-overview-v28": {
        tag: "MÓDULO [01] // ACTUALIZACIÓN DE ARQUITECTURA",
        h1: "Arquitectura Principal (v0.28.0)",
        desc: "Pipeline desacoplado de ML para producción, deduplicación en 3 niveles, parser DOM autorreparable y concurrencia supervisada."
      },
      "sec-install-prereqs": {
        tag: "MÓDULO [02] // INSTALACIÓN Y GUÍA RÁPIDA",
        h1: "Requisitos Previos del Sistema",
        desc: "Entorno Python 3.10+, navegadores sigilosos, aceleración por hardware CUDA y soporte de Redis Streams."
      },
      "sec-install-steps": {
        tag: "MÓDULO [02] // INSTALACIÓN Y GUÍA RÁPIDA",
        h1: "Instalación Paso a Paso",
        desc: "Configuración de entornos virtuales, instalación mediante pip y descarga de binarios de navegadores."
      },
      "sec-cli-flags": {
        tag: "MÓDULO [03] // REFERENCIA DE COMANDOS CLI",
        h1: "Matriz Completa de Flags de Ejecución",
        desc: "Guía de referencia de todos los parámetros de línea de comandos, umbrales y cuotas de extracción."
      },
      "sec-cli-builder": {
        tag: "MÓDULO [03] // REFERENCIA DE COMANDOS CLI",
        h1: "Constructor Interactivo de CLI",
        desc: "Ajuste parámetros de destino, concurrencia de workers y opciones de sigilo para generar el comando de terminal."
      },
      "sec-engine-waf": {
        tag: "MÓDULO [04] // ARQUITECTURA DEL MOTOR PRINCIPAL",
        h1: "Pipeline de Escalación WAF Sigiloso de 8 Niveles",
        desc: "Escalamiento adaptativo para evadir Cloudflare Turnstile, Datadome, Incapsula y defensas antibot."
      },
      "sec-webui-arch": {
        tag: "MÓDULO [06] // PANEL DE CONTROL WEBUI",
        h1: "Arquitectura del Servidor WebUI",
        desc: "Centro de comando reactivo construido con FastAPI y HTMX con telemetría en tiempo real por SSE."
      },
      "sec-output-cas": {
        tag: "MÓDULO [08] // FORMATOS DE SALIDA Y EXPORTACIÓN",
        h1: "Almacenamiento Dirigido por Contenido (CAS)",
        desc: "Deduplicación criptográfica SHA-256 con enlaces duros NTFS/POSIX sin costo adicional de almacenamiento en disco."
      },
      "sec-threat-overview": {
        tag: "MÓDULO [10] // MODELO DE AMENAZAS Y SEGURIDAD",
        h1: "Modelo de Amenazas y Blindaje de Seguridad",
        desc: "Defensas verificadas: mitigación estricta de SSRF, aislamiento de tareas, prevención de traversal y protección contra inyección de prompts."
      }
    }
  },

  ja: {
    meta: {
      title: "scrAPE v0.30.1 // 技術ドキュメントポータル",
      desc: "scrAPE v0.30.1 の公式技術ドキュメント、CLIフラグマトリックス、アーキテクチャガイド、および運用マニュアル。"
    },
    ui: {
      searchPlaceholder: "ドキュメント内を検索...",
      searchHint: "Ctrl+K",
      langStripLabel: "ドキュメント表示言語 // LANGUAGE:",
      githubLink: "[GITHUB リポジトリ]",
      badgeNew: "新機能",
      badgeVerified: "検証済み",
      copyCode: "[コードをコピー]",
      copiedCode: "[コピー完了!]",
      commandBuilder: "インタラクティブ CLI ビルダー",
      builderPrompt: "パラメータを設定してターミナル実行コマンドを生成:",
      builderOutputLabel: "実行可能な CLI コマンド:",
      footerTagline: "高スループットなメディア収集と強固なWAF回避を実現する自律型ステルスWebスクレイピングエンジン。",
      searchResults: "件ヒット",
      noResults: "一致なし"
    },
    modules: [
      "[01] システム概要",
      "[02] インストールとクイックスタート",
      "[03] CLI リファレンス",
      "[04] コアエンジンアーキテクチャ",
      "[05] 設定リファレンス",
      "[06] WEBUI ダッシュボード",
      "[07] デプロイと運用",
      "[08] 出力およびエクスポート",
      "[09] テストとトラブルシューティング",
      "[10] 脅威モデルとセキュリティ"
    ],
    nav: {
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
    sections: {
      "sec-overview-arch": {
        tag: "モジュール [01] // システム概要",
        h1: "システムアーキテクチャと目的",
        desc: "自律的なメディア抽出と AI データセット構築のためのマルチエンジン・ステルスWebスクレイピング基盤。"
      },
      "sec-overview-formats": {
        tag: "モジュール [01] // システム概要",
        h1: "対応フォーマットと動作上限",
        desc: "対応メディア種別、ファイル容量制限、画像最小解像度、および RPS 制限。"
      },
      "sec-overview-pillars": {
        tag: "モジュール [01] // システム概要",
        h1: "次世代コアアーキテクチャの柱",
        desc: "劣線形 BK-Tree 重複排除、プロファイラースレッド完全分離、高効率 HTTP プール、および VLM ビジュアル修復。"
      },
      "sec-overview-v28": {
        tag: "モジュール [01] // アーキテクチャ更新",
        h1: "コアアーキテクチャ (v0.28.0)",
        desc: "商用グレード非同期 ML パイプライン、3層重複排除、セルフヒーリング DOM パーサー、監視下ハイブリッド並行処理。"
      },
      "sec-install-prereqs": {
        tag: "モジュール [02] // インストールとクイックスタート",
        h1: "システム動作環境とツールチェーン",
        desc: "Python 3.10+ ランタイム、ステルスブラウザドライバ、CUDA 演算アクセラレーション、Redis Streams。"
      },
      "sec-install-steps": {
        tag: "モジュール [02] // インストールとクイックスタート",
        h1: "ステップ・バイ・ステップ導入手順",
        desc: "仮想環境の構築、pip パッケージ導入、ヘッドレスブラウザバイナリの自動同期。"
      },
      "sec-cli-flags": {
        tag: "モジュール [03] // CLI リファレンス",
        h1: "完全 CLI 実行フラグマトリックス",
        desc: "全コマンドライン引数、ネットワーク閾値の上書き、および抽出バジェットに関する完全ガイド。"
      },
      "sec-cli-builder": {
        tag: "モジュール [03] // CLI リファレンス",
        h1: "インタラクティブ CLI コマンドビルダー",
        desc: "ターゲット設定、ワーカー並列数、ステルス段階を直感的に構成し、実行用コマンドをワンクリック生成。"
      },
      "sec-engine-waf": {
        tag: "モジュール [04] // コアエンジンアーキテクチャ",
        h1: "8段階ステルス WAF エスカレーションパイプライン",
        desc: "Cloudflare Turnstile、Datadome、Incapsula などのアンチボット保護を段階的・適応的にバイパス。"
      },
      "sec-webui-arch": {
        tag: "モジュール [06] // WEBUI ダッシュボード",
        h1: "WebUI サーバーアーキテクチャ",
        desc: "FastAPI と HTMX を採用した軽量・高速な指令センター。SSE によるリアルタイムテレメトリ配信。"
      },
      "sec-output-cas": {
        tag: "モジュール [08] // 出力およびエクスポート",
        h1: "コンテンツアドレス指定ストレージ (CAS)",
        desc: "SHA-256 ハッシュ照合と NTFS/POSIX ハードリンクにより、ディスク消費ゼロで同一ファイルを重複排除。"
      },
      "sec-threat-overview": {
        tag: "モジュール [10] // 脅威モデルとセキュリティ",
        h1: "脅威モデルとセキュリティ堅牢化",
        desc: "SSRF 完全防御、タスク排他リース、CAS パストラバーサル防止、プロンプトインジェクション耐性の公式検証。"
      }
    }
  },

  ru: {
    meta: {
      title: "scrAPE v0.30.1 // Портал технической документации",
      desc: "Официальная техническая документация, матрица флагов CLI, архитектура и руководство оператора scrAPE v0.30.1."
    },
    ui: {
      searchPlaceholder: "ПОИСК ПО ДОКУМЕНТАЦИИ...",
      searchHint: "Ctrl+K",
      langStripLabel: "ЯЗЫК ДОКУМЕНТАЦИИ // LANGUAGE:",
      githubLink: "[GITHUB]",
      badgeNew: "НОВОЕ",
      badgeVerified: "ПРОВЕРЕНО",
      copyCode: "[КОПИРОВАТЬ]",
      copiedCode: "[СКОПИРОВАНО!]",
      commandBuilder: "ИНТЕРАКТИВНЫЙ КОНСТРУКТОР CLI",
      builderPrompt: "НАСТРОЙТЕ ПАРАМЕТРЫ И СГЕНЕРИРУЙТЕ КОМАНДУ:",
      builderOutputLabel: "ГОТОВАЯ КОМАНДА ДЛЯ ТЕРМИНАЛА:",
      footerTagline: "Автономный движок скрытного сбора медиаданных и обхода WAF с высокой пропускной способностью.",
      searchResults: "найдено",
      noResults: "нет совпадений"
    },
    modules: [
      "[01] ОБЗОР СИСТЕМЫ",
      "[02] УСТАНОВКА И БЫСТРЫЙ СТАРТ",
      "[03] СПРАВОЧНИК CLI",
      "[04] АРХИТЕКТУРА ЯДРА",
      "[05] СПРАВОЧНИК КОНФИГУРАЦИИ",
      "[06] ВЕБ-ПАНЕЛЬ УПРАВЛЕНИЯ",
      "[07] РАЗВЕРТЫВАНИЕ И ЭКСПЛУАТАЦИЯ",
      "[08] ВЫВОД И ЭКСПОРТ ДАННЫХ",
      "[09] ТЕСТИРОВАНИЕ И ДИАГНОСТИКА",
      "[10] МОДЕЛЬ УГРОЗ И БЕЗОПАСНОСТЬ"
    ],
    nav: {
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
    sections: {
      "sec-overview-arch": {
        tag: "МОДУЛЬ [01] // ОБЗОР СИСТЕМЫ",
        h1: "Архитектура и цели системы",
        desc: "Многоуровневая система скрытного сбора данных для автономного извлечения медиа и генерации датасетов ИИ."
      },
      "sec-overview-formats": {
        tag: "МОДУЛЬ [01] // ОБЗОР СИСТЕМЫ",
        h1: "Поддерживаемые форматы и рабочие лимиты",
        desc: "Спецификации ресурсов, фильтры размера файлов, минимальные габариты и лимиты запросов (RPS)."
      },
      "sec-overview-pillars": {
        tag: "МОДУЛЬ [01] // ОБЗОР СИСТЕМЫ",
        h1: "Ключевые архитектурные основы нового поколения",
        desc: "Сублинейная дедупликация BK-Tree, изоляция потоков профилировщика, пул соединений HTTP и VLM-самовосстановление."
      },
      "sec-overview-v28": {
        tag: "МОДУЛЬ [01] // АРХИТЕКТУРНОЕ ОБНОВЛЕНИЕ",
        h1: "Базовая архитектура (v0.28.0)",
        desc: "Промышленный асинхронный ML-пайплайн, трехуровневая дедупликация, самовосстанавливающийся DOM и управляемый параллелизм."
      },
      "sec-install-prereqs": {
        tag: "МОДУЛЬ [02] // УСТАНОВКА И БЫСТРЫЙ СТАРТ",
        h1: "Системные требования и зависимости",
        desc: "Python 3.10+, драйверы скрытных браузеров, аппаратное ускорение CUDA и инфраструктура Redis Streams."
      },
      "sec-install-steps": {
        tag: "МОДУЛЬ [02] // УСТАНОВКА И БЫСТРЫЙ СТАРТ",
        h1: "Пошаговая установка",
        desc: "Создание виртуального окружения, установка пакетов pip и синхронизация браузерных бинарников."
      },
      "sec-cli-flags": {
        tag: "МОДУЛЬ [03] // СПРАВОЧНИК CLI",
        h1: "Полная матрица флагов командной строки",
        desc: "Исчерпывающий справочник по всем параметрам CLI, порогам фильтрации и бюджетам сбора."
      },
      "sec-cli-builder": {
        tag: "МОДУЛЬ [03] // СПРАВОЧНИК CLI",
        h1: "Интерактивный конструктор команд CLI",
        desc: "Настройте параметры цели, число воркеров и эскалацию защиты для генерации готовой терминальной команды."
      },
      "sec-engine-waf": {
        tag: "МОДУЛЬ [04] // АРХИТЕКТУРА ЯДРА",
        h1: "8-уровневый пайплайн скрытного обхода WAF",
        desc: "Адаптивная эскалация для преодоления Cloudflare Turnstile, Datadome, Incapsula и систем защиты от ботов."
      },
      "sec-webui-arch": {
        tag: "МОДУЛЬ [06] // ВЕБ-ПАНЕЛЬ УПРАВЛЕНИЯ",
        h1: "Архитектура веб-сервера",
        desc: "Тактический командный центр на FastAPI и HTMX с передачей телеметрии в реальном времени через SSE."
      },
      "sec-output-cas": {
        tag: "МОДУЛЬ [08] // ВЫВОД И ЭКСПОРТ ДАННЫХ",
        h1: "Адресуемое по контенту хранилище (CAS)",
        desc: "Дедупликация SHA-256 с использованием жестких ссылок NTFS/POSIX без лишнего расхода дискового пространства."
      },
      "sec-threat-overview": {
        tag: "МОДУЛЬ [10] // МОДЕЛЬ УГРОЗ И БЕЗОПАСНОСТЬ",
        h1: "Модель угроз и укрепление безопасности",
        desc: "Формализованные средства защиты: предотвращение SSRF, изоляция аренды задач, защита CAS и устойчивость к инъекциям промптов."
      }
    }
  },

  de: {
    meta: {
      title: "scrAPE v0.30.1 // Technisches Dokumentationsportal",
      desc: "Offizielle technische Dokumentation, CLI-Flag-Matrix, Architekturleitfaden und Betriebshandbuch für scrAPE v0.30.1."
    },
    ui: {
      searchPlaceholder: "DOKUMENTATION DURCHSUCHEN...",
      searchHint: "Ctrl+K",
      langStripLabel: "DOKUMENTATIONSSPRACHE // LANGUAGE:",
      githubLink: "[GITHUB]",
      badgeNew: "NEU",
      badgeVerified: "VERIFIZIERT",
      copyCode: "[CODE KOPIEREN]",
      copiedCode: "[KOPIERT!]",
      commandBuilder: "INTERAKTIVER CLI-BUILDER",
      builderPrompt: "PARAMETER KONFIGURIEREN UND TERMINAL-BEFEHL ERZEUGEN:",
      builderOutputLabel: "AUSFÜHRBARER CLI-BEFEHL:",
      footerTagline: "Autonome Engine für verdeckte Medienextraktion und robusten WAF-Bypass mit hohem Durchsatz.",
      searchResults: "gefunden",
      noResults: "keine Treffer"
    },
    modules: [
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
    nav: {
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
    sections: {
      "sec-overview-arch": {
        tag: "MODUL [01] // SYSTEMÜBERSICHT",
        h1: "Systemarchitektur und Ziele",
        desc: "Multi-Engine-Stealth-Web-Scraping-System für autonome Medienextraktion und KI-Dataset-Erstellung."
      },
      "sec-overview-formats": {
        tag: "MODUL [01] // SYSTEMÜBERSICHT",
        h1: "Unterstützte Formate und Betriebsgrenzen",
        desc: "Asset-Spezifikationen, Dateigrößenfilter, minimale Auflösungen und RPS-Ratenbegrenzungen."
      },
      "sec-overview-pillars": {
        tag: "MODUL [01] // SYSTEMÜBERSICHT",
        h1: "Architekturpfeiler der nächsten Generation",
        desc: "Sublineare BK-Tree-Deduplizierung, Profiler-Thread-Isolation, Enterprise-HTTP-Pooling und VLM-visuelle Selbstheilung."
      },
      "sec-overview-v28": {
        tag: "MODUL [01] // ARCHITEKTUR-UPDATE",
        h1: "Kernarchitektur (v0.28.0)",
        desc: "Produktionsreife entkoppelte ML-Pipeline, 3-stufige Deduplizierung, selbstheilender DOM-Parser und geregelte Parallelität."
      },
      "sec-install-prereqs": {
        tag: "MODUL [02] // INSTALLATION & SCHNELLSTART",
        h1: "Systemanforderungen und Toolchain",
        desc: "Python 3.10+ Laufzeitumgebung, Stealth-Browser-Treiber, CUDA-Hardwarebeschleunigung und Redis Streams."
      },
      "sec-install-steps": {
        tag: "MODUL [02] // INSTALLATION & SCHNELLSTART",
        h1: "Schritt-für-Schritt-Installation",
        desc: "Einrichtung der virtuellen Umgebung, pip-Installation und Download der Headless-Browser-Binärdateien."
      },
      "sec-cli-flags": {
        tag: "MODUL [03] // CLI-REFERENZ",
        h1: "Vollständige CLI-Flag-Matrix",
        desc: "Vollständiger Referenzleitfaden für alle Befehlszeilenparameter, Schwellenwerte und Extraktionsbudgets."
      },
      "sec-cli-builder": {
        tag: "MODUL [03] // CLI-REFERENZ",
        h1: "Interaktiver CLI-Befehls-Generator",
        desc: "Passen Sie Zielparameter, Worker-Parallelität und Stealth-Stufen an, um den ausführbaren Befehl zu erstellen."
      },
      "sec-engine-waf": {
        tag: "MODUL [04] // KERN-ENGINE-ARCHITEKTUR",
        h1: "8-stufige Stealth-WAF-Eskalationspipeline",
        desc: "Adaptive Eskalation zur Umgehung von Cloudflare Turnstile, Datadome, Incapsula und Anti-Bot-Schutzmaßnahmen."
      },
      "sec-webui-arch": {
        tag: "MODUL [06] // WEBUI-DASHBOARD",
        h1: "WebUI-Serverarchitektur",
        desc: "Reaktives Kontrollzentrum auf Basis von FastAPI und HTMX mit Echtzeit-SSE-Streaming-Telemetrie."
      },
      "sec-output-cas": {
        tag: "MODUL [08] // AUSGABE & EXPORTE",
        h1: "Inhaltsadressierter Speicher (CAS)",
        desc: "Kryptografische SHA-256-Deduplizierung mit NTFS/POSIX-Hardlinks ohne zusätzlichen Festplattenspeicherbedarf."
      },
      "sec-threat-overview": {
        tag: "MODUL [10] // BEDROHUNGSMODELL & SICHERHEIT",
        h1: "Bedrohungsmodell und Sicherheits-Härtung",
        desc: "Verifizierte Abwehrmaßnahmen: vollständige SSRF-Prävention, Task-Lease-Isolation, Traversal-Schutz und Prompt-Injektions-Immunität."
      }
    }
  }
};

/**
 * Applies internationalization across the portal.
 */
function setPortalLanguage(lang) {
  if (!I18N_DICTS[lang]) {
    lang = 'en';
  }

  const dict = I18N_DICTS[lang];
  document.documentElement.lang = lang;

  // 1. Update Title and Meta
  if (dict.meta) {
    document.title = dict.meta.title;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute('content', dict.meta.desc);
  }

  // 2. Update Header & Search
  const searchInput = document.getElementById('doc-search');
  if (searchInput && dict.ui) {
    searchInput.placeholder = dict.ui.searchPlaceholder;
  }
  const searchHint = document.querySelector('.search-hint');
  if (searchHint && dict.ui) {
    searchHint.textContent = dict.ui.searchHint;
  }

  // 3. Update Module Headers
  const moduleTitles = document.querySelectorAll('.nav-module-title');
  moduleTitles.forEach((mt, idx) => {
    if (dict.modules[idx]) {
      const span = mt.querySelector('span:first-child');
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

  // 5. Update Section Headers (Tags, H1, Desc)
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
      }
    });
  }

  // 6. Update UI Labels & Badges
  const quickStripLabel = document.querySelector('.lang-quick-label');
  if (quickStripLabel && dict.ui.langStripLabel) {
    quickStripLabel.textContent = dict.ui.langStripLabel;
  }

  const footerTagline = document.querySelector('.footer-tagline');
  if (footerTagline && dict.ui.footerTagline) {
    footerTagline.textContent = dict.ui.footerTagline;
  }

  const builderTitle = document.querySelector('#sec-cli-builder .card-title');
  if (builderTitle && dict.ui.commandBuilder) {
    builderTitle.textContent = dict.ui.commandBuilder;
  }

  const builderOutputLabel = document.querySelector('#sec-cli-builder .code-header span');
  if (builderOutputLabel && dict.ui.builderOutputLabel) {
    builderOutputLabel.textContent = dict.ui.builderOutputLabel;
  }

  const copyButtons = document.querySelectorAll('.copy-btn');
  copyButtons.forEach(btn => {
    if (dict.ui.copyCode && !btn.textContent.includes('!')) {
      btn.textContent = dict.ui.copyCode;
    }
  });

  // 7. Sync Dropdowns & Buttons
  const select = document.getElementById('lang-select');
  if (select) select.value = lang;

  document.querySelectorAll('.lang-pill-btn, .lang-quick-btn').forEach(btn => {
    if (btn.getAttribute('data-lang') === lang) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // 8. Persist Choice in localStorage & URL parameter
  try {
    localStorage.setItem('scrape_doc_lang', lang);
    const url = new URL(window.location.href);
    if (url.searchParams.get('lang') !== lang) {
      url.searchParams.set('lang', lang);
      window.history.replaceState({}, '', url.toString());
    }
  } catch (e) {
    // Ignore sandbox or local file restrictions
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

  // Header Dropdown Listener
  const select = document.getElementById('lang-select');
  if (select) {
    select.addEventListener('change', (e) => {
      setPortalLanguage(e.target.value);
    });
  }

  // Quick Language Strip Buttons
  document.querySelectorAll('.lang-pill-btn, .lang-quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.getAttribute('data-lang');
      setPortalLanguage(lang);
    });
  });

  // Initial Language Render
  setPortalLanguage(activeLang);
}

// Hook into DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPortalI18n);
} else {
  initPortalI18n();
}

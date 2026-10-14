# -*- coding: utf-8 -*-
"""
Full Multilingual Database for all 55 Sections across:
en, id, zh, es, ja, ru, de
"""

from sections_data import MODULE_TAGS

SECTIONS_DB = {}

def add_sec(sec_id, tag_key, en_h1, en_desc, en_cards, en_codeHeaders=None, en_alerts=None,
            id_h1=None, id_desc=None, id_cards=None, id_codeHeaders=None, id_alerts=None,
            zh_h1=None, zh_desc=None, zh_cards=None, zh_codeHeaders=None, zh_alerts=None,
            es_h1=None, es_desc=None, es_cards=None, es_codeHeaders=None, es_alerts=None,
            ja_h1=None, ja_desc=None, ja_cards=None, ja_codeHeaders=None, ja_alerts=None,
            ru_h1=None, ru_desc=None, ru_cards=None, ru_codeHeaders=None, ru_alerts=None,
            de_h1=None, de_desc=None, de_cards=None, de_codeHeaders=None, de_alerts=None):
    
    SECTIONS_DB[sec_id] = {
        "en": {
            "tag": MODULE_TAGS[tag_key]["en"],
            "h1": en_h1,
            "desc": en_desc,
            "cards": en_cards,
            "codeHeaders": en_codeHeaders or [],
            "alerts": en_alerts or []
        },
        "id": {
            "tag": MODULE_TAGS[tag_key]["id"],
            "h1": id_h1 or en_h1,
            "desc": id_desc or en_desc,
            "cards": id_cards or en_cards,
            "codeHeaders": id_codeHeaders or en_codeHeaders or [],
            "alerts": id_alerts or en_alerts or []
        },
        "zh": {
            "tag": MODULE_TAGS[tag_key]["zh"],
            "h1": zh_h1 or en_h1,
            "desc": zh_desc or en_desc,
            "cards": zh_cards or en_cards,
            "codeHeaders": zh_codeHeaders or en_codeHeaders or [],
            "alerts": zh_alerts or en_alerts or []
        },
        "es": {
            "tag": MODULE_TAGS[tag_key]["es"],
            "h1": es_h1 or en_h1,
            "desc": es_desc or en_desc,
            "cards": es_cards or en_cards,
            "codeHeaders": es_codeHeaders or en_codeHeaders or [],
            "alerts": es_alerts or en_alerts or []
        },
        "ja": {
            "tag": MODULE_TAGS[tag_key]["ja"],
            "h1": ja_h1 or en_h1,
            "desc": ja_desc or en_desc,
            "cards": ja_cards or en_cards,
            "codeHeaders": ja_codeHeaders or en_codeHeaders or [],
            "alerts": ja_alerts or en_alerts or []
        },
        "ru": {
            "tag": MODULE_TAGS[tag_key]["ru"],
            "h1": ru_h1 or en_h1,
            "desc": ru_desc or en_desc,
            "cards": ru_cards or en_cards,
            "codeHeaders": ru_codeHeaders or en_codeHeaders or [],
            "alerts": ru_alerts or en_alerts or []
        },
        "de": {
            "tag": MODULE_TAGS[tag_key]["de"],
            "h1": de_h1 or en_h1,
            "desc": de_desc or en_desc,
            "cards": de_cards or en_cards,
            "codeHeaders": de_codeHeaders or en_codeHeaders or [],
            "alerts": de_alerts or en_alerts or []
        }
    }

print("add_sec helper defined.")

# ==========================================
# MODULE 01: SYSTEM OVERVIEW
# ==========================================
add_sec(
    "sec-overview-arch", "01",
    en_h1="Architecture and Objectives",
    en_desc="Multi-engine stealth web scraping system for autonomous media extraction and AI dataset generation.",
    en_cards=["1.1 System Architecture"],
    en_alerts=[{"title": "[!] CORE OPERATIONAL GUARANTEE", "bodyHtml": "The system executes via an 8-tier WAF fallback pipeline. Requests automatically escalate from lightweight direct HTTP up to headful stealth browser automation when challenge loops are detected. No manual intervention is required."}],
    id_h1="Arsitektur & Tujuan Sistem",
    id_desc="Sistem web scraping stealth multi-mesin untuk ekstraksi media otonom dan kurasi dataset kecerdasan buatan (AI).",
    id_cards=["1.1 Arsitektur Sistem"],
    id_alerts=[{"title": "[!] JAMINAN OPERASIONAL INTI", "bodyHtml": "Sistem beroperasi melalui pipeline fallback WAF 8-tingkat. Permintaan secara otomatis dieskalasi dari HTTP langsung yang ringan hingga otomatisasi browser stealth headful ketika loop tantangan terdeteksi. Tidak diperlukan intervensi manual."}],
    zh_h1="系统架构与设计目标",
    zh_desc="专为大规模自主媒体资产提取与 AI 训练数据集构建而设计的多引擎隐身抓取系统。",
    zh_cards=["1.1 系统底层架构"],
    zh_alerts=[{"title": "[!] 核心运行保障", "bodyHtml": "系统通过 8 级 WAF 降级保护管道运行。当检测到反爬质询循环时，请求会自动从轻量级直接 HTTP 递增升级到带界面的隐身浏览器自动化。整个过程无需人工干预。"}],
    es_h1="Arquitectura y Objetivos",
    es_desc="Sistema de raspado web sigiloso multimotor para extracción autónoma de medios y generación de conjuntos de datos de IA.",
    es_cards=["1.1 Arquitectura del sistema"],
    es_alerts=[{"title": "[!] GARANTÍA OPERATIVA FUNDAMENTAL", "bodyHtml": "El sistema opera mediante un pipeline de contingencia WAF de 8 niveles. Las solicitudes escalan automáticamente desde HTTP directo ligero hasta automatización de navegador sigiloso con interfaz gráfica cuando se detectan bucles de desafío. No se requiere intervención manual."}],
    ja_h1="アーキテクチャと目標",
    ja_desc="自律型メディア抽出および AI データセット生成のためのマルチエンジンステルス Web スクレイピングシステム。",
    ja_cards=["1.1 システムアーキテクチャ"],
    ja_alerts=[{"title": "[!] コア運用の保証", "bodyHtml": "システムは8段階のWAFフォールバックパイプラインを介して動作します。チャレンジループが検出されると、リクエストは軽量な直接HTTPからヘッドフルステルスブラウザ自動化へと自動的にエスカレーションされます。手動の介入は不要です。"}],
    ru_h1="Архитектура и цели системы",
    ru_desc="Многомоторная stealth-система веб-скрейпинга для автономного извлечения медиа и генерации датасетов для ИИ.",
    ru_cards=["1.1 Архитектура системы"],
    ru_alerts=[{"title": "[!] БАЗОВАЯ ГАРАНТИЯ РАБОТОСПОСОБНОСТИ", "bodyHtml": "Система функционирует через 8-уровневый резервный пайплайн WAF. При обнаружении циклов проверок запросы автоматически эскалируются от легковесного прямого HTTP до автоматизации в stealth-браузере с графическим интерфейсом. Ручное вмешательство не требуется."}],
    de_h1="Architektur und Zielsetzungen",
    de_desc="Multi-Engine-Stealth-Web-Scraping-System für autonome Medienextraktion und KI-Datensatzerstellung.",
    de_cards=["1.1 Systemarchitektur"],
    de_alerts=[{"title": "[!] KERN-BETRIEBSGARANTIE", "bodyHtml": "Das System operiert über eine 8-Stufen-WAF-Fallback-Pipeline. Anfragen eskalieren bei Erkennung von Challenge-Schleifen automatisch von schlankem direktem HTTP bis hin zu sichtbarer Stealth-Browser-Automatisierung. Es ist kein manueller Eingriff erforderlich."}]
)

add_sec(
    "sec-overview-formats", "01",
    en_h1="Supported Formats and Operating Limits",
    en_desc="Asset specifications, size filters, dimension boundaries, and rate bounds.",
    en_cards=["1.2 Media and Data Capabilities"],
    id_h1="Format yang Didukung & Batasan Operasional",
    id_desc="Spesifikasi aset, filter batas ukuran byte, resolusi dimensi minimum, dan batasan laju request (RPS).",
    id_cards=["1.2 Kapabilitas Media & Data"],
    zh_h1="支持的文件格式与运行阈值限制",
    zh_desc="多媒体资产技术规格、字节大小过滤规则、图像宽高分辨率下限以及抓取速率硬性指标。",
    zh_cards=["1.2 媒体与数据处理能力"],
    es_h1="Formatos Compatibles y Límites Operativos",
    es_desc="Especificaciones de activos, filtros de tamaño, límites de dimensiones y tasas de solicitudes.",
    es_cards=["1.2 Capacidades de medios y datos"],
    ja_h1="対応フォーマットと運用制限",
    ja_desc="メディア仕様、ファイルサイズフィルター、画像解像度の境界値、リクエストレート制限。",
    ja_cards=["1.2 メディアおよびデータ機能"],
    ru_h1="Поддерживаемые форматы и эксплуатационные лимиты",
    ru_desc="Спецификации ресурсов, фильтры размера файлов, ограничения разрешения и лимиты запросов.",
    ru_cards=["1.2 Возможности медиа и данных"],
    de_h1="Unterstützte Formate und Betriebsgrenzen",
    de_desc="Asset-Spezifikationen, Größenfilter, Dimensionsgrenzen und Ratenbeschränkungen.",
    de_cards=["1.2 Medien- & Datenkapazitäten"]
)

add_sec(
    "sec-overview-layout", "01",
    en_h1="Project Directory Layout",
    en_desc="File and folder organization of the repository.",
    en_cards=["1.3 Directory Structure"],
    en_codeHeaders=["TEXT // REPOSITORY TREE"],
    id_h1="Struktur Direktori Proyek",
    id_desc="Organisasi file dan modul repositori sistem.",
    id_cards=["1.3 Struktur Direktori"],
    id_codeHeaders=["TEKS // STRUKTUR REPOSITORI"],
    zh_h1="项目目录结构与模块组织",
    zh_desc="系统源代码树、配置持久化目录以及各子系统组织架构说明。",
    zh_cards=["1.3 代码仓库目录结构"],
    zh_codeHeaders=["文本 // 代码仓库结构树"],
    es_h1="Estructura de Directorios del Proyecto",
    es_desc="Organización de archivos y carpetas del repositorio.",
    es_cards=["1.3 Estructura de directorios"],
    es_codeHeaders=["TEXTO // ÁRBOL DEL REPOSITORIO"],
    ja_h1="プロジェクトのディレクトリ構成",
    ja_desc="リポジトリのファイルとフォルダーの体系的構成。",
    ja_cards=["1.3 ディレクトリ構造"],
    ja_codeHeaders=["テキスト // リポジトリツリー"],
    ru_h1="Структура каталогов проекта",
    ru_desc="Организация файлов и модулей репозитория.",
    ru_cards=["1.3 Структура каталогов"],
    ru_codeHeaders=["ТЕКСТ // ДЕРЕВО РЕПОЗИТОРИЯ"],
    de_h1="Projekt-Verzeichnislayout",
    de_desc="Datei- und Ordnerorganisation des Repositories.",
    de_cards=["1.3 Verzeichnisstruktur"],
    de_codeHeaders=["TEXT // REPOSITORY-BAUM"]
)

add_sec(
    "sec-overview-pillars", "01",
    en_h1="Core Architecture Pillars (v0.30.1)",
    en_desc="Enterprise multi-node orchestration, sub-linear BK-tree perceptual deduplication, isolated profiler thread pools, and zero-duplicate content-addressable storage.",
    en_cards=["1.4 Core Architecture Pillars (v0.30.1)"],
    en_codeHeaders=["BASH // CORE PILLAR CLI ACTIVATION"],
    id_h1="Pilar Arsitektur Inti (v0.30.1)",
    id_desc="Orkestrasi multi-node enterprise, deduplikasi perseptual sub-linear BK-tree, pool thread profiler terisolasi, dan CAS nol-duplikasi.",
    id_cards=["1.4 Pilar Arsitektur Inti (v0.30.1)"],
    id_codeHeaders=["BASH // AKTIVASI CLI PILAR INTI"],
    zh_h1="核心架构支柱 (v0.30.1)",
    zh_desc="企业级多节点协同编排、亚线性 BK-Tree 感知哈希去重、完全隔离的探针分析线程池以及零冗余内容寻址存储 (CAS)。",
    zh_cards=["1.4 核心架构支柱 (v0.30.1)"],
    zh_codeHeaders=["BASH // 核心支柱 CLI 启动指令"],
    es_h1="Pilares de la Arquitectura Central (v0.30.1)",
    es_desc="Orquestación multinodo empresarial, deduplicación perceptual sublineal con árbol BK, grupos de subprocesos aislados y CAS sin duplicados.",
    es_cards=["1.4 Pilares de la arquitectura central (v0.30.1)"],
    es_codeHeaders=["BASH // ACTIVACIÓN CLI DE PILARES BÁSICOS"],
    ja_h1="コアアーキテクチャの柱 (v0.30.1)",
    ja_desc="エンタープライズマルチノードオーケストレーション、劣線形BKツリー知覚重複排除、分離プロファイラースレッドプール、ゼロ重複CAS。",
    ja_cards=["1.4 コアアーキテクチャの柱 (v0.30.1)"],
    ja_codeHeaders=["BASH // コア機能 CLI 起動コマンド"],
    ru_h1="Основные архитектурные опоры (v0.30.1)",
    ru_desc="Корпоративная многоузловая оркестрация, сублинейная дедупликация BK-Tree, изолированные пулы профилировщиков и хранилище CAS.",
    ru_cards=["1.4 Основные архитектурные опоры (v0.30.1)"],
    ru_codeHeaders=["BASH // АКТИВАЦИЯ КЛЮЧЕВЫХ КОМПОНЕНТОВ В CLI"],
    de_h1="Kernarchitektur-Säulen (v0.30.1)",
    de_desc="Enterprise-Multi-Node-Orchestrierung, sublineare perzeptuelle BK-Tree-Deduplizierung, isolierte Profiler-Thread-Pools und Content-Addressable Storage (CAS).",
    de_cards=["1.4 Kernarchitektur-Säulen (v0.30.1)"],
    de_codeHeaders=["BASH // KERNKOMPONENTEN-CLI-AKTIVIERUNG"]
)

add_sec(
    "sec-overview-v28", "01_update",
    en_h1="Core Architecture (v0.28.0)",
    en_desc="Production-grade decoupled ML pipeline, 3-tier hierarchical deduplication, self-healing DOM parser, and supervised hybrid concurrency.",
    en_cards=["1.4 Architectural Breakthroughs in v0.28.0"],
    id_h1="Arsitektur Inti (v0.28.0)",
    id_desc="Pipeline ML terpisah kelas produksi, deduplikasi hierarki 3 tingkat, parser DOM mandiri, dan konkurensi terkontrol.",
    id_cards=["1.4 Terobosan Arsitektur pada v0.28.0"],
    zh_h1="核心架构演进 (v0.28.0)",
    zh_desc="生产级解耦式机器学习流水线、三层分级去重体系、自愈式 DOM 解析器与监督混合并发架构。",
    zh_cards=["1.4 v0.28.0 核心架构突破"],
    es_h1="Arquitectura Central (v0.28.0)",
    es_desc="Pipeline de ML desacoplado para producción, deduplicación jerárquica de 3 niveles, analizador DOM autorreparable y concurrencia híbrida supervisada.",
    es_cards=["1.4 Innovaciones arquitectónicas en v0.28.0"],
    ja_h1="コアアーキテクチャ (v0.28.0)",
    ja_desc="本番仕様の分離型MLパイプライン、3階層重複排除、自己修復DOMパーサー、監視付きハイブリッド並行処理。",
    ja_cards=["1.4 v0.28.0 におけるアーキテクチャの刷新"],
    ru_h1="Архитектура ядра (v0.28.0)",
    ru_desc="Промышленный изолированный ML-пайплайн, 3-уровневая иерархическая дедупликация, самовосстанавливающийся парсер DOM и гибридный параллелизм.",
    ru_cards=["1.4 Архитектурные прорывы в версии v0.28.0"],
    de_h1="Kernarchitektur (v0.28.0)",
    de_desc="Produktionsreife entkoppelte ML-Pipeline, 3-stufige hierarchische Deduplizierung, selbstheilender DOM-Parser und überwachte hybride Nebenläufigkeit.",
    de_cards=["1.4 Architektonische Durchbrüche in v0.28.0"]
)

# ==========================================
# MODULE 02: INSTALLATION AND QUICKSTART
# ==========================================
add_sec(
    "sec-install-prereqs", "02",
    en_h1="System Prerequisites and Toolchain",
    en_desc="Python runtime, headless browser drivers, CUDA hardware acceleration, and Redis infrastructure requirements.",
    en_cards=["2.1 System Requirements"],
    id_h1="Prasyarat Sistem & Kebutuhan Lingkungan",
    id_desc="Runtime Python 3.10+, driver browser stealth, akselerasi perangkat keras CUDA, dan infrastruktur Redis Streams.",
    id_cards=["2.1 Persyaratan Sistem"],
    zh_h1="系统环境与前置依赖需求",
    zh_desc="Python 3.10+ 运行时环境、无头浏览器驱动、CUDA 硬件加速以及 Redis 集群设施需求。",
    zh_cards=["2.1 系统与环境需求"],
    es_h1="Requisitos Previos del Sistema",
    es_desc="Entorno de ejecución de Python, controladores de navegador en modo headless, aceleración por hardware CUDA y requisitos de Redis.",
    es_cards=["2.1 Requisitos del sistema"],
    ja_h1="システム前提条件とツールチェーン",
    ja_desc="Python ランタイム、ヘッドレスブラウザドライバー、CUDA ハードウェアアクセラレーション、Redis 要件。",
    ja_cards=["2.1 システム要件"],
    ru_h1="Системные требования и инструменты",
    ru_desc="Среда выполнения Python, драйверы браузеров, аппаратное ускорение CUDA и инфраструктура Redis.",
    ru_cards=["2.1 Системные требования"],
    de_h1="Systemvoraussetzungen und Toolchain",
    de_desc="Python-Laufzeitumgebung, Headless-Browser-Treiber, CUDA-Hardwarebeschleunigung und Redis-Infrastrukturanforderungen.",
    de_cards=["2.1 Systemvoraussetzungen"]
)

add_sec(
    "sec-install-steps", "02",
    en_h1="Step-by-Step Installation",
    en_desc="Virtual environment provisioning, pip package installation, and browser binary synchronization.",
    en_cards=["2.2 Setup Procedure"],
    en_codeHeaders=["BASH // INSTALLATION COMMANDS"],
    en_alerts=[{"title": "[i] FLARESOLVERR SETUP", "bodyHtml": "FlareSolverr (Tier 5) runs as a Docker container. Start it with: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"}],
    id_h1="Langkah-Langkah Instalasi Lengkap",
    id_desc="Pembuatan virtual environment, instalasi paket pip, dan sinkronisasi binary browser headless.",
    id_cards=["2.2 Prosedur Instalasi & Pengaturan"],
    id_codeHeaders=["BASH // PERINTAH INSTALASI"],
    id_alerts=[{"title": "[i] PENGATURAN FLARESOLVERR", "bodyHtml": "FlareSolverr (Tingkat 5) berjalan sebagai kontainer Docker. Jalankan dengan: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"}],
    zh_h1="详细安装与部署步骤",
    zh_desc="Python 虚拟环境构建、pip 依赖包安装以及无头隐身浏览器内核同步下载。",
    zh_cards=["2.2 安装步骤与部署流程"],
    zh_codeHeaders=["BASH // 快速安装指令集"],
    zh_alerts=[{"title": "[i] FLARESOLVERR 服务部署", "bodyHtml": "FlareSolverr (Tier 5) 作为 Docker 容器独立运行。使用以下命令启动服务: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"}],
    es_h1="Pasos de Instalación Paso a Paso",
    es_desc="Aprovisionamiento de entorno virtual, instalación de paquetes pip y sincronización de binarios de navegador.",
    es_cards=["2.2 Procedimiento de instalación"],
    es_codeHeaders=["BASH // COMANDOS DE INSTALACIÓN"],
    es_alerts=[{"title": "[i] CONFIGURACIÓN DE FLARESOLVERR", "bodyHtml": "FlareSolverr (Nivel 5) se ejecuta como un contenedor Docker. Inícielo con: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"}],
    ja_h1="ステップバイステップのインストール手順",
    ja_desc="仮想環境の構築、pip パッケージのインストール、ブラウザバイナリの同期。",
    ja_cards=["2.2 セットアップ手順"],
    ja_codeHeaders=["BASH // インストールコマンド"],
    ja_alerts=[{"title": "[i] FLARESOLVERR セットアップ", "bodyHtml": "FlareSolverr (Tier 5) は Docker コンテナとして実行されます。起動コマンド: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"}],
    ru_h1="Пошаговая инструкция по установке",
    ru_desc="Создание виртуального окружения, установка пакетов pip и синхронизация бинарных файлов браузера.",
    ru_cards=["2.2 Процедура установки и настройки"],
    ru_codeHeaders=["BASH // КОМАНДЫ УСТАНОВКИ"],
    ru_alerts=[{"title": "[i] НАСТРОЙКА FLARESOLVERR", "bodyHtml": "FlareSolverr (Уровень 5) работает как контейнер Docker. Запустите его командой: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"}],
    de_h1="Schritt-für-Schritt-Installationsanleitung",
    de_desc="Bereitstellung der virtuellen Umgebung, Installation der pip-Pakete und Synchronisierung der Browser-Binärdateien.",
    de_cards=["2.2 Installationsablauf & Einrichtung"],
    de_codeHeaders=["BASH // INSTALLATIONSBEFEHLE"],
    de_alerts=[{"title": "[i] FLARESOLVERR-EINRICHTUNG", "bodyHtml": "FlareSolverr (Stufe 5) läuft als Docker-Container. Starten mit: <code>docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest</code>"}]
)

add_sec(
    "sec-install-launchers", "02",
    en_h1="Master Launchers and Wizard",
    en_desc="Interactive launcher scripts for all execution modes.",
    en_cards=["2.3 Launcher Options"],
    en_codeHeaders=["POWERSHELL // MASTER LAUNCHER"],
    id_h1="Peluncur Utama & Wizard Interaktif",
    id_desc="Skrip peluncur lintas-platform untuk seluruh mode eksekusi.",
    id_cards=["2.3 Opsi Peluncur & Wizard"],
    id_codeHeaders=["POWERSHELL // PELUNCUR UTAMA"],
    zh_h1="主启动脚本与交互式向导",
    zh_desc="适用于所有执行模式的交互式跨平台一键启动脚本与向导工具。",
    zh_cards=["2.3 启动脚本选项与交互式向导"],
    zh_codeHeaders=["POWERSHELL // 主启动脚本"],
    es_h1="Lanzadores Maestros y Asistente",
    es_desc="Scripts de inicio interactivos para todos los modos de ejecución.",
    es_cards=["2.3 Opciones del lanzador y asistente"],
    es_codeHeaders=["POWERSHELL // LANZADOR MAESTRO"],
    ja_h1="マスターランチャーとウィザード",
    ja_desc="すべての実行モードに対応するインタラクティブな起動スクリプト。",
    ja_cards=["2.3 ランチャーオプションとウィザード"],
    ja_codeHeaders=["POWERSHELL // マスターランチャー"],
    ru_h1="Скрипты запуска и интерактивный мастер",
    ru_desc="Интерактивные скрипты запуска для всех режимов работы системы.",
    ru_cards=["2.3 Параметры скрипта запуска и мастера"],
    ru_codeHeaders=["POWERSHELL // ОСНОВНОЙ СКРИПТ ЗАПУСКА"],
    de_h1="Master-Starter und Assistent",
    de_desc="Interaktive Starter-Skripte für sämtliche Ausführungsmodi.",
    de_cards=["2.3 Starter-Optionen & Assistent"],
    de_codeHeaders=["POWERSHELL // MASTER-STARTER"]
)

add_sec(
    "sec-install-recipes", "02",
    en_h1="First Run Recipes",
    en_desc="Copy-paste commands for common extraction patterns.",
    en_cards=["2.4 Command Recipes"],
    en_codeHeaders=[
        "RECIPE 1 // STANDARD SEED EXTRACTION WITH REJECTED MEDIA RETENTION",
        "RECIPE 2 // CONTINUOUS WATCHDOG AGENT WITH STATE CACHE",
        "RECIPE 3 // QUICK VALIDATION RUN (NO DOWNLOADS)",
        "RECIPE 4 // SEARCH-ONLY DISCOVERY (NO SEEDS)",
        "RECIPE 5 // STEALTH CRAWL (POLITE SPEED)"
    ],
    id_h1="Resep Eksekusi Pertama",
    id_desc="Perintah siap pakai (copy-paste) untuk pola ekstraksi umum.",
    id_cards=["2.4 Resep Perintah Eksekusi Pertama"],
    id_codeHeaders=[
        "RESEP 1 // EKSTRAKSI SEED STANDAR DENGAN RETENSI MEDIA DITOLAK",
        "RESEP 2 // AGEN PENGAWAS KONTINU DENGAN CACHE STATUS",
        "RESEP 3 // UJI VALIDASI CEPAT (TANPA UNDUHAN)",
        "RESEP 4 // PENEMUAN HANYA-PENCARIAN (TANPA SEED)",
        "RESEP 5 // CRAWL STEALTH (KECEPATAN SOPAN)"
    ],
    zh_h1="常用执行配方与命令示例",
    zh_desc="即拷即用的经典抓取与资产提取命令模式示例。",
    zh_cards=["2.4 常用执行命令配方"],
    zh_codeHeaders=[
        "配方 1 // 标准种子清单提取与未通过筛选媒体留存",
        "配方 2 // 带有状态缓存的持续监控守护进程",
        "配方 3 // 快速连通性验证运行 (不执行媒体下载)",
        "配方 4 // 仅基于搜索引擎的自主发现 (无种子清单)",
        "配方 5 // 深度隐身慢速抓取 (低频防风控模式)"
    ],
    es_h1="Recetas de Comandos para el Primer Inicio",
    es_desc="Comandos listos para copiar y pegar para patrones de extracción comunes.",
    es_cards=["2.4 Recetas de comandos para primer inicio"],
    es_codeHeaders=[
        "RECETA 1 // EXTRACCIÓN ESTÁNDAR DE SEEDS CON RETENCIÓN DE MEDIOS RECHAZADOS",
        "RECETA 2 // AGENTE DE MONITOREO CONTINUO CON CACHÉ DE ESTADO",
        "RECETA 3 // EJECUCIÓN RÁPIDA DE VALIDACIÓN (SIN DESCARGAS)",
        "RECETA 4 // DESCUBRIMIENTO SOLO POR BÚSQUEDA (SIN SEEDS)",
        "RECETA 5 // RASTREO SIGILOSO (VELOCIDAD CORTÉS)"
    ],
    ja_h1="初回実行コマンドレシピ",
    ja_desc="一般的な抽出パターンのためのコピー＆ペースト可能なコマンド。",
    ja_cards=["2.4 初回実行コマンドレシピ"],
    ja_codeHeaders=[
        "レシピ 1 // 除外メディア保持を伴う標準シード抽出",
        "レシピ 2 // 状態キャッシュを備えた継続的監視エージェント",
        "レシピ 3 // クイック検証実行 (ダウンロードなし)",
        "レシピ 4 // 検索による自動探索 (シードなし)",
        "レシピ 5 // ステルスクロール (低速丁寧モード)"
    ],
    ru_h1="Шаблоны команд для первого запуска",
    ru_desc="Готовые команды для типовых сценариев извлечения медиа.",
    ru_cards=["2.4 Шаблоны команд для первого запуска"],
    ru_codeHeaders=[
        "РЕЦЕПТ 1 // СТАНДАРТНОЕ ИЗВЛЕЧЕНИЕ ПО SEED-СПИСКАМ С СОХРАНЕНИЕМ ОТКЛОНЕННЫХ МЕДИА",
        "РЕЦЕПТ 2 // НЕПРЕРЫВНЫЙ АГЕНТ-НАБЛЮДАТЕЛЬ С КЭШИРОВАНИЕМ СОСТОЯНИЯ",
        "РЕЦЕПТ 3 // БЫСТРАЯ ПРОВЕРКА (БЕЗ СКАЧИВАНИЯ МЕДИА)",
        "РЕЦЕПТ 4 // ПОИСКОВОЕ ОБНАРУЖЕНИЕ (БЕЗ НАЧАЛЬНЫХ ССЫЛОК)",
        "РЕЦЕПТ 5 // СКРЫТЫЙ СБОР (ВЕЖЛИВЫЙ НИЗКОСКОРОСТНОЙ РЕЖИМ)"
    ],
    de_h1="Befehlsrezepte für den ersten Lauf",
    de_desc="Copy-Paste-Befehle für typische Extraktionsszenarien.",
    de_cards=["2.4 Befehlsrezepte für den ersten Lauf"],
    de_codeHeaders=[
        "REZEPT 1 // STANDARD-SEED-EXTRAKTION MIT SPEICHERUNG ABGELEHNTER MEDIEN",
        "REZEPT 2 // KONTINUIERLICHER WATCHDOG-AGENT MIT STATUS-CACHE",
        "REZEPT 3 // SCHNELLER VALIDIERUNGSLAUF (OHNE DOWNLOADS)",
        "REZEPT 4 // REINE SUCHERKENNUNG (OHNE SEEDS)",
        "REZEPT 5 // STEALTH-CRAWL (HÖFLICHE GESCHWINDIGKEIT)"
    ]
)

# ==========================================
# MODULE 03: CLI REFERENCE
# ==========================================
add_sec(
    "sec-cli-flags", "03",
    en_h1="Complete CLI Execution Flag Matrix",
    en_desc="Full reference guide for all command-line switches, flags, threshold overrides, and extraction budgets.",
    en_cards=["3.1 Command Line Parameters"],
    id_h1="Matriks Lengkap Flag Eksekusi CLI",
    id_desc="Panduan referensi menyeluruh untuk seluruh opsi command-line, switch bypass, dan alokasi budget ekstraksi.",
    id_cards=["3.1 Matriks Parameter Command Line"],
    zh_h1="CLI 命令行执行参数全景矩阵",
    zh_desc="系统所有命令行开关、参数阈值覆盖、资源预算分配与并发控制标志参考指南。",
    zh_cards=["3.1 命令行参数矩阵"],
    es_h1="Matriz Completa de Parámetros de Ejecución CLI",
    es_desc="Guía de referencia completa para todos los modificadores de línea de comandos, límites y presupuestos de extracción.",
    es_cards=["3.1 Matriz de parámetros de línea de comandos"],
    ja_h1="完全な CLI 実行フラグマトリックス",
    ja_desc="すべてのコマンドラインスイッチ、フラグ、しきい値の上書き、抽出バジェットの完全リファレンス。",
    ja_cards=["3.1 コマンドライン引数マトリックス"],
    ru_h1="Полная матрица флагов выполнения CLI",
    ru_desc="Полное руководство по всем ключам командной строки, переопределениям порогов и бюджетам извлечения.",
    ru_cards=["3.1 Матрица параметров командной строки"],
    de_h1="Vollständige CLI-Ausführungsflag-Matrix",
    de_desc="Vollständiger Referenzleitfaden für alle Befehlszeilenschalter, Flags, Schwellenwertüberschreibungen und Extraktionsbudgets.",
    de_cards=["3.1 Befehlszeilenparameter-Matrix"]
)

add_sec(
    "sec-cli-builder", "03",
    en_h1="Interactive CLI Command Builder",
    en_desc="Configure target parameters, concurrency pools, and stealth escalation flags to generate a ready-to-run terminal command.",
    en_cards=["3.2 Command Generator"],
    en_codeHeaders=["GENERATED CLI COMMAND STRING"],
    id_h1="Pembuat Perintah CLI Interaktif",
    id_desc="Atur parameter target, konkurensi worker, dan opsi stealth untuk menghasilkan baris perintah terminal siap pakai.",
    id_cards=["3.2 Generator Perintah Interaktif"],
    id_codeHeaders=["STRING PERINTAH CLI DIHASILKAN"],
    zh_h1="交互式 CLI 命令生成器",
    zh_desc="可视化配置目标关键词、并发工作池大小与隐身防风控等级，实时生成终端执行指令。",
    zh_cards=["3.2 交互式命令生成器"],
    zh_codeHeaders=["生成的 CLI 命令行指令"],
    es_h1="Generador Interactivo de Comandos CLI",
    es_desc="Configure parámetros de destino, grupos de concurrencia y flags de sigilo para generar un comando ejecutable.",
    es_cards=["3.2 Generador interactivo de comandos"],
    es_codeHeaders=["CADENA DE COMANDO CLI GENERADA"],
    ja_h1="インタラクティブ CLI コマンドビルダー",
    ja_desc="ターゲットパラメータ、並行処理プール、ステルスフラグを設定して、即実行可能なコマンドを生成します。",
    ja_cards=["3.2 インタラクティブコマンドジェネレーター"],
    ja_codeHeaders=["生成された CLI コマンド文字列"],
    ru_h1="Интерактивный конструктор команд CLI",
    ru_desc="Настройка параметров цели, пулов параллелизма и флагов скрытности для генерации готовой команды терминала.",
    ru_cards=["3.2 Интерактивный генератор команд"],
    ru_codeHeaders=["СГЕНЕРИРОВАННАЯ СТРОКА КОМАНДЫ CLI"],
    de_h1="Interaktiver CLI-Befehlsgenerator",
    de_desc="Konfigurieren Sie Zielparameter, Parallelitätspools und Stealth-Flags, um einen sofort ausführbaren Terminalbefehl zu generieren.",
    de_cards=["3.2 Interaktiver Befehlsgenerator"],
    de_codeHeaders=["GENERIERTE CLI-BEFEHLSZEILE"]
)

add_sec(
    "sec-cli-profiles", "03",
    en_h1="Execution Profiles",
    en_desc="Pre-tuned profile presets for specialized scrape topologies.",
    en_cards=["3.3 Preset Profile Matrix"],
    id_h1="Profil Eksekusi Bawaan",
    id_desc="Preset profil siap pakai yang telah dioptimalkan untuk berbagai topologi scraping khusus.",
    id_cards=["3.3 Matriks Profil Preset"],
    zh_h1="执行配置文件预设矩阵",
    zh_desc="针对不同抓取拓扑和目标站点预先调优的配置文件预设矩阵。",
    zh_cards=["3.3 预设配置档案矩阵"],
    es_h1="Perfiles de Ejecución",
    es_desc="Preajustes de perfil optimizados para topologías de raspado especializadas.",
    es_cards=["3.3 Matriz de perfiles predefinidos"],
    ja_h1="実行プロファイル",
    ja_desc="特定のスクレイピング環境向けに事前調整されたプロファイルプリセット。",
    ja_cards=["3.3 プリセットプロファイルマトリックス"],
    ru_h1="Профили выполнения",
    ru_desc="Предварительно настроенные профили для специализированных сценариев сбора данных.",
    ru_cards=["3.3 Матрица предустановленных профилей"],
    de_h1="Ausführungsprofile",
    de_desc="Vorkonfigurierte Profilvoreinstellungen für spezialisierte Scraping-Topologien.",
    de_cards=["3.3 Voreingestellte Profilmatrix"]
)

# ==========================================
# MODULE 04: CORE ENGINE ARCHITECTURE
# ==========================================
add_sec(
    "sec-engine-bfs", "04",
    en_h1="BFS Crawl Loop",
    en_desc="Asynchronous breadth-first traversal loop, priority queue dispatch, and link extraction.",
    en_cards=["4.1 Execution Sequence"],
    id_h1="Loop Crawl BFS",
    id_desc="Loop traversal breadth-first asinkron, dispatch antrean prioritas, dan ekstraksi tautan cerdas.",
    id_cards=["4.1 Urutan Eksekusi BFS"],
    zh_h1="BFS 广度优先爬行循环",
    zh_desc="基于异步协程的高性能广度优先遍历循环、动态优先级队列分发与超链接提取流水线。",
    zh_cards=["4.1 BFS 抓取执行时序"],
    es_h1="Bucle de Rastreo BFS",
    es_desc="Bucle de recorrido asíncrono en anchura, despacho de cola de prioridad y extracción de enlaces.",
    es_cards=["4.1 Secuencia de ejecución BFS"],
    ja_h1="BFS クロールループ",
    ja_desc="非同期幅優先探索ループ、優先度キューディスパッチ、リンク抽出処理。",
    ja_cards=["4.1 BFS実行シーケンス"],
    ru_h1="Цикл обхода BFS",
    ru_desc="Асинхронный цикл поиска в ширину, диспетчеризация очередей с приоритетом и извлечение ссылок.",
    ru_cards=["4.1 Последовательность выполнения BFS"],
    de_h1="BFS-Crawl-Schleife",
    de_desc="Asynchrone Breitensuch-Traversierungsschleife, Prioritäts-Queue-Dispatch und Link-Extraktion.",
    de_cards=["4.1 BFS-Ausführungssequenz"]
)

add_sec(
    "sec-engine-waf", "04",
    en_h1="8-Tier Stealth WAF Escalation Pipeline",
    en_desc="Multi-tiered adaptive fallback resolving Cloudflare Turnstile, Datadome, Incapsula, and bot mitigation barriers.",
    en_cards=["4.2 WAF Pipeline Hierarchy"],
    id_h1="Pipeline Eskalasi WAF Stealth 8-Tingkat",
    id_desc="Fallback bertingkat adaptif untuk menembus Cloudflare Turnstile, Datadome, Incapsula, dan proteksi anti-bot modern.",
    id_cards=["4.2 Hierarki Pipeline WAF 8-Tingkat"],
    zh_h1="8 级自适应隐身 WAF 降级保护管道",
    zh_desc="多层级自适应阶梯式回退机制，无感绕过 Cloudflare Turnstile、Datadome、Incapsula 等防爬风控屏障。",
    zh_cards=["4.2 8级隐身 WAF 降级管道体系"],
    es_h1="Pipeline de Escalado WAF Sigiloso de 8 Niveles",
    es_desc="Contingencia adaptativa de múltiples niveles que resuelve Cloudflare Turnstile, Datadome, Incapsula y defensas antibot.",
    es_cards=["4.2 Jerarquía del pipeline WAF de 8 niveles"],
    ja_h1="8段階ステルス WAF エスカレーションパイプライン",
    ja_desc="Cloudflare Turnstile、Datadome、Incapsulaなどのボット対策を解決する適応型フォールバック。",
    ja_cards=["4.2 8段階WAFパイプライン階層"],
    ru_h1="8-уровневый эскалационный stealth-пайплайн WAF",
    ru_desc="Многоуровневый адаптивный механизм обхода Cloudflare Turnstile, Datadome, Incapsula и систем защиты от ботов.",
    ru_cards=["4.2 Иерархия 8-уровневого пайплайна WAF"],
    de_h1="8-Stufen-Stealth-WAF-Eskalationspipeline",
    de_desc="Mehrstufiger adaptiver Fallback zur Überwindung von Cloudflare Turnstile, Datadome, Incapsula und Bot-Abwehrsystemen.",
    de_cards=["4.2 8-Stufen-WAF-Pipeline-Hierarchie"]
)

add_sec(
    "sec-engine-captcha", "04",
    en_h1="Universal Captcha Strategy",
    en_desc="Automated solver providers, challenge interception, and retry handlers.",
    en_cards=["4.3 Challenge Resolution Strategy"],
    id_h1="Strategi Captcha Universal",
    id_desc="Penyedia solver otomatis, intersepsi challenge visual, dan penanganan percobaan ulang mandiri.",
    id_cards=["4.3 Strategi Penyelesaian Challenge & Captcha"],
    zh_h1="通用验证码与人机质询求解策略",
    zh_desc="自动化第三方打码平台适配器、页面质询无感知拦截以及自适应重试容错机制。",
    zh_cards=["4.3 验证码与反爬质询解析策略"],
    es_h1="Estrategia Universal de Captcha",
    es_desc="Proveedores de resolución automatizada, intercepción de desafíos y controladores de reintentos.",
    es_cards=["4.3 Estrategia de resolución de captchas y desafíos"],
    ja_h1="ユニバーサルキャプチャ戦略",
    ja_desc="自動解決プロバイダー、チャレンジのインターセプト、およびリトライハンドラー。",
    ja_cards=["4.3 チャレンジ・キャプチャ解決戦略"],
    ru_h1="Универсальная стратегия обхода капчи",
    ru_desc="Автоматические провайдеры решения, перехват проверок и обработчики повторных попыток.",
    ru_cards=["4.3 Стратегия решения капч и проверок"],
    de_h1="Universelle Captcha-Strategie",
    de_desc="Automatisierte Solver-Anbieter, Challenge-Interzeption und Retry-Handler.",
    de_cards=["4.3 Captcha- & Challenge-Lösungsstrategie"]
)

add_sec(
    "sec-engine-scoring", "04",
    en_h1="Quality Scoring and Rejection",
    en_desc="URL classification, image dimension thresholds, and rejected media disk persistence.",
    en_cards=["4.4 Rejection Rules & Retention Paths"],
    id_h1="Penilaian Kualitas & Penolakan Aset",
    id_desc="Klasifikasi URL, ambang batas dimensi gambar minimum, dan persistensi media yang ditolak ke disk.",
    id_cards=["4.4 Aturan Penolakan & Jalur Retensi"],
    zh_h1="资产质量智能评分与拒绝留存策略",
    zh_desc="URL 智能分类、最小图像宽高过滤阈值以及被剔除低质媒体的分类落盘持久化机制。",
    zh_cards=["4.4 资源质量过滤规则与留存路径"],
    es_h1="Puntuación de Calidad y Rechazo",
    es_desc="Clasificación de URL, umbrales de dimensiones de imagen y persistencia en disco de medios rechazados.",
    es_cards=["4.4 Reglas de rechazo y rutas de retención"],
    ja_h1="品質スコアリングと除外判定",
    ja_desc="URL分類、画像解像度しきい値、および除外されたメディアのディスク保持管理。",
    ja_cards=["4.4 拒否ルールと保存パス"],
    ru_h1="Оценка качества и отбраковка ресурсов",
    ru_desc="Классификация URL, пороговые значения размеров изображений и сохранение отклоненных медиа на диск.",
    ru_cards=["4.4 Правила фильтрации и пути сохранения"],
    de_h1="Qualitätsbewertung und Ausschussbehandlung",
    de_desc="URL-Klassifizierung, Mindestbildabmessungen und Speicherung abgelehnter Medien auf Festplatte.",
    de_cards=["4.4 Ablehnungsregeln & Speicherpfade"]
)

add_sec(
    "sec-engine-normalize", "04",
    en_h1="URL Normalization",
    en_desc="Strip tracking parameters, canonicalize protocols, and prevent redundant queue cycles.",
    en_cards=["4.5 Canonicalization Pipeline"],
    id_h1="Normalisasi URL & Kanonisasi",
    id_desc="Pembersihan parameter pelacakan (tracking), kanonisasi protokol, dan pencegahan siklus antrean redundan.",
    id_cards=["4.5 Pipeline Kanonisasi URL"],
    zh_h1="URL 规范化与清洗管道",
    zh_desc="剔除营销追踪参数、规范化网络协议与路径，杜绝重复入队与死循环遍历。",
    zh_cards=["4.5 URL 规范化与清洗管道"],
    es_h1="Normalización de URL",
    es_desc="Eliminación de parámetros de seguimiento, canonización de protocolos y prevención de ciclos redundantes.",
    es_cards=["4.5 Pipeline de canonización de URL"],
    ja_h1="URL 正規化",
    ja_desc="追跡パラメータの削除、プロトコルの正規化、冗長な探索サイクルの防止。",
    ja_cards=["4.5 URL正規化パイプライン"],
    ru_h1="Нормализация URL",
    ru_desc="Удаление трекинговых параметров, канонизация протоколов и предотвращение избыточных циклов в очереди.",
    ru_cards=["4.5 Пайплайн нормализации URL"],
    de_h1="URL-Normalisierung",
    de_desc="Entfernung von Tracking-Parametern, Protokollkanonisierung und Vermeidung redundanter Queue-Zyklen.",
    de_cards=["4.5 URL-Kanonisierungs-Pipeline"]
)

add_sec(
    "sec-engine-pool", "04",
    en_h1="Pre-Warmed Browser Pool",
    en_desc="High-performance Camoufox browser pool recycling and context leasing.",
    en_cards=["4.6 Pre-Warmed Browser Lifecycle"],
    en_codeHeaders=["PYTHON // PREWARMED BROWSER POOL LEASING"],
    id_h1="Pool Browser Siap-Pakai (Pre-Warmed)",
    id_desc="Daur ulang pool browser Camoufox berperforma tinggi dan mekanisme leasing konteks terisolasi.",
    id_cards=["4.6 Siklus Hidup Pool Browser Siap-Pakai"],
    id_codeHeaders=["PYTHON // LEASING POOL BROWSER PREWARMED"],
    zh_h1="预热浏览器池与上下文借调",
    zh_desc="基于 Camoufox 内核的高性能热备无头浏览器池、自动周期性回收与上下文安全租用机制。",
    zh_cards=["4.6 预热浏览器池生命周期管理"],
    zh_codeHeaders=["PYTHON // 预热浏览器实例租借模式"],
    es_h1="Grupo de Navegadores Precalentados",
    es_desc="Reciclaje de alto rendimiento del grupo de navegadores Camoufox y asignación de contextos.",
    es_cards=["4.6 Ciclo de vida del grupo de navegadores precalentados"],
    es_codeHeaders=["PYTHON // ASIGNACIÓN DE NAVEGADORES PRECALENTADOS"],
    ja_h1="事前起動ブラウザプール",
    ja_desc="高性能 Camoufox ブラウザプールのリサイクルと分離コンテキストのリース管理。",
    ja_cards=["4.6 事前起動ブラウザプールのライフサイクル"],
    ja_codeHeaders=["PYTHON // 事前起動ブラウザプールのリース"],
    ru_h1="Пул предварительно запущенных браузеров",
    ru_desc="Высокопроизводительная утилизация пула браузеров Camoufox и изолированное предоставление контекстов.",
    ru_cards=["4.6 Жизненный цикл пула предварительно запущенных браузеров"],
    ru_codeHeaders=["PYTHON // АРЕНДА КОНТЕКСТОВ БРАУЗЕРА ИЗ ПУЛА"],
    de_h1="Vorgewärmter Browser-Pool",
    de_desc="Hochleistungs-Recycling des Camoufox-Browser-Pools und isoliertes Kontext-Leasing.",
    de_cards=["4.6 Lebenszyklus des vorgewärmten Browser-Pools"],
    de_codeHeaders=["PYTHON // VORGEWÄRMTES BROWSER-POOL-LEASING"]
)

add_sec(
    "sec-engine-broker", "04",
    en_h1="Redis Streams Task Broker",
    en_desc="Distributed consumer groups, pending entry tracking (PEL), and atomic task dispatch.",
    en_cards=["4.7 Distributed Cluster Coordination"],
    en_codeHeaders=["PYTHON // TASK BROKER INTERACTION PATTERN"],
    id_h1="Broker Tugas Redis Streams",
    id_desc="Grup konsumen terdistribusi, pelacakan pending entry (PEL), dan pengiriman tugas atomik.",
    id_cards=["4.7 Koordinasi Kluster Terdistribusi via Redis Streams"],
    id_codeHeaders=["PYTHON // POLA INTERAKSI BROKER TUGAS"],
    zh_h1="基于 Redis Streams 的分布式任务代理",
    zh_desc="分布式消费者组支持、未确认消息条目追踪 (PEL) 与原子任务并发分发协议。",
    zh_cards=["4.7 基于 Redis Streams 的分布式集群协同"],
    zh_codeHeaders=["PYTHON // 任务代理交互模式示例"],
    es_h1="Intermediario de Tareas Redis Streams",
    es_desc="Grupos de consumidores distribuidos, seguimiento de entradas pendientes (PEL) y despacho atómico de tareas.",
    es_cards=["4.7 Coordinación de clúster distribuido con Redis Streams"],
    es_codeHeaders=["PYTHON // PATRÓN DE INTERACCIÓN DEL INTERMEDIARIO DE TAREAS"],
    ja_h1="Redis Streams タスクブローカー",
    ja_desc="分散コンシューマーグループ、保留中エントリ追跡 (PEL)、アトミックなタスク配信。",
    ja_cards=["4.7 Redis Streams による分散クラスタ調整"],
    ja_codeHeaders=["PYTHON // タスクブローカーの相互作用パターン"],
    ru_h1="Брокер задач на базе Redis Streams",
    ru_desc="Распределенные группы потребителей, отслеживание незавершенных записей (PEL) и атомарная диспетчеризация задач.",
    ru_cards=["4.7 Координация распределенного кластера через Redis Streams"],
    ru_codeHeaders=["PYTHON // ПАТТЕРН ВЗАИМОДЕЙСТВИЯ С БРОКЕРОМ ЗАДАЧ"],
    de_h1="Redis-Streams-Task-Broker",
    de_desc="Verteilte Consumer-Gruppen, Pending Entry List (PEL)-Tracking und atomarer Task-Dispatch.",
    de_cards=["4.7 Verteilte Cluster-Koordination via Redis Streams"],
    de_codeHeaders=["PYTHON // TASK-BROKER-INTERAKTIONSMUSTER"]
)

add_sec(
    "sec-engine-ml", "04",
    en_h1="Vision Hardware & ML Pipeline",
    en_desc="CUDA/MPS device detection, half-precision (FP16) inference, and aesthetic scoring.",
    en_cards=["4.8 Hardware Acceleration Matrix"],
    en_codeHeaders=["PYTHON // HARDWARE DISCOVERY & PRECISION NEGOTIATION"],
    id_h1="Hardware Visi & Pipeline ML",
    id_desc="Deteksi perangkat keras CUDA/MPS, inferensi half-precision (FP16), dan penilaian estetika otomatis.",
    id_cards=["4.8 Matriks Akselerasi Perangkat Keras (CUDA / MPS)"],
    id_codeHeaders=["PYTHON // DETEKSI PERANGKAT KERAS & NEGOSIASI PRESISI"],
    zh_h1="视觉硬件加速与机器学习推理管道",
    zh_desc="自动检测宿主机 CUDA / Apple MPS 加速硬件，支持 FP16 半精度加速与 LAION 美学质量智能评分。",
    zh_cards=["4.8 视觉硬件加速矩阵 (CUDA / MPS / FP16)"],
    zh_codeHeaders=["PYTHON // 硬件环境发现与计算精度自适应协商"],
    es_h1="Hardware de Visión y Pipeline de ML",
    es_desc="Detección de dispositivos CUDA/MPS, inferencia de precisión media (FP16) y puntuación estética.",
    es_cards=["4.8 Matriz de aceleración de hardware (CUDA / MPS)"],
    es_codeHeaders=["PYTHON // DETECCIÓN DE HARDWARE Y NEGOCIACIÓN DE PRECISIÓN"],
    ja_h1="ビジョンハードウェアと ML パイプライン",
    ja_desc="CUDA/MPS デバイス検出、半精度 (FP16) 推論、美的スコアリング処理。",
    ja_cards=["4.8 ハードウェアアクセラレーションマトリックス"],
    ja_codeHeaders=["PYTHON // ハードウェア検出と精度交渉"],
    ru_h1="Аппаратное зрение и ML-пайплайн",
    ru_desc="Обнаружение ускорителей CUDA/MPS, инференс в половинной точности (FP16) и эстетический скоринг.",
    ru_cards=["4.8 Матрица аппаратного ускорения (CUDA / MPS)"],
    ru_codeHeaders=["PYTHON // ОБНАРУЖЕНИЕ ОБОРУДОВАНИЯ И ВЫБОР ТОЧНОСТИ"],
    de_h1="Vision-Hardware & ML-Pipeline",
    de_desc="CUDA/MPS-Geräteerkennung, Half-Precision (FP16)-Inferenz und automatische ästhetische Qualitätsbewertung.",
    de_cards=["4.8 Hardware-Beschleunigungsmatrix (CUDA / MPS)"],
    de_codeHeaders=["PYTHON // HARDWARE-ERKENNUNG & PRÄZISIONS-NEGOTIATION"]
)

add_sec(
    "sec-engine-healing", "04",
    en_h1="Self-Healing DOM Parser",
    en_desc="4-tier DOM recovery cascade with multi-provider LLM heuristic repair.",
    en_cards=["4.9 Autonomous Selector Repair"],
    en_codeHeaders=[
        "PYTHON // SELF-HEALING EXTRACTION CASCADE",
        "TEXT // MULTI-PROVIDER LLM SYNTHESIS CASCADE"
    ],
    id_h1="Parser DOM Self-Healing",
    id_desc="Kaskade pemulihan DOM 4-tingkat dengan perbaikan heuristik LLM multi-penyedia.",
    id_cards=["4.9 Perbaikan Selektor Otonom & VLM Healing"],
    id_codeHeaders=[
        "PYTHON // KASKADE EKSTRAKSI SELF-HEALING",
        "TEKS // KASKADE SINTESIS LLM MULTI-PENYEDIA"
    ],
    zh_h1="自愈式 DOM 页面解析引擎",
    zh_desc="四级自愈降级梯队，集成多云大语言模型 (Ollama / OpenRouter / Claude) 视觉感知与启发式选择器自愈。",
    zh_cards=["4.9 自主选择器修复与 VLM 视觉感知自愈"],
    zh_codeHeaders=[
        "PYTHON // 自愈式提取阶梯回退代码",
        "文本 // 多大模型供应商协同合成回退序列"
    ],
    es_h1="Analizador DOM Autorreparable",
    es_desc="Cascada de recuperación DOM de 4 niveles con reparación heurística mediante LLM multiproveedor.",
    es_cards=["4.9 Reparación autónoma de selectores y autorreparación VLM"],
    es_codeHeaders=[
        "PYTHON // CASCADA DE EXTRACCIÓN AUTORREPARABLE",
        "TEXTO // CASCADA DE SÍNTESIS LLM MULTIPROVEEDOR"
    ],
    ja_h1="自己修復型 DOM パーサー",
    ja_desc="マルチプロバイダーLLMヒューリスティック修復を備えた4段階のDOMリカバリーカスケード。",
    ja_cards=["4.9 自律的セレクター修復と VLM ビジュアル修復"],
    ja_codeHeaders=[
        "PYTHON // 自己修復抽出カスケード",
        "テキスト // マルチプロバイダーLLM統合カスケード"
    ],
    ru_h1="Самовосстанавливающийся парсер DOM",
    ru_desc="4-уровневый каскад восстановления DOM с эвристическим исправлением через несколько провайдеров LLM.",
    ru_cards=["4.9 Автономное восстановление селекторов и исправление через VLM"],
    ru_codeHeaders=[
        "PYTHON // КАСКАД САМОВОССТАНАВЛИВАЮЩЕГОСЯ ИЗВЛЕЧЕНИЯ",
        "ТЕКСТ // КАСКАД СИНТЕЗА ЧЕРЕЗ НЕСКОЛЬКО ПРОВАЙДЕРОВ LLM"
    ],
    de_h1="Selbstheilender DOM-Parser",
    de_desc="4-stufige DOM-Wiederherstellungskaskade mit heuristischer Multi-Provider-LLM-Reparatur.",
    de_cards=["4.9 Autonome Selektor-Reparatur & VLM-Heilung"],
    de_codeHeaders=[
        "PYTHON // SELBSTHEILENDE EXTRAKTIONSKASKADE",
        "TEXT // MULTI-PROVIDER-LLM-SYNTHESE-KASKADE"
    ]
)

add_sec(
    "sec-engine-bktree", "04",
    en_h1="BK-Tree Deduplication & Concurrency Partitioning",
    en_desc="Discrete metric tree indexing, hamming distance clustering, and isolated profiler execution pools.",
    en_cards=["4.10 Discrete Metric Tree & Execution Pool Partitioning"],
    en_codeHeaders=["PYTHON // BK-TREE METRIC SEARCH & CONNECTION POOLING"],
    id_h1="Deduplikasi BK-Tree & Partisi Konkurensi",
    id_desc="Pengindeksan pohon metrik diskrit, klasterisasi jarak Hamming, dan pemisahan pool eksekusi profiler terisolasi.",
    id_cards=["4.10 Pohon Metrik Diskrit & Partisi Pool Eksekusi"],
    id_codeHeaders=["PYTHON // PENCARIAN METRIK BK-TREE & CONNECTION POOLING"],
    zh_h1="BK-Tree 离散去重与并发线程池物理分区",
    zh_desc="基于汉明距离的离散度量树极速检索、毫秒级近重复图像剪枝与 CPU 密集型分析线程池物理隔离。",
    zh_cards=["4.10 离散距离度量树与执行池分区隔离"],
    zh_codeHeaders=["PYTHON // BK-TREE 距离度量搜索与网络连接池实现"],
    es_h1="Deduplicación con Árbol BK y Partición de Concurrencia",
    es_desc="Indexación en árbol métrico discreto, agrupación por distancia de Hamming y grupos de ejecución aislados.",
    es_cards=["4.10 Árbol métrico discreto y partición del grupo de ejecución"],
    es_codeHeaders=["PYTHON // BÚSQUEDA MÉTRICA EN ÁRBOL BK Y AGRUPACIÓN DE CONEXIONES"],
    ja_h1="BKツリー重複排除と並行処理のパーティショニング",
    ja_desc="離散距離ツリーインデックス、ハミング距離クラスタリング、分離されたプロファイラー実行プール。",
    ja_cards=["4.10 離散距離ツリーと実行プールのパーティショニング"],
    ja_codeHeaders=["PYTHON // BKツリー距離探索とコネクションプーリング"],
    ru_h1="Дедупликация на деревьях BK-Tree и сегментация параллелизма",
    ru_desc="Индексирование в метрических деревьях, кластеризация по расстоянию Хэмминга и изолированные пулы профилировщиков.",
    ru_cards=["4.10 Дерево дискретных метрик и сегментация пула выполнения"],
    ru_codeHeaders=["PYTHON // МЕТРИЧЕСКИЙ ПОИСК В BK-TREE И ПУЛЫ СОЕДИНЕНИЙ"],
    de_h1="BK-Tree-Deduplizierung & Concurrency-Partitionierung",
    de_desc="Diskrete Metrikbaum-Indizierung, Hamming-Distanz-Clustering und isolierte Profiler-Ausführungspools.",
    de_cards=["4.10 Diskreter Metrikbaum & Ausführungspool-Partitionierung"],
    de_codeHeaders=["PYTHON // BK-TREE-METRIKSUCHE & VERBINDUNGSPOOLING"]
)

# ==========================================
# MODULE 05: CONFIGURATION REFERENCE
# ==========================================
add_sec(
    "sec-config-env", "05",
    en_h1="Environment Variables (.env)",
    en_desc="Production credentials, rate limits, proxy gateways, and API tokens.",
    en_cards=["5.1 .env Configuration Template"],
    id_h1="Variabel Lingkungan (.env)",
    id_desc="Kredensial produksi, batas laju request, gateway proksi, dan token API.",
    id_cards=["5.1 Templat Konfigurasi .env"],
    zh_h1="环境变量与生产凭据配置 (.env)",
    zh_desc="生产环境安全凭据、请求速率限制、反向代理网关与第三方打码/LLM API 访问令牌配置。",
    zh_cards=["5.1 .env 环境变量配置模板"],
    es_h1="Variables de Entorno (.env)",
    es_desc="Credenciales de producción, límites de velocidad, puertas de enlace proxy y tokens de API.",
    es_cards=["5.1 Plantilla de configuración .env"],
    ja_h1="環境変数 (.env)",
    ja_desc="本番用認証情報、レート制限、プロキシゲートウェイ、API トークン。",
    ja_cards=["5.1 .env 設定テンプレート"],
    ru_h1="Переменные окружения (.env)",
    ru_desc="Учетные данные продакшена, лимиты скорости, прокси-шлюзы и токены API.",
    ru_cards=["5.1 Шаблон конфигурации .env"],
    de_h1="Umgebungsvariablen (.env)",
    de_desc="Produktionsanmeldedaten, Ratenbegrenzungen, Proxy-Gateways und API-Token.",
    de_cards=["5.1 .env Konfigurationsvorlage"]
)

add_sec(
    "sec-config-domain", "05",
    en_h1="domain_config.json",
    en_desc="Per-domain concurrency limits, custom wait selectors, and header overrides.",
    en_cards=["5.2 Configuration Keys Reference"],
    id_h1="domain_config.json",
    id_desc="Batas konkurensi per-domain, selektor tunggu kustom, dan penimpaan header HTTP.",
    id_cards=["5.2 Referensi Kunci Konfigurasi (domain_config.json)"],
    zh_h1="域名细粒度策略配置 (domain_config.json)",
    zh_desc="按目标域名自定义并发度、CSS/XPath 页面加载等待选择器与动态 HTTP Header 覆盖。",
    zh_cards=["5.2 域名级覆盖配置参考 (domain_config.json)"],
    es_h1="domain_config.json",
    es_desc="Límites de concurrencia por dominio, selectores de espera personalizados y anulaciones de encabezados.",
    es_cards=["5.2 Referencia de claves de configuración (domain_config.json)"],
    ja_h1="domain_config.json",
    ja_desc="ドメインごとの並行数制限、カスタム待機セレクター、HTTPヘッダーの上書き設定。",
    ja_cards=["5.2 設定キーリファレンス (domain_config.json)"],
    ru_h1="domain_config.json",
    ru_desc="Ограничения параллелизма по доменам, селекторы ожидания и переопределения заголовков.",
    ru_cards=["5.2 Справочник ключей конфигурации (domain_config.json)"],
    de_h1="domain_config.json",
    de_desc="Domain-spezifische Nebenläufigkeitsgrenzen, benutzerdefinierte Wait-Selektoren und Header-Überschreibungen.",
    de_cards=["5.2 Konfigurationsschlüssel-Referenz (domain_config.json)"]
)

add_sec(
    "sec-config-urlnorm", "05",
    en_h1="url_normalisation_rules.json",
    en_desc="Regular expressions for query parameter stripping and domain transformations.",
    en_cards=["5.3 Normalization Rule Schema"],
    en_codeHeaders=["JSON // RULE SCHEMA EXAMPLE"],
    en_alerts=[{"title": "[!] MANDATORY RULE", "bodyHtml": "Never hardcode domain-specific URL normalization regexes in Python files under <code>src/</code>. All rules MUST be declared in <code>data/url_normalisation_rules.json</code>."}],
    id_h1="url_normalisation_rules.json",
    id_desc="Ekspresi reguler (regex) untuk penghapusan parameter query dan transformasi domain.",
    id_cards=["5.3 Skema Aturan Normalisasi (url_normalisation_rules.json)"],
    id_codeHeaders=["JSON // CONTOH SKEMA ATURAN"],
    id_alerts=[{"title": "[!] ATURAN WAJIB", "bodyHtml": "Jangan pernah melakukan hardcode regex normalisasi URL spesifik domain di file Python di bawah <code>src/</code>. Seluruh aturan WAJIB dideklarasikan dalam <code>data/url_normalisation_rules.json</code>."}],
    zh_h1="URL 规范化规则定义 (url_normalisation_rules.json)",
    zh_desc="用于清理垃圾查询参数、重定向规整与特定域名 URL 转换的正则表达式声明系统。",
    zh_cards=["5.3 规范化规则架构 (url_normalisation_rules.json)"],
    zh_codeHeaders=["JSON // 规范化规则定义示例"],
    zh_alerts=[{"title": "[!] 强制执行规则", "bodyHtml": "严禁在 <code>src/</code> 目录下的 Python 源码中硬编码特定域名的 URL 正则表达式！所有规则必须在 <code>data/url_normalisation_rules.json</code> 中集中声明与维护。"}],
    es_h1="url_normalisation_rules.json",
    es_desc="Expresiones regulares para depurar parámetros de consulta y transformaciones de dominio.",
    es_cards=["5.3 Esquema de reglas de normalización (url_normalisation_rules.json)"],
    es_codeHeaders=["JSON // EJEMPLO DE ESQUEMA DE REGLA"],
    es_alerts=[{"title": "[!] REGLA OBLIGATORIA", "bodyHtml": "Nunca codifique expresiones regulares de normalización de URL específicas de dominio en archivos Python en <code>src/</code>. Todas las reglas DEBEN declararse en <code>data/url_normalisation_rules.json</code>."}],
    ja_h1="url_normalisation_rules.json",
    ja_desc="クエリパラメータの除去とドメイン変換のための正規表現ルール。",
    ja_cards=["5.3 正規化ルールスキーマ (url_normalisation_rules.json)"],
    ja_codeHeaders=["JSON // ルールスキーマの例"],
    ja_alerts=[{"title": "[!] 必須ルール", "bodyHtml": "<code>src/</code> 配下の Python ファイルにドメイン固有の URL 正規化正規表現を直接ハードコードしないでください。すべてのルールは必ず <code>data/url_normalisation_rules.json</code> に宣言する必要があります。"}],
    ru_h1="url_normalisation_rules.json",
    ru_desc="Регулярные выражения для удаления параметров запроса и трансформации доменов.",
    ru_cards=["5.3 Схема правил нормализации (url_normalisation_rules.json)"],
    ru_codeHeaders=["JSON // ПРИМЕР СХЕМЫ ПРАВИЛА"],
    ru_alerts=[{"title": "[!] ОБЯЗАТЕЛЬНОЕ ПРАВИЛО", "bodyHtml": "Ни в коем случае не зашивайте регулярные выражения нормализации URL для конкретных доменов в коде Python в каталоге <code>src/</code>. Все правила ДОЛЖНЫ быть объявлены в <code>data/url_normalisation_rules.json</code>."}],
    de_h1="url_normalisation_rules.json",
    de_desc="Reguläre Ausdrücke zur Bereinigung von Abfrageparametern und für Domain-Transformationen.",
    de_cards=["5.3 Normalisierungsregel-Schema (url_normalisation_rules.json)"],
    de_codeHeaders=["JSON // REGEL-SCHEMA-BEISPIEL"],
    de_alerts=[{"title": "[!] VERBINDLICHE REGEL", "bodyHtml": "Codieren Sie domainspezifische URL-Normalisierungs-Regexes niemals fest in Python-Dateien unter <code>src/</code> ein. Alle Regeln MÜSSEN in <code>data/url_normalisation_rules.json</code> deklariert werden."}]
)

add_sec(
    "sec-config-seeds", "05",
    en_h1="Seed Manifest Syntax",
    en_desc="Comments, inline directives, and priority weights in seeds/*.txt files.",
    en_cards=["5.4 Annotation Reference"],
    en_codeHeaders=["MANIFEST // SEED MANIFEST ANNOTATION EXAMPLE"],
    id_h1="Sintaks Manifest Seed",
    id_desc="Komentar, direktif inline, dan bobot prioritas dalam file seeds/*.txt.",
    id_cards=["5.4 Referensi Anotasi Manifest Seed"],
    id_codeHeaders=["MANIFEST // CONTOH ANOTASI MANIFEST SEED"],
    zh_h1="Seed 种子清单语法规范",
    zh_desc="seeds/*.txt 清单中的注释规范、行内深度控制指令与动态优先级权重定义。",
    zh_cards=["5.4 Seed 种子清单注解参考"],
    zh_codeHeaders=["MANIFEST // 种子清单行内注解语法示例"],
    es_h1="Sintaxis del Manifiesto de Seeds",
    es_desc="Comentarios, directivas en línea y pesos de prioridad en archivos seeds/*.txt.",
    es_cards=["5.4 Referencia de anotaciones de manifiesto seed"],
    es_codeHeaders=["MANIFEST // EJEMPLO DE ANOTACIÓN DE MANIFIESTO SEED"],
    ja_h1="シードマニフェスト構文",
    ja_desc="seeds/*.txt ファイルにおけるコメント、インラインディレクティブ、優先度ウェイト。",
    ja_cards=["5.4 シードマニフェストのアノテーションリファレンス"],
    ja_codeHeaders=["MANIFEST // シードマニフェストアノテーションの例"],
    ru_h1="Синтаксис манифестов seed-ссылок",
    ru_desc="Комментарии, строчные директивы и веса приоритета в файлах seeds/*.txt.",
    ru_cards=["5.4 Справочник аннотаций манифеста seed-ссылок"],
    ru_codeHeaders=["MANIFEST // ПРИМЕР АННОТАЦИЙ МАНИФЕСТА SEED-СПИСКА"],
    de_h1="Seed-Manifest-Syntax",
    de_desc="Kommentare, Inline-Direktiven und Prioritätsgewichte in seeds/*.txt-Dateien.",
    de_cards=["5.4 Annotationsreferenz für Seed-Manifeste"],
    de_codeHeaders=["MANIFEST // SEED-MANIFEST-ANNOTATIONSBEISPIEL"]
)

add_sec(
    "sec-config-profiles", "05",
    en_h1="Subject Profiles",
    en_desc="Subject-specific presets, output templates, and blacklist linkages.",
    en_cards=["5.5 Profile Presets"],
    id_h1="Profil Target Subjek",
    id_desc="Preset spesifik subjek, templat direktori output, dan keterkaitan blacklist.",
    id_cards=["5.5 Preset Profil Target (subject_profiles.json)"],
    zh_h1="抓取主题预设档案 (subject_profiles.json)",
    zh_desc="面向特定提取实体的预设配置、定制化输出结构模板与特定域名黑名单绑定。",
    zh_cards=["5.5 目标主题预设档案 (subject_profiles.json)"],
    es_h1="Perfiles de Asunto",
    es_desc="Preajustes específicos por temática, plantillas de salida y vinculación de listas negras.",
    es_cards=["5.5 Ajustes preestablecidos de perfil (subject_profiles.json)"],
    ja_h1="サブジェクトプロファイル",
    ja_desc="対象固有のプリセット、出力テンプレート、ブラックリストとの連携設定。",
    ja_cards=["5.5 プロファイルプリセット (subject_profiles.json)"],
    ru_h1="Профили объектов сбора",
    ru_desc="Специфические для объектов шаблоны, шаблоны вывода и привязки к черным спискам.",
    ru_cards=["5.5 Предустановки профилей (subject_profiles.json)"],
    de_h1="Subjekt-Profile",
    de_desc="Subjektspezifische Voreinstellungen, Ausgabetemplates und Blacklist-Verknüpfungen.",
    de_cards=["5.5 Profil-Voreinstellungen (subject_profiles.json)"]
)

add_sec(
    "sec-config-blacklist", "05",
    en_h1="Blacklist Management",
    en_desc="Globally excluded domains, ad servers, and low-value resource patterns.",
    en_cards=["5.6 Domain Blacklisting"],
    id_h1="Manajemen Blacklist Domain",
    id_desc="Domain yang dikecualikan secara global, server iklan, dan pola sumber daya bernilai rendah.",
    id_cards=["5.6 Manajemen Blacklist Domain & Filter Pengecualian"],
    zh_h1="域名黑名单与全局过滤 (blacklist.json)",
    zh_desc="全局排除的目标域名、广告追踪节点以及低价值无用资产的模式过滤管理。",
    zh_cards=["5.6 域名黑名单与排除过滤 (blacklist.json)"],
    es_h1="Gestión de Listas Negras",
    es_desc="Dominios excluidos globalmente, servidores de anuncios y patrones de recursos de bajo valor.",
    es_cards=["5.6 Gestión de listas negras de dominios y exclusiones"],
    ja_h1="ブラックリスト管理",
    ja_desc="グローバルに除外されたドメイン、広告サーバー、価値の低いリソースパターン。",
    ja_cards=["5.6 ドメインブラックリストと除外設定 (blacklist.json)"],
    ru_h1="Управление черными списками",
    ru_desc="Глобально исключенные домены, рекламные сети и паттерны нерелевантных ресурсов.",
    ru_cards=["5.6 Управление черными списками доменов (blacklist.json)"],
    de_h1="Blacklist-Verwaltung",
    de_desc="Global ausgeschlossene Domains, Ad-Server und Muster minderwertiger Ressourcen.",
    de_cards=["5.6 Domain-Blacklisting & Ausschlussfilter"]
)

print("Modules 03, 04, 05 added.")

# ==========================================
# MODULE 06: WEBUI DASHBOARD
# ==========================================
add_sec(
    "sec-webui-arch", "06",
    en_h1="WebUI Server Architecture",
    en_desc="FastAPI and HTMX reactive command center with real-time SSE streaming telemetry.",
    en_cards=["6.1 Decoupled FastAPI Server"],
    id_h1="Arsitektur Server WebUI",
    id_desc="Pusat komando reaktif berbasis FastAPI dan HTMX dengan streaming telemetri Server-Sent Events (SSE).",
    id_cards=["6.1 Server FastAPI Terpisah"],
    zh_h1="WebUI 可视化服务器架构",
    zh_desc="基于 FastAPI 与 HTMX 响应式构建的轻量控制中枢，支持 SSE 实时事件流与轻量前端解耦交互。",
    zh_cards=["6.1 解耦式 FastAPI 架构"],
    es_h1="Arquitectura del Servidor WebUI",
    es_desc="Centro de comando reactivo con FastAPI y HTMX con telemetría en tiempo real mediante SSE.",
    es_cards=["6.1 Servidor FastAPI desacoplado"],
    ja_h1="WebUI サーバーアーキテクチャ",
    ja_desc="リアルタイム SSE ストリーミングテレメトリを備えた FastAPI および HTMX リアクティブコマンドセンター。",
    ja_cards=["6.1 分離型 FastAPI サーバー"],
    ru_h1="Архитектура сервера WebUI",
    ru_desc="Реактивный командный центр на базе FastAPI и HTMX с потоковой телеметрией в реальном времени через SSE.",
    ru_cards=["6.1 Изолированный сервер FastAPI"],
    de_h1="WebUI-Serverarchitektur",
    de_desc="Reaktive Kommandozentrale mit FastAPI und HTMX mit Echtzeit-SSE-Streaming-Telemetrie.",
    de_cards=["6.1 Entkoppelter FastAPI-Server"]
)

add_sec(
    "sec-webui-views", "06",
    en_h1="Command Center and Media Vault",
    en_desc="Interactive control dashboard, live crawler status, and gallery inspection.",
    en_cards=["6.2 Dashboard Views"],
    id_h1="Command Center & Media Vault",
    id_desc="Dashboard kontrol interaktif, status crawler real-time, dan inspeksi galeri media hasil unduhan.",
    id_cards=["6.2 Tampilan Dashboard (Command Center & Media Vault)"],
    zh_h1="控制中枢仪表板与媒体资产金库",
    zh_desc="交互式抓取任务管控面板、实时运行拓扑以及全功能媒体画廊资产审查视图。",
    zh_cards=["6.2 仪表板核心视图 (指挥中心与媒体库)"],
    es_h1="Centro de Comando y Bóveda de Medios",
    es_desc="Panel de control interactivo, estado del rastreador en vivo e inspección de galería.",
    es_cards=["6.2 Vistas del panel (Centro de comando y bóveda de medios)"],
    ja_h1="コマンドセンターとメディア保管庫",
    ja_desc="インタラクティブな制御ダッシュボード、リアルタイムのクローラー状態、ギャラリー検査機能。",
    ja_cards=["6.2 ダッシュボードビュー (コマンドセンター & メディア保管庫)"],
    ru_h1="Командный центр и медиа-хранилище",
    ru_desc="Интерактивная панель управления, мониторинг скрейпера в реальном времени и галерея ресурсов.",
    ru_cards=["6.2 Представления дашборда (Командный центр и хранилище)"],
    de_h1="Kommandozentrale und Medientresor",
    de_desc="Interaktives Kontroll-Dashboard, Live-Crawler-Status und Galerie-Inspektion.",
    de_cards=["6.2 Dashboard-Ansichten (Kommandozentrale & Medientresor)"]
)

add_sec(
    "sec-webui-telemetry", "06",
    en_h1="Live Telemetry and SSE",
    en_desc="Real-time event streaming via Server-Sent Events, queue rates, and memory gauges.",
    en_cards=["6.3 Real-Time Event Pipeline"],
    id_h1="Telemetri Live & SSE",
    id_desc="Streaming event real-time melalui Server-Sent Events, metrik kecepatan antrean, dan monitor memori.",
    id_cards=["6.3 Pipeline Event Real-Time (SSE & Canvas)"],
    zh_h1="实时遥测监控与 SSE 事件流",
    zh_desc="通过 Server-Sent Events (SSE) 协议实时推送系统指标，包含任务队列吞吐率与内存使用率仪表盘。",
    zh_cards=["6.3 实时事件流管道 (SSE 与 Canvas 网络图)"],
    es_h1="Telemetría en Vivo y SSE",
    es_desc="Transmisión de eventos en tiempo real mediante Server-Sent Events, velocidades de cola y memoria.",
    es_cards=["6.3 Pipeline de eventos en tiempo real (SSE y Canvas)"],
    ja_h1="ライブテレメトリと SSE",
    ja_desc="Server-Sent Events、キュー処理レート、メモリ使用率ゲージによるリアルタイムストリーミング。",
    ja_cards=["6.3 リアルタイムイベントパイプライン (SSE & Canvas)"],
    ru_h1="Телеметрия в реальном времени и SSE",
    ru_desc="Потоковая передача событий через Server-Sent Events, скорость очередей и датчики памяти.",
    ru_cards=["6.3 Пайплайн событий реального времени (SSE и Canvas)"],
    de_h1="Live-Telemetrie und SSE",
    de_desc="Echtzeit-Ereignis-Streaming über Server-Sent Events, Queue-Raten und Speicheranzeigen.",
    de_cards=["6.3 Echtzeit-Event-Pipeline (SSE & Canvas)"]
)

add_sec(
    "sec-webui-design", "06",
    en_h1="Design Tokens",
    en_desc="Tactical utilitarian brutalist CSS tokens, high-contrast monospace typography, and color palettes.",
    en_cards=["6.4 Design Tokens Reference"],
    id_h1="Token Desain Brutalis",
    id_desc="Token CSS brutalis utilitarian taktis, tipografi monospace kontras tinggi, dan palet warna amber.",
    id_cards=["6.4 Referensi Token Desain (Brutalisme Taktis)"],
    zh_h1="UI 设计令牌规范 (Design Tokens)",
    zh_desc="战术实用主义 (Utilitarian Brutalism) 设计规范、高对比等宽终端字体与硬朗机能色彩体系。",
    zh_cards=["6.4 设计规范令牌参考 (战术实用主义)"],
    es_h1="Tokens de Diseño",
    es_desc="Tokens CSS de brutalismo utilitario táctico, tipografía monoespaciada de alto contraste y paletas de colores.",
    es_cards=["6.4 Referencia de tokens de diseño (Brutalismo táctico)"],
    ja_h1="デザイントークン",
    ja_desc="タクティカルブルータリズム CSS トークン、高コントラスト等幅タイポグラフィ、カラーパレット。",
    ja_cards=["6.4 デザイントークンリファレンス (タクティカルブルータリズム)"],
    ru_h1="Дизайн-токены",
    ru_desc="Тактические CSS-токены утилитарного брутализма, высококонтрастная моноширинная типографика и палитры.",
    ru_cards=["6.4 Справочник дизайн-токенов (Тактический брутализм)"],
    de_h1="Design-Tokens",
    de_desc="Taktische utilitaristische brutalistische CSS-Tokens, kontrastreiche Monospace-Typografie und Farbpaletten.",
    de_cards=["6.4 Design-Token-Referenz (Taktischer Brutalismus)"]
)

add_sec(
    "sec-webui-health", "06",
    en_h1="Node Health Tactical Monitor",
    en_desc="Subsystem health checks, heartbeat probes, and Redis cluster telemetry.",
    en_cards=["6.5 Tactical Telemetry & Governance"],
    en_codeHeaders=["JSON // NODE HEALTH TELEMETRY PAYLOAD"],
    id_h1="Monitor Taktis Node Health",
    id_desc="Pemeriksaan kesehatan subsistem, probe heartbeat berkala, dan telemetri kluster Redis.",
    id_cards=["6.5 Telemetri Taktis & Tata Kelola Node"],
    id_codeHeaders=["JSON // PAYLOAD TELEMETRI KESEHATAN NODE"],
    zh_h1="集群节点健康战术监控",
    zh_desc="多子系统就绪健康检查、定时节点心跳探测与 Redis 分布式集群治理指标。",
    zh_cards=["6.5 战术遥测监控与节点健康治理"],
    zh_codeHeaders=["JSON // 节点健康指标遥测载荷示例"],
    es_h1="Monitor Táctico de Estado del Nodo",
    es_desc="Verificaciones de estado de subsistemas, sondas de latido y telemetría de clúster Redis.",
    es_cards=["6.5 Telemetría táctica y gobernanza de nodos"],
    es_codeHeaders=["JSON // CARGA ÚTIL DE TELEMETRÍA DE ESTADO DEL NODO"],
    ja_h1="ノード健全性タクティカルモニター",
    ja_desc="サブシステムの正常性チェック、ハートビートプローブ、Redis クラスタテレメトリ。",
    ja_cards=["6.5 タクティカルテレメトリとノードガバナンス"],
    ja_codeHeaders=["JSON // ノード健全性テレメトリペイロード"],
    ru_h1="Тактический монитор работоспособности узлов",
    ru_desc="Проверки состояния подсистем, периодические пробы heartbeat и телеметрия кластера Redis.",
    ru_cards=["6.5 Тактическая телеметрия и управление узлами"],
    ru_codeHeaders=["JSON // ПОЛЕЗНАЯ НАГРУЗКА ТЕЛЕМЕТРИИ РАБОТОСПОСОБНОСТИ УЗЛА"],
    de_h1="Taktischer Knoten-Gesundheitsmonitor",
    de_desc="Subsystem-Integritätsprüfungen, Heartbeat-Sonden und Redis-Cluster-Telemetrie.",
    de_cards=["6.5 Taktische Telemetrie & Knoten-Governance"],
    de_codeHeaders=["JSON // KNOTENGESUNDHEITS-TELEMETRIE-PAYLOAD"]
)

# ==========================================
# MODULE 07: DEPLOYMENT AND OPERATIONS
# ==========================================
add_sec(
    "sec-ops-docker", "07",
    en_h1="Docker Compose",
    en_desc="Multi-container production deployment with FlareSolverr, Redis, and WebUI.",
    en_cards=["7.1 Container Deployment"],
    en_codeHeaders=["BASH // DOCKER COMPOSE LAUNCH"],
    id_h1="Deployment dengan Docker Compose",
    id_desc="Penyebaran produksi multi-kontainer dengan FlareSolverr, Redis Streams, dan server WebUI.",
    id_cards=["7.1 Deployment Kontainer dengan Docker Compose"],
    id_codeHeaders=["BASH // PELUNCURAN DOCKER COMPOSE"],
    zh_h1="Docker Compose 生产集群部署",
    zh_desc="包含 FlareSolverr、Redis 消息代理与 WebUI 控制中枢的标准化多容器生产部署编排。",
    zh_cards=["7.1 Docker Compose 容器化集群部署"],
    zh_codeHeaders=["BASH // DOCKER COMPOSE 启动命令"],
    es_h1="Despliegue con Docker Compose",
    es_desc="Despliegue en producción multicontenedor con FlareSolverr, Redis y WebUI.",
    es_cards=["7.1 Despliegue en contenedores con Docker Compose"],
    es_codeHeaders=["BASH // LANZAMIENTO CON DOCKER COMPOSE"],
    ja_h1="Docker Compose によるデプロイ",
    ja_desc="FlareSolverr、Redis、WebUI を備えたマルチコンテナ本番環境デプロイ。",
    ja_cards=["7.1 Docker Compose によるコンテナデプロイ"],
    ja_codeHeaders=["BASH // DOCKER COMPOSE 起動"],
    ru_h1="Развертывание через Docker Compose",
    ru_desc="Многоконтейнерное производственное развертывание с FlareSolverr, Redis и WebUI.",
    ru_cards=["7.1 Развертывание в контейнерах с Docker Compose"],
    ru_codeHeaders=["BASH // ЗАПУСК ЧЕРЕЗ DOCKER COMPOSE"],
    de_h1="Docker Compose",
    de_desc="Multi-Container-Produktionsbereitstellung mit FlareSolverr, Redis und WebUI.",
    de_cards=["7.1 Container-Bereitstellung mit Docker Compose"],
    de_codeHeaders=["BASH // DOCKER COMPOSE START"]
)

add_sec(
    "sec-ops-watchdog", "07",
    en_h1="Watchdog Agent",
    en_desc="Continuous crawl daemon with automated health checks and restart policies.",
    en_cards=["7.2 Continuous Monitoring Loop"],
    en_codeHeaders=["POWERSHELL // WATCHDOG AGENT COMMAND"],
    id_h1="Agen Pengawas (Watchdog)",
    id_desc="Daemon crawl kontinu dengan pemeriksaan kesehatan otomatis dan kebijakan restart cerdas.",
    id_cards=["7.2 Loop Pemantauan Berkelanjutan (Watchdog)"],
    id_codeHeaders=["POWERSHELL // PERINTAH AGEN PENGAWAS"],
    zh_h1="Watchdog 守护监控代理",
    zh_desc="具备自适应退避重启、SQLite WAL 状态持久化与异常自恢复能力的常驻抓取守护进程。",
    zh_cards=["7.2 Watchdog 持续监控守护进程"],
    zh_codeHeaders=["POWERSHELL // WATCHDOG 守护进程启动指令"],
    es_h1="Agente Watchdog",
    es_desc="Demonio de rastreo continuo con comprobaciones automáticas de estado y políticas de reinicio.",
    es_cards=["7.2 Bucle de monitoreo continuo (Watchdog)"],
    es_codeHeaders=["POWERSHELL // COMANDO DEL AGENTE WATCHDOG"],
    ja_h1="Watchdog エージェント",
    ja_desc="自動ヘルスチェックと再起動ポリシーを備えた継続的クロールデーモン。",
    ja_cards=["7.2 継続的モニタリングループ (Watchdog)"],
    ja_codeHeaders=["POWERSHELL // WATCHDOG エージェントコマンド"],
    ru_h1="Агент-наблюдатель (Watchdog)",
    ru_desc="Демон непрерывного сбора данных с автоматической проверкой работоспособности и перезапуском.",
    ru_cards=["7.2 Непрерывный цикл мониторинга (Watchdog)"],
    ru_codeHeaders=["POWERSHELL // КОМАНДА ЗАПУСКА АГЕНТА WATCHDOG"],
    de_h1="Watchdog-Agent",
    de_desc="Kontinuierlicher Crawl-Daemon mit automatisierten Integritätsprüfungen und Neustartrichtlinien.",
    de_cards=["7.2 Kontinuierliche Überwachungsschleife (Watchdog)"],
    de_codeHeaders=["POWERSHELL // WATCHDOG-AGENT-BEFEHL"]
)

add_sec(
    "sec-ops-notifications", "07",
    en_h1="Notification Pipeline",
    en_desc="Pluggable notification channels (Telegram, Discord, Slack, Webhooks).",
    en_cards=["7.3 Multi-Channel Alerts"],
    id_h1="Saluran Notifikasi Multi-Platform",
    id_desc="Saluran peringatan pluggable: bot Telegram, webhook Discord, Slack, dan HTTP webhook kustom.",
    id_cards=["7.3 Peringatan Multi-Saluran (Telegram, Discord, Slack)"],
    zh_h1="多渠道实时告警通知管道",
    zh_desc="插件式告警推送体系，支持 Telegram Bot、Discord Webhook、Slack 以及第三方自定义 Webhook 接入。",
    zh_cards=["7.3 多渠道实时报警 (Telegram / Discord / Slack / Webhook)"],
    es_h1="Pipeline de Notificaciones",
    es_desc="Canales de notificación conectables (Telegram, Discord, Slack, Webhooks).",
    es_cards=["7.3 Alertas multicanal (Telegram, Discord, Slack)"],
    ja_h1="通知パイプライン",
    ja_desc="プラグイン可能な通知チャネル (Telegram、Discord、Slack、Webhooks)。",
    ja_cards=["7.3 マルチチャネルアラート (Telegram, Discord, Slack)"],
    ru_h1="Пайплайн уведомлений",
    ru_desc="Подключаемые каналы оповещений (Telegram, Discord, Slack, вебхуки).",
    ru_cards=["7.3 Многоканальные оповещения (Telegram, Discord, Slack)"],
    de_h1="Benachrichtigungs-Pipeline",
    de_desc="Pluggable Benachrichtigungskanäle (Telegram, Discord, Slack, Webhooks).",
    de_cards=["7.3 Mehrkanal-Benachrichtigungen (Telegram, Discord, Slack)"]
)

add_sec(
    "sec-ops-proxy", "07",
    en_h1="Proxy Pool Management",
    en_desc="Proxy rotation, latency auto-quarantine, and bandwidth quotas.",
    en_cards=["7.4 Proxy Manager Strategy"],
    id_h1="Manajemen Pool Proksi",
    id_desc="Rotasi proksi cerdas, karantina latensi otomatis, dan kuota konsumsi bandwidth.",
    id_cards=["7.4 Strategi Manajer Proksi & Karantina Latensi"],
    zh_h1="代理池管理与自适应隔离策略",
    zh_desc="多协议代理轮换、自适应高延迟节点熔断隔离、失败重试与带宽预算配额管理。",
    zh_cards=["7.4 代理池管理策略与自适应延迟隔离"],
    es_h1="Gestión del Grupo de Proxies",
    es_desc="Rotación de proxies, autocuarentena por latencia y cuotas de ancho de banda.",
    es_cards=["7.4 Estrategia del administrador de proxies y cuarentena"],
    ja_h1="プロキシプール管理",
    ja_desc="プロキシローテーション、レイテンシによる自動隔離、帯域幅クォータ管理。",
    ja_cards=["7.4 プロキシ管理戦略とレイテンシ隔離"],
    ru_h1="Управление пулом прокси",
    ru_desc="Ротация прокси, автоматическая изоляция узлов с высокой задержкой и квоты трафика.",
    ru_cards=["7.4 Стратегия управления пулом прокси и изоляция задержек"],
    de_h1="Proxy-Pool-Verwaltung",
    de_desc="Proxy-Rotation, automatische Latenz-Quarantäne und Bandbreitenkontingente.",
    de_cards=["7.4 Proxy-Manager-Strategie & Quarantäne"]
)

add_sec(
    "sec-ops-sessions", "07",
    en_h1="Session and Cookie Management",
    en_desc="Persistent per-domain sticky sessions and interactive cookie login.",
    en_cards=["7.5 Session Storage"],
    en_codeHeaders=["BASH // SESSION LOGIN COMMANDS"],
    id_h1="Vault Sesi & Cookie",
    id_desc="Sesi sticky per-domain yang persisten dan alur login cookie interaktif menggunakan browser headful.",
    id_cards=["7.5 Penyimpanan Sesi & Manajemen Cookie"],
    id_codeHeaders=["BASH // PERINTAH LOGIN SESI"],
    zh_h1="粘性会话与持久化 Cookie 管理",
    zh_desc="按目标域名隔离的持久化粘性会话、带界面交互式登录捕获与 Cookie 加密存储规范。",
    zh_cards=["7.5 粘性会话与持久化 Cookie 管理"],
    zh_codeHeaders=["BASH // 会话交互式登录指令"],
    es_h1="Gestión de Sesiones y Cookies",
    es_desc="Sesiones fijas persistentes por dominio e inicio de sesión interactivo con cookies.",
    es_cards=["7.5 Almacenamiento de sesiones y gestión de cookies"],
    es_codeHeaders=["BASH // COMANDOS DE INICIO DE SESIÓN"],
    ja_h1="セッションおよびクッキーの管理",
    ja_desc="ドメインごとの永続的なスティッキーセッションと対話型クッキーログイン。",
    ja_cards=["7.5 セッションストレージとクッキー管理"],
    ja_codeHeaders=["BASH // セッションログインコマンド"],
    ru_h1="Управление сессиями и cookie",
    ru_desc="Постоянные сессии с привязкой к доменам и интерактивный вход для сбора cookie.",
    ru_cards=["7.5 Хранилище сессий и управление cookie"],
    ru_codeHeaders=["BASH // КОМАНДЫ ДЛЯ АВТОРИЗАЦИИ СЕССИИ"],
    de_h1="Sitzungs- und Cookie-Verwaltung",
    de_desc="Persistente domänenspezifische Sticky-Sessions und interaktiver Cookie-Login.",
    de_cards=["7.5 Sitzungs- & Cookie-Speicherverwaltung"],
    de_codeHeaders=["BASH // SITZUNGS-LOGIN-BEFEHLE"]
)

# ==========================================
# MODULE 08: OUTPUT AND EXPORTS
# ==========================================
add_sec(
    "sec-output-structure", "08",
    en_h1="Output Directory Structure",
    en_desc="Run output artifacts layout.",
    en_cards=["8.1 Artifact Organization"],
    en_codeHeaders=["TEXT // OUTPUT DIRECTORY LAYOUT"],
    id_h1="Struktur Direktori Output",
    id_desc="Tata letak artefak hasil eksekusi crawl pada sistem file.",
    id_cards=["8.1 Organisasi Artefak & Direktori Output"],
    id_codeHeaders=["TEKS // TATA LETAK DIREKTORI OUTPUT"],
    zh_h1="输出目录组织结构与成果物规整",
    zh_desc="每次抓取运行的成果物落盘结构、多媒体资产存储路径以及元数据清单组织规范。",
    zh_cards=["8.1 抓取成果物与输出目录结构"],
    zh_codeHeaders=["文本 // 成果物输出目录组织树"],
    es_h1="Estructura de Directorios de Salida",
    es_desc="Disposición de artefactos generados en la ejecución.",
    es_cards=["8.1 Organización de artefactos y directorios de salida"],
    es_codeHeaders=["TEXTO // DISTRIBUCIÓN DEL DIRECTORIO DE SALIDA"],
    ja_h1="出力ディレクトリ構造",
    ja_desc="クロール実行結果の成果物レイアウト構成。",
    ja_cards=["8.1 成果物および出力ディレクトリの構成"],
    ja_codeHeaders=["テキスト // 出力ディレクトリレイアウト"],
    ru_h1="Структура каталогов вывода",
    ru_desc="Структура файлов и артефактов по завершении цикла сбора данных.",
    ru_cards=["8.1 Организация артефактов и выходной директории"],
    ru_codeHeaders=["ТЕКСТ // СТРУКТУРА КАТАЛОГА ВЫВОДА"],
    de_h1="Ausgabeverzeichnisstruktur",
    de_desc="Layout der Ausführungs-Artefakte.",
    de_cards=["8.1 Artefakt- & Ausgabeverzeichnisorganisation"],
    de_codeHeaders=["TEXT // AUSGABEVERZEICHNIS-LAYOUT"]
)

add_sec(
    "sec-output-manifest", "08",
    en_h1="manifest.json Schema",
    en_desc="Complete results JSON schema documentation.",
    en_cards=["8.2 JSON Payload Fields"],
    id_h1="Skema manifest.json",
    id_desc="Dokumentasi skema JSON lengkap untuk hasil eksekusi crawl.",
    id_cards=["8.2 Kolom Payload JSON (manifest.json)"],
    zh_h1="manifest.json 全量元数据规范",
    zh_desc="抓取结果汇总清单 manifest.json 的 JSON Schema 结构定义与各字段详尽技术规范。",
    zh_cards=["8.2 JSON 数据字段详解 (manifest.json)"],
    es_h1="Esquema manifest.json",
    es_desc="Documentación completa del esquema JSON de resultados.",
    es_cards=["8.2 Campos de carga útil JSON (manifest.json)"],
    ja_h1="manifest.json スキーマ",
    ja_desc="実行結果 JSON スキーマの完全なドキュメント。",
    ja_cards=["8.2 JSON ペイロードフィールド (manifest.json)"],
    ru_h1="Схема manifest.json",
    ru_desc="Полная документация схемы JSON для итогового манифеста.",
    ru_cards=["8.2 Поля полезной нагрузки JSON (manifest.json)"],
    de_h1="manifest.json-Schema",
    de_desc="Vollständige Dokumentation des JSON-Ergebnisschemas.",
    de_cards=["8.2 JSON-Nutzlastfelder (manifest.json)"]
)

add_sec(
    "sec-output-domain", "08",
    en_h1="domain_report.json Schema",
    en_desc="Per-domain crawl metrics report.",
    en_cards=["8.3 Per-Domain Yield Report"],
    id_h1="Skema domain_report.json",
    id_desc="Laporan metrik performa crawl per domain target.",
    id_cards=["8.3 Laporan Hasil per Domain (domain_report.json)"],
    zh_h1="domain_report.json 域名效能报告架构",
    zh_desc="按目标域名聚合统计的请求成功率、WAF 触发次数、下载有效载荷大小与产出效能报告。",
    zh_cards=["8.3 单域名抓取效能报告 (domain_report.json)"],
    es_h1="Esquema domain_report.json",
    es_desc="Informe de métricas de rastreo desglosado por dominio.",
    es_cards=["8.3 Informe de rendimiento por dominio (domain_report.json)"],
    ja_h1="domain_report.json スキーマ",
    ja_desc="ドメインごとのクロール指標とパフォーマンスレポート。",
    ja_cards=["8.3 ドメイン別収量レポート (domain_report.json)"],
    ru_h1="Схема domain_report.json",
    ru_desc="Отчет о метриках сбора данных с разбивкой по каждому домену.",
    ru_cards=["8.3 Отчет об эффективности по доменам (domain_report.json)"],
    de_h1="domain_report.json-Schema",
    de_desc="Messwertebericht pro Domain.",
    de_cards=["8.3 Ertragsbericht pro Domain (domain_report.json)"]
)

add_sec(
    "sec-output-kohya", "08",
    en_h1="Kohya LoRA Dataset Export",
    en_desc="Kohya_ss LoRA dataset ZIP archive generation.",
    en_cards=["8.4 LoRA Dataset Generator"],
    id_h1="Ekspor Dataset Kohya LoRA",
    id_desc="Pembuatan arsip ZIP dataset format Kohya_ss LoRA dengan tag deskriptif otomatis.",
    id_cards=["8.4 Generator Dataset Kohya LoRA"],
    zh_h1="Kohya_ss LoRA 训练数据集一键打包导出",
    zh_desc="自动生成符合 Kohya_ss 规范的图片与配对 .txt 标签文件，一键打包为可直接喂给 SD 训练的 ZIP 压缩包。",
    zh_cards=["8.4 Kohya LoRA 训练数据集生成器"],
    es_h1="Exportación de Conjunto de Datos Kohya LoRA",
    es_desc="Generación de archivos ZIP de conjuntos de datos compatibles con Kohya_ss LoRA.",
    es_cards=["8.4 Generador de conjuntos de datos Kohya LoRA"],
    ja_h1="Kohya LoRA データセットエクスポート",
    ja_desc="Kohya_ss LoRA 形式データセットの ZIP アーカイブ自動生成。",
    ja_cards=["8.4 Kohya LoRA データセットジェネレーター"],
    ru_h1="Экспорт датасетов Kohya LoRA",
    ru_desc="Генерация готовых ZIP-архивов датасетов в формате Kohya_ss LoRA.",
    ru_cards=["8.4 Генератор датасетов для Kohya LoRA"],
    de_h1="Kohya-LoRA-Datensatzexport",
    de_desc="Generierung von ZIP-Archiven für Kohya_ss-LoRA-Datensätze.",
    de_cards=["8.4 Kohya LoRA-Datensatzgenerator"]
)

add_sec(
    "sec-output-rag", "08",
    en_h1="RAG Ingestion Formats",
    en_desc="LLM RAG exports (Markdown chunks and JSONL embeddings).",
    en_cards=["8.5 RAG Export Options"],
    id_h1="Format Ingesti RAG untuk LLM",
    id_desc="Ekspor data halaman untuk RAG LLM (pecahan Markdown terkonsolidasi dan format embedding JSONL).",
    id_cards=["8.5 Opsi Ekspor RAG (Markdown & JSONL)"],
    zh_h1="大模型 RAG 知识库摄取导出格式",
    zh_desc="面向 LLM 检索增强生成 (RAG) 场景，支持按页面切片的规整 Markdown 与用于向量检索的 JSONL 文本嵌入格式。",
    zh_cards=["8.5 针对 LLM 的 RAG 摄取导出格式"],
    es_h1="Formatos de Ingesta para RAG",
    es_desc="Exportaciones para RAG en LLM (fragmentos en Markdown y embeddings en JSONL).",
    es_cards=["8.5 Opciones de exportación RAG (Markdown y JSONL)"],
    ja_h1="RAG 投入用データフォーマット",
    ja_desc="LLM RAG 向けエクスポート (Markdown チャンクおよび JSONL エンベディング)。",
    ja_cards=["8.5 RAG 投入用エクスポート形式 (Markdown / JSONL)"],
    ru_h1="Форматы импорта для RAG",
    ru_desc="Экспорт для RAG в LLM (структурированные фрагменты Markdown и эмбеддинги в JSONL).",
    ru_cards=["8.5 Форматы экспорта для RAG (Markdown и JSONL)"],
    de_h1="RAG-Aufnahmeformate",
    de_desc="LLM-RAG-Exporte (Markdown-Chunks und JSONL-Embeddings).",
    de_cards=["8.5 RAG-Aufnahmeformate (Markdown & JSONL)"]
)

add_sec(
    "sec-output-cas", "08",
    en_h1="Content-Addressable Storage (CAS)",
    en_desc="Global deduplication repository eliminating duplicate file storage across repeated crawls.",
    en_cards=["8.6 Content-Addressable Store Architecture"],
    en_codeHeaders=[
        "PYTHON // CAS DEDUPLICATION & RUN LINKING",
        "TEXT // CAS STORAGE LIFECYCLE"
    ],
    id_h1="Penyimpanan Berbasis Konten (CAS)",
    id_desc="Repositori deduplikasi global instan SHA-256 dengan hardlink NTFS/POSIX tanpa redundansi disk.",
    id_cards=["8.6 Arsitektur Content-Addressable Storage (CAS)"],
    id_codeHeaders=[
        "PYTHON // DEDUPLIKASI CAS & PENAUTAN RUN",
        "TEKS // SIKLUS HIDUP PENYIMPANAN CAS"
    ],
    zh_h1="内容寻址存储底层架构 (CAS)",
    zh_desc="基于 SHA-256 全局内容哈希去重与 NTFS/POSIX 跨目录硬链接技术，消除重复抓取导致的磁盘物理冗余。",
    zh_cards=["8.6 内容寻址存储底层架构 (CAS)"],
    zh_codeHeaders=[
        "PYTHON // CAS 内容哈希去重与抓取软硬链接关联",
        "文本 // CAS 物理存储生命周期架构"
    ],
    es_h1="Almacenamiento Direccionable por Contenido (CAS)",
    es_desc="Repositorio de deduplicación global que elimina archivos duplicados en rastreos repetidos.",
    es_cards=["8.6 Arquitectura de almacenamiento direccionable por contenido (CAS)"],
    es_codeHeaders=[
        "PYTHON // DEDUPLICACIÓN CAS Y ENLACE DE EJECUCIÓN",
        "TEXTO // CICLO DE VIDA DE ALMACENAMIENTO CAS"
    ],
    ja_h1="コンテンツアドレス指定ストレージ (CAS)",
    ja_desc="反復クロール全体で重複ファイルのディスク消費をゼロにするグローバル重複排除ストレージ。",
    ja_cards=["8.6 コンテンツアドレス指定ストレージ (CAS) アーキテクチャ"],
    ja_codeHeaders=[
        "PYTHON // CAS 重複排除と実行リンク",
        "テキスト // CAS ストレージのライフサイクル"
    ],
    ru_h1="Хранилище с адресацией по содержимому (CAS)",
    ru_desc="Глобальный репозиторий дедупликации SHA-256, исключающий дубликаты файлов при повторных обходах.",
    ru_cards=["8.6 Архитектура адресации по содержимому (CAS)"],
    ru_codeHeaders=[
        "PYTHON // ДЕДУПЛИКАЦИЯ CAS И СВЯЗЫВАНИЕ ЗАПУСКОВ",
        "ТЕКСТ // ЖИЗНЕННЫЙ ЦИКЛ ХРАНИЛИЩА CAS"
    ],
    de_h1="Inhaltsadressierbarer Speicher (CAS)",
    de_desc="Globales Deduplizierungs-Repository zur Vermeidung doppelter Dateispeicherung bei wiederholten Crawls.",
    de_cards=["8.6 Architektur des inhaltsadressierbaren Speichers (CAS)"],
    de_codeHeaders=[
        "PYTHON // CAS-DEDUPLIZIERUNG & LAUF-VERKNÜPFUNG",
        "TEXT // CAS-SPEICHER-LEBENSZYKLUS"
    ]
)

add_sec(
    "sec-output-parquet", "08",
    en_h1="Apache Parquet Dataset Export",
    en_desc="Columnar Snappy-compressed datasets optimized for Polars, DuckDB, Pandas, and Big Data OLAP pipelines.",
    en_cards=["8.7 Columnar Data Export Pipeline"],
    en_codeHeaders=["PYTHON // PARQUET DATASET GENERATION"],
    id_h1="Ekspor Dataset Apache Parquet",
    id_desc="Dataset kolumnar terkompresi Snappy yang dioptimalkan untuk pipeline Polars, DuckDB, Pandas, dan Big Data OLAP.",
    id_cards=["8.7 Pipeline Ekspor Data Kolumnar (Apache Parquet)"],
    id_codeHeaders=["PYTHON // GENERASI DATASET PARQUET"],
    zh_h1="Apache Parquet 列式分析数据导出",
    zh_desc="Snappy 压缩列式高性能数据集导出，完美适配 Polars、DuckDB、Pandas 以及现代大数据 OLAP 分析流。",
    zh_cards=["8.7 列式存储导出管道 (Apache Parquet)"],
    zh_codeHeaders=["PYTHON // PARQUET 列式数据集生成核心代码"],
    es_h1="Exportación de Datos en Apache Parquet",
    es_desc="Conjuntos de datos columnares con compresión Snappy optimizados para Polars, DuckDB, Pandas y pipelines OLAP.",
    es_cards=["8.7 Pipeline de exportación de datos columnares (Apache Parquet)"],
    es_codeHeaders=["PYTHON // GENERACIÓN DE CONJUNTOS DE DATOS PARQUET"],
    ja_h1="Apache Parquet データセットエクスポート",
    ja_desc="Polars、DuckDB、Pandas、ビッグデータ OLAP パイプライン向けに最適化された Snappy 圧縮列指向データセット。",
    ja_cards=["8.7 列指向データエクスポートパイプライン (Apache Parquet)"],
    ja_codeHeaders=["PYTHON // PARQUET データセットの生成"],
    ru_h1="Экспорт датасетов в Apache Parquet",
    ru_desc="Колоночные датасеты со сжатием Snappy, оптимизированные для аналитических пайплайнов Polars, DuckDB, Pandas и OLAP.",
    ru_cards=["8.7 Пайплайн колоночного экспорта данных (Apache Parquet)"],
    ru_codeHeaders=["PYTHON // ГЕНЕРАЦИЯ ДАТАСЕТОВ PARQUET"],
    de_h1="Apache-Parquet-Datensatzexport",
    de_desc="Spaltenorientierte, Snappy-komprimierte Datensätze, optimiert für Polars, DuckDB, Pandas und Big Data OLAP-Pipelines.",
    de_cards=["8.7 Spaltenorientierte Datenexport-Pipeline (Apache Parquet)"],
    de_codeHeaders=["PYTHON // PARQUET-DATENSATZGENERIERUNG"]
)

print("Modules 06, 07, 08 added.")

# ==========================================
# MODULE 09: TESTING AND TROUBLESHOOTING
# ==========================================
add_sec(
    "sec-test-pytest", "09",
    en_h1="Running pytest",
    en_desc="Executing the automated test suite.",
    en_cards=["9.1 Automated Pytest Suite"],
    en_codeHeaders=["POWERSHELL // RUN FULL TEST SUITE"],
    id_h1="Menjalankan Pengujian pytest",
    id_desc="Eksekusi suite pengujian unit dan integrasi otomatis secara komprehensif.",
    id_cards=["9.1 Suite Pengujian Otomatis Pytest"],
    id_codeHeaders=["POWERSHELL // JALANKAN TEST SUITE LENGKAP"],
    zh_h1="执行 pytest 自动化测试套件",
    zh_desc="运行覆盖核心架构、反爬管道与存储系统的完整自动化单元与集成测试套件。",
    zh_cards=["9.1 自动化 Pytest 测试套件"],
    zh_codeHeaders=["POWERSHELL // 运行完整测试套件"],
    es_h1="Ejecución de Pruebas con pytest",
    es_desc="Ejecución del conjunto de pruebas automatizadas y de integración.",
    es_cards=["9.1 Suite automatizada de pruebas Pytest"],
    es_codeHeaders=["POWERSHELL // EJECUTAR SUITE DE PRUEBAS COMPLETA"],
    ja_h1="pytest の実行",
    ja_desc="自動テストスイートの実行とカバレッジの確認。",
    ja_cards=["9.1 自動化された Pytest スイート"],
    ja_codeHeaders=["POWERSHELL // 完全なテストスイートを実行"],
    ru_h1="Запуск набора тестов pytest",
    ru_desc="Выполнение полного автоматизированного набора модульных и интеграционных тестов.",
    ru_cards=["9.1 Автоматизированный набор тестов Pytest"],
    ru_codeHeaders=["POWERSHELL // ЗАПУСК ПОЛНОГО НАБОРА ТЕСТОВ"],
    de_h1="Ausführen von pytest",
    de_desc="Ausführen der automatisierten Test-Suite.",
    de_cards=["9.1 Automatisierte Pytest-Suite"],
    de_codeHeaders=["POWERSHELL // KOMPLETTE TEST-SUITE AUSFÜHREN"]
)

add_sec(
    "sec-test-tdai", "09",
    en_h1="Verification Protocol (TDAI)",
    en_desc="Test-Driven AI verification rules and RED-GREEN-REFACTOR protocol.",
    en_cards=["9.2 Empirical Verification Protocol"],
    en_alerts=[{"title": "[!] MANDATORY RULE", "bodyHtml": "Never declare a feature or fix complete without running empirical runtime verification commands and demonstrating clean test passes."}],
    id_h1="Protokol Verifikasi (TDAI)",
    id_desc="Aturan verifikasi AI Berbasis Pengujian (TDAI) dan protokol siklus RED-GREEN-REFACTOR.",
    id_cards=["9.2 Protokol Verifikasi Empiris (TDAI)"],
    id_alerts=[{"title": "[!] ATURAN WAJIB", "bodyHtml": "Jangan pernah menyatakan fitur atau perbaikan selesai tanpa menjalankan perintah verifikasi runtime empiris dan mendemonstrasikan hasil pengujian yang 100% lulus."}],
    zh_h1="经验性实机验证规范 (TDAI)",
    zh_desc="测试驱动 AI 开发 (TDAI) 验证规范与不可妥协的 RED-GREEN-REFACTOR 质量门禁协议。",
    zh_cards=["9.2 经验性实机验证规范 (TDAI)"],
    zh_alerts=[{"title": "[!] 强制执行规则", "bodyHtml": "严禁在未执行端到端实机验证命令且未出具完整的测试通过证据前，宣布任何功能或 Bug 修复已完成！必须展示确凿的通过日志。"}],
    es_h1="Protocolo de Verificación Empírica (TDAI)",
    es_desc="Reglas de verificación de IA guiada por pruebas y protocolo RED-GREEN-REFACTOR.",
    es_cards=["9.2 Protocolo de verificación empírica (TDAI)"],
    es_alerts=[{"title": "[!] REGLA OBLIGATORIA", "bodyHtml": "Nunca declare una función o corrección completa sin ejecutar comandos empíricos de verificación en tiempo de ejecución y demostrar aprobaciones de prueba limpias."}],
    ja_h1="実証的検証プロトコル (TDAI)",
    ja_desc="テスト駆動 AI 検証ルールと RED-GREEN-REFACTOR プロトコル。",
    ja_cards=["9.2 実証的検証プロトコル (TDAI)"],
    ja_alerts=[{"title": "[!] 必須ルール", "bodyHtml": "実機ランタイム検証コマンドを実行し、完全なテスト合格を実証することなく、機能や修正の完了を宣言しないでください。"}],
    ru_h1="Протокол эмпирической верификации (TDAI)",
    ru_desc="Правила верификации на основе тестов (TDAI) и цикл RED-GREEN-REFACTOR.",
    ru_cards=["9.2 Эмпирический протокол верификации (TDAI)"],
    ru_alerts=[{"title": "[!] ОБЯЗАТЕЛЬНОЕ ПРАВИЛО", "bodyHtml": "Никогда не объявляйте задачу или исправление завершенными без запуска эмпирических команд проверки в реальном времени и демонстрации успешных тестов."}],
    de_h1="Verifikationsprotokoll (TDAI)",
    de_desc="Testgetriebene KI-Verifikationsregeln und RED-GREEN-REFACTOR-Protokoll.",
    de_cards=["9.2 Empirisches Verifikationsprotokoll (TDAI)"],
    de_alerts=[{"title": "[!] VERBINDLICHE REGEL", "bodyHtml": "Erklären Sie ein Feature oder einen Fix niemals für abgeschlossen, ohne empirische Laufzeitüberprüfungsbefehle auszuführen und saubere Testergebnisse nachzuweisen."}]
)

add_sec(
    "sec-test-logs", "09",
    en_h1="Log Diagnostics Recipes",
    en_desc="Log analysis and grep commands for runtime diagnostics.",
    en_cards=["9.3 PowerShell Diagnostic Commands"],
    en_codeHeaders=["POWERSHELL // GREP LOGS FOR ERRORS AND BLOCKS"],
    id_h1="Resep Diagnostik Log",
    id_desc="Analisis log dan perintah grep untuk diagnostik runtime cepat.",
    id_cards=["9.3 Perintah Diagnostik PowerShell & Analisis Log"],
    id_codeHeaders=["POWERSHELL // GREP LOG UNTUK ERROR & PEMBLOKIRAN"],
    zh_h1="日志诊断与错误快速排查配方",
    zh_desc="生产环境日志排查诊断命令集合，包含 HTTP 429 限流与 Cloudflare 拦截规则快速 grep 检索。",
    zh_cards=["9.3 PowerShell 快速排错命令与日志检索"],
    zh_codeHeaders=["POWERSHELL // 错误与反爬拦截日志检索命令"],
    es_h1="Recetas de Diagnóstico de Registros",
    es_desc="Análisis de registros y comandos grep para diagnóstico en tiempo de ejecución.",
    es_cards=["9.3 Comandos de diagnóstico de PowerShell y análisis de logs"],
    es_codeHeaders=["POWERSHELL // BÚSQUEDA DE ERRORES Y BLOQUEOS EN LOGS"],
    ja_h1="ログ診断レシピ",
    ja_desc="実行時診断のためのログ解析と grep コマンド集。",
    ja_cards=["9.3 PowerShell 診断コマンドとログ解析"],
    ja_codeHeaders=["POWERSHELL // エラーおよびブロックのログ検索"],
    ru_h1="Рецепты диагностики по логам",
    ru_desc="Анализ логов и команды grep для быстрой диагностики в рантайме.",
    ru_cards=["9.3 Диагностические команды PowerShell и анализ логов"],
    ru_codeHeaders=["POWERSHELL // ПОИСК ОШИБОК И БЛОКИРОВОК В ЛОГАХ"],
    de_h1="Log-Diagnoserezepte",
    de_desc="Log-Analyse und Grep-Befehle für die Laufzeitdiagnose.",
    de_cards=["9.3 PowerShell-Diagnosebefehle & Log-Analyse"],
    de_codeHeaders=["POWERSHELL // LOGS NACH FEHLERN UND BLOCKADEN DURCHSUCHEN"]
)

add_sec(
    "sec-test-diagnostic", "09",
    en_h1="Operator Diagnostic Matrix",
    en_desc="Exhaustive diagnostic table for operator troubleshooting.",
    en_cards=["9.4 Diagnostic Matrix"],
    id_h1="Matriks Diagnostik Operator",
    id_desc="Tabel diagnostik komprehensif untuk pemecahan masalah operator.",
    id_cards=["9.4 Matriks Diagnostik Operator"],
    zh_h1="运维诊断与故障排除全景矩阵",
    zh_desc="详尽的运维故障排查对照表，覆盖网络异常、内存告警、打码超时与节点失联等常见故障应对方案。",
    zh_cards=["9.4 运维诊断排错对照矩阵"],
    es_h1="Matriz de Diagnóstico del Operador",
    es_desc="Tabla de diagnóstico exhaustiva para la resolución de problemas por parte del operador.",
    es_cards=["9.4 Matriz de diagnóstico del operador"],
    ja_h1="オペレーター診断マトリックス",
    ja_desc="トラブルシューティングのための網羅的なオペレーター向け診断テーブル。",
    ja_cards=["9.4 オペレーター診断マトリックス"],
    ru_h1="Диагностическая матрица оператора",
    ru_desc="Исчерпывающая диагностическая таблица для устранения неполадок оператором.",
    ru_cards=["9.4 Матрица диагностики оператора"],
    de_h1="Operator-Diagnosematrix",
    de_desc="Vollständige Diagnosetabelle für die Fehlerbehebung durch den Operator.",
    de_cards=["9.4 Operator-Diagnosematrix"]
)

add_sec(
    "sec-test-guidelines", "09",
    en_h1="Developer Guidelines",
    en_desc="Mandatory coding rules and workspace standards.",
    en_cards=["9.5 Mandatory Coding Rules"],
    id_h1="Pedoman Pengembang & Standar Kode",
    id_desc="Aturan pengkodean wajib dan standar integritas ruang kerja.",
    id_cards=["9.5 Aturan Pengkodean Wajib Pengembang"],
    zh_h1="核心开发者工程与代码质量规范",
    zh_desc="系统强制性开发规范、严格遵循的代码风格约定以及代码质量红线要求。",
    zh_cards=["9.5 强制性工程编码规范"],
    es_h1="Pautas para Desarrolladores",
    es_desc="Reglas obligatorias de desarrollo y estándares de calidad del espacio de trabajo.",
    es_cards=["9.5 Reglas obligatorias de desarrollo de código"],
    ja_h1="開発者ガイドライン",
    ja_desc="必須のコーディング規約およびワークスペースの品質基準。",
    ja_cards=["9.5 開発者向け必須コーディング規約"],
    ru_h1="Руководство для разработчиков",
    ru_desc="Обязательные стандарты написания кода и требования к качеству проекта.",
    ru_cards=["9.5 Обязательные стандарты разработки кода"],
    de_h1="Entwickler-Richtlinien",
    de_desc="Verbindliche Programmierregeln und Workspace-Standards.",
    de_cards=["9.5 Verbindliche Entwicklungsregeln"]
)

# ==========================================
# MODULE 10: THREAT MODEL & SECURITY
# ==========================================
add_sec(
    "sec-threat-overview", "10",
    en_h1="Security Architecture & v0.30.0 Verification",
    en_desc="Authoritative threat model, STRIDE architectural contract, and empirical verification matrix for v0.30.0 distributed scaling.",
    en_cards=[
        "10.1 Trust Boundaries & Data Flow Architecture",
        "10.1.1 STRIDE Threat Categorization",
        "10.1.2 Cross-Cutting Invariants"
    ],
    en_codeHeaders=["ARCHITECTURE // v0.30.0 DISTRIBUTED TRUST BOUNDARIES & DATA FLOW"],
    en_alerts=[
        {
            "title": "PRODUCTION RELEASE // v0.30.0 VERIFIED & CERTIFIED",
            "bodyHtml": "All three threat-modeled frontiers (Distributed Task Leasing, Cloud CAS Synchronization, Vision-Language DOM Healing) specified in this module are <strong>fully implemented, adversarially tested, and empirically CI verified</strong> in the v0.30.0 release across Ubuntu, macOS, and Windows runners."
        },
        {
            "title": "MANDATORY ARCHITECTURAL CONTRACT",
            "bodyHtml": "This specification is the authoritative baseline for all v0.30.0 feature implementations. Every acceptance criterion (AC1.1 through AC3.6) must have a corresponding automated test in <code>tests/</code> before any component is considered release-ready."
        }
    ],
    id_h1="Arsitektur Keamanan & Verifikasi v0.30.0",
    id_desc="Model ancaman otoritatif, kontrak arsitektur STRIDE, dan matriks verifikasi empiris untuk penskalaan terdistribusi v0.30.0.",
    id_cards=[
        "10.1 Batas Kepercayaan & Arsitektur Aliran Data",
        "10.1.1 Kategorisasi Ancaman STRIDE",
        "10.1.2 Invarian Lintas-Sektor"
    ],
    id_codeHeaders=["ARSITEKTUR // v0.30.0 BATAS KEPERCAYAAN TERDISTRIBUSI & ALIRAN DATA"],
    id_alerts=[
        {
            "title": "RILIS PRODUKSI // v0.30.0 TERVERIFIKASI & TERSERTIFIKASI",
            "bodyHtml": "Ketiga aspek model ancaman (Leasing Tugas Terdistribusi, Sinkronisasi Cloud CAS, Pemulihan DOM Vision-Language) yang ditentukan dalam modul ini telah <strong>diimplementasikan sepenuhnya, diuji secara adversarial, dan diverifikasi CI secara empiris</strong> pada rilis v0.30.0 di runner Ubuntu, macOS, dan Windows."
        },
        {
            "title": "KONTRAK ARSITEKTUR WAJIB",
            "bodyHtml": "Spesifikasi ini adalah garis dasar otoritatif untuk seluruh implementasi fitur v0.30.0. Setiap kriteria penerimaan (AC1.1 hingga AC3.6) wajib memiliki tes otomatis di <code>tests/</code> sebelum komponen apa pun dianggap siap rilis."
        }
    ],
    zh_h1="安全架构与 v0.30.0 规范验证",
    zh_desc="权威威胁建模规范、STRIDE 架构契约以及 v0.30.0 分布式扩展能力的实机经验验证矩阵。",
    zh_cards=[
        "10.1 信任边界与分布式数据流架构",
        "10.1.1 STRIDE 威胁建模分类",
        "10.1.2 跨组件核心不变量"
    ],
    zh_codeHeaders=["架构图 // v0.30.0 分布式信任边界与数据流"],
    zh_alerts=[
        {
            "title": "生产版本发布 // v0.30.0 已全面验证与认证",
            "bodyHtml": "本模块规定的三大前沿架构领域 (分布式任务租约、云端 CAS 存储同步、视觉大模型 DOM 自愈) 在 v0.30.0 版本中已<strong>完全实现、经受对抗性测试并经验证在 CI (Ubuntu/macOS/Windows) 矩阵中全部通过</strong>。"
        },
        {
            "title": "强制性架构契约",
            "bodyHtml": "本技术规范是 v0.30.0 所有功能实现的权威基准。在任何组件被批准发布前，每个验收标准 (AC1.1 至 AC3.6) 必须在 <code>tests/</code> 中拥有对应的自动化测试用例。"
        }
    ],
    es_h1="Arquitectura de Seguridad y Verificación v0.30.0",
    es_desc="Modelo de amenazas autorizado, contrato arquitectónico STRIDE y matriz de verificación empírica para el escalado distribuido v0.30.0.",
    es_cards=[
        "10.1 Límites de confianza y arquitectura de flujo de datos",
        "10.1.1 Categorización de amenazas STRIDE",
        "10.1.2 Invariantes transversales"
    ],
    es_codeHeaders=["ARQUITECTURA // LÍMITES DE CONFIANZA DISTRIBUIDOS Y FLUJO DE DATOS v0.30.0"],
    es_alerts=[
        {
            "title": "VERSIÓN DE PRODUCCIÓN // v0.30.0 VERIFICADA Y CERTIFICADA",
            "bodyHtml": "Las tres fronteras modeladas contra amenazas (Arrendamiento de tareas distribuidas, Sincronización de CAS en la nube, Autorreparación DOM con visión y lenguaje) están <strong>completamente implementadas, probadas de forma adversaria y verificadas en CI</strong> en v0.30.0."
        },
        {
            "title": "CONTRATO ARQUITECTÓNICO OBLIGATORIO",
            "bodyHtml": "Esta especificación es la línea base autorizada para todas las implementaciones de características de v0.30.0. Cada criterio de aceptación (AC1.1 a AC3.6) debe tener una prueba automatizada correspondiente en <code>tests/</code>."
        }
    ],
    ja_h1="セキュリティアーキテクチャと v0.30.0 の検証",
    ja_desc="v0.30.0 分散スケーリングのための権威ある脅威モデル、STRIDE アーキテクチャコントラクト、実証的検証マトリックス。",
    ja_cards=[
        "10.1 トラストバウンダリとデータフローアーキテクチャ",
        "10.1.1 STRIDE脅威カテゴリ",
        "10.1.2 横断的インバリアント"
    ],
    ja_codeHeaders=["アーキテクチャ // v0.30.0 分散トラストバウンダリとデータフロー"],
    ja_alerts=[
        {
            "title": "本番リリース // v0.30.0 検証および認定完了",
            "bodyHtml": "本モジュールで規定された3つの最先端アーキテクチャ領域（分散タスクリース、クラウドCAS同期、VLMによるDOM自己修復）は、v0.30.0 リリースにおいて<strong>完全に実装され、敵対的テストおよび CI 検証（Ubuntu/macOS/Windows）をすべてクリア</strong>しています。"
        },
        {
            "title": "必須アーキテクチャ契約",
            "bodyHtml": "本仕様書は、v0.30.0 のすべての機能実装における信頼できる基準です。各受入基準（AC1.1～AC3.6）は、コンポーネントがリリース準備完了とみなされる前に、<code>tests/</code> に対応する自動テストを備えている必要があります。"
        }
    ],
    ru_h1="Архитектура безопасности и верификация v0.30.0",
    ru_desc="Официальная модель угроз, архитектурный контракт STRIDE и матрица эмпирической проверки распределенного масштабирования v0.30.0.",
    ru_cards=[
        "10.1 Границы доверия и архитектура потоков данных",
        "10.1.1 Категоризация угроз STRIDE",
        "10.1.2 Сквозные инварианты"
    ],
    ru_codeHeaders=["АРХИТЕКТУРА // РАСПРЕДЕЛЕННЫЕ ГРАНИЦЫ ДОВЕРИЯ И ПОТОК ДАННЫХ v0.30.0"],
    ru_alerts=[
        {
            "title": "ПРОИЗВОДСТВЕННЫЙ РЕЛИЗ // v0.30.0 ПРОВЕРЕН И СЕРТИФИЦИРОВАН",
            "bodyHtml": "Все три области моделирования угроз (распределенная аренда задач, облачная синхронизация CAS, исправление DOM через VLM) в версии v0.30.0 <strong>полностью реализованы, протестированы на устойчивость к атакам и верифицированы в матрице CI</strong>."
        },
        {
            "title": "ОБЯЗАТЕЛЬНЫЙ АРХИТЕКТУРНЫЙ КОНТРАКТ",
            "bodyHtml": "Настоящая спецификация является обязательным эталоном для всех реализаций в версии v0.30.0. Каждый критерий приемки (AC1.1–AC3.6) должен быть подкреплен автоматизированным тестом в <code>tests/</code>."
        }
    ],
    de_h1="Sicherheitsarchitektur & v0.30.0 Verifikation",
    de_desc="Autoritatives Bedrohungsmodell, STRIDE-Architekturvertrag und empirische Verifikationsmatrix für die verteilte v0.30.0-Skalierung.",
    de_cards=[
        "10.1 Vertrauensgrenzen & Datenflussarchitektur",
        "10.1.1 STRIDE-Bedrohungskategorisierung",
        "10.1.2 Übergreifende Invarianten"
    ],
    de_codeHeaders=["ARCHITEKTUR // v0.30.0 VERTEILTE VERTRAUENSGRENZEN & DATENFLUSS"],
    de_alerts=[
        {
            "title": "PRODUKTIONS-RELEASE // v0.30.0 VERIFIZIERT & ZERTIFIZIERT",
            "bodyHtml": "Alle drei in diesem Modul spezifizierten Bedrohungsmodell-Frontbereiche (Distributed Task Leasing, Cloud CAS Synchronization, Vision-Language DOM Healing) sind im v0.30.0-Release auf Ubuntu-, macOS- und Windows-Runnern <strong>vollständig implementiert, adversarial getestet und empirisch durch die CI verifiziert</strong>."
        },
        {
            "title": "VERBINDLICHER ARCHITEKTURVERTRAG",
            "bodyHtml": "Diese Spezifikation bildet die maßgebliche Baseline für alle v0.30.0-Feature-Implementierungen. Jedes Akzeptanzkriterium (AC1.1 bis AC3.6) muss über einen entsprechenden automatisierten Test in <code>tests/</code> verfügen, bevor eine Komponente als freigabefähig gilt."
        }
    ]
)

add_sec(
    "sec-threat-leasing", "10_c1",
    en_h1="Distributed Task Leasing Threat Matrix",
    en_desc="STRIDE vulnerability analysis, attack scenarios, and atomic mitigation mechanisms for Redis Stream worker daemons.",
    en_cards=[
        "10.2 Component 1 Design Overview",
        "10.2.1 Threat & Vulnerability Matrix (Component 1)",
        "10.2.2 Detailed Mitigation Specifications"
    ],
    en_codeHeaders=["PYTHON // ATOMIC IDEMPOTENCY LOCK ACQUISITION"],
    en_alerts=[
        {
            "title": "COMPONENT 1 IMPLEMENTED & VERIFIED // AC1.1–AC1.7 PASSED",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>, <code>DistributedWorkerNode</code>, and CLI worker daemons (<code>src.cli.worker</code>) are fully implemented and verified against acceptance criteria AC1.1 through AC1.7. Automated test verification is backed by 98 tests across <code>tests/core/test_task_schema.py</code> (84 fuzz tests), <code>tests/core/test_worker_pool.py</code>, and <code>tests/core/test_distributed_worker.py</code>."
        }
    ],
    id_h1="Matriks Ancaman Task Leasing Terdistribusi",
    id_desc="Analisis kerentanan STRIDE, skenario serangan, dan mekanisme mitigasi atomik untuk worker daemon Redis Stream.",
    id_cards=[
        "10.2 Gambaran Desain Komponen 1",
        "10.2.1 Matriks Ancaman & Kerentanan (Komponen 1)",
        "10.2.2 Spesifikasi Mitigasi Rinci"
    ],
    id_codeHeaders=["PYTHON // AKUISISI KUNCI IDEMPOTEN ATOMIK"],
    id_alerts=[
        {
            "title": "KOMPONEN 1 TERIMPLEMENTASI & TERVERIFIKASI // AC1.1–AC1.7 LULUS",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>, <code>DistributedWorkerNode</code>, dan daemon worker CLI (<code>src.cli.worker</code>) telah diimplementasikan sepenuhnya dan diverifikasi terhadap kriteria penerimaan AC1.1 hingga AC1.7 dengan 98 pengujian otomatis."
        }
    ],
    zh_h1="分布式任务租约威胁矩阵 (组件 1)",
    zh_desc="针对 Redis Streams 工作节点的 STRIDE 脆弱性深入分析、恶意攻击场景建模以及原子化防御缓解机制。",
    zh_cards=[
        "10.2 组件 1 设计概览 (分布式任务租约)",
        "10.2.1 组件 1 威胁与漏洞矩阵",
        "10.2.2 详细防御与缓解规范"
    ],
    zh_codeHeaders=["PYTHON // 原子幂等性锁获取与超时续约实现"],
    zh_alerts=[
        {
            "title": "组件 1 已实现并全面验证 // AC1.1–AC1.7 验收测试 100% 通过",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>、<code>DistributedWorkerNode</code> 以及 CLI 独立工作守护进程已针对 AC1.1 至 AC1.7 验收标准全面实现并通过实机验证，backed by 98 项自动化测试用例。"
        }
    ],
    es_h1="Matriz de Amenazas de Asignación de Tareas Distribuidas",
    es_desc="Análisis de vulnerabilidad STRIDE, escenarios de ataque y mecanismos de mitigación atómica para demonios trabajadores de Redis Stream.",
    es_cards=[
        "10.2 Resumen de diseño del componente 1",
        "10.2.1 Matriz de amenazas y vulnerabilidades (Componente 1)",
        "10.2.2 Especificaciones detalladas de mitigación"
    ],
    es_codeHeaders=["PYTHON // ADQUISICIÓN DE BLOQUEO DE IDEMPOTENCIA ATÓMICA"],
    es_alerts=[
        {
            "title": "COMPONENTE 1 IMPLEMENTADO Y VERIFICADO // AC1.1–AC1.7 APROBADOS",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>, <code>DistributedWorkerNode</code> y los demonios CLI están completamente implementados y verificados contra los criterios de aceptación AC1.1 a AC1.7."
        }
    ],
    ja_h1="分散タスクリース脅威マトリックス (コンポーネント 1)",
    ja_desc="Redis Stream ワーカーデーモンのための STRIDE 脆弱性分析、攻撃シナリオ、アトミックな緩和メカニズム。",
    ja_cards=[
        "10.2 コンポーネント 1 設計概要",
        "10.2.1 脅威および脆弱性マトリックス (コンポーネント 1)",
        "10.2.2 詳細な緩和仕様"
    ],
    ja_codeHeaders=["PYTHON // アトミックな冪等性ロックの取得"],
    ja_alerts=[
        {
            "title": "コンポーネント 1 実装および検証完了 // AC1.1–AC1.7 合格",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>、<code>DistributedWorkerNode</code>、CLI ワーカーデーモンは受入基準 AC1.1～AC1.7 に対して完全に実装され、98件の自動テストによって実証検証されています。"
        }
    ],
    ru_h1="Матрица угроз распределенной аренды задач (Компонент 1)",
    ru_desc="Анализ уязвимостей по модели STRIDE, сценарии атак и механизмы атомарной защиты для воркеров Redis Stream.",
    ru_cards=[
        "10.2 Обзор архитектуры компонента 1",
        "10.2.1 Матрица угроз и уязвимостей (Компонент 1)",
        "10.2.2 Детальные спецификации защиты"
    ],
    ru_codeHeaders=["PYTHON // АТОМАРНЫЙ ЗАХВАТ БЛОКИРОВКИ ИДЕМПОТЕНТНОСТИ"],
    ru_alerts=[
        {
            "title": "КОМПОНЕНТ 1 РЕАЛИЗОВАН И ПРОВЕРЕН // AC1.1–AC1.7 ПРОЙДЕНЫ",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>, <code>DistributedWorkerNode</code> и CLI-воркеры полностью реализованы и проверены на соответствие критериям приемки AC1.1–AC1.7 (98 тестов)."
        }
    ],
    de_h1="Distributed-Task-Leasing-Bedrohungsmatrix",
    de_desc="STRIDE-Schwachstellenanalyse, Angriffsszenarien und atomare Minderungsmechanismen für Redis-Stream-Worker-Daemons.",
    de_cards=[
        "10.2 Designübersicht Komponente 1",
        "10.2.1 Bedrohungs- & Schwachstellenmatrix (Komponente 1)",
        "10.2.2 Detaillierte Minderungs-Spezifikationen"
    ],
    de_codeHeaders=["PYTHON // ATOMARER IDEMPOTENZ-SPERREN-ERWERB"],
    de_alerts=[
        {
            "title": "KOMPONENTE 1 IMPLEMENTIERT & VERIFIZIERT // AC1.1–AC1.7 BESTANDEN",
            "bodyHtml": "<code>RedisStreamTaskBroker</code>, <code>DistributedWorkerNode</code> und CLI-Worker-Daemons (<code>src.cli.worker</code>) sind vollständig implementiert und anhand der Akzeptanzkriterien AC1.1 bis AC1.7 verifiziert. Die automatische Testverifikation wird durch 98 Tests gestützt."
        }
    ]
)

add_sec(
    "sec-threat-cas", "10_c2",
    en_h1="Cloud CAS Synchronization Threat Matrix",
    en_desc="Defense-in-depth specifications, cryptographic verification, and SSRF prevention for S3 / Cloudflare R2 / MinIO storage backends.",
    en_cards=[
        "10.3 Component 2 Design Overview",
        "10.3.1 Threat & Vulnerability Matrix (Component 2)",
        "10.3.2 Cryptographic Hash Path Enforcement"
    ],
    en_codeHeaders=["PYTHON // CAS KEY PATH VALIDATION & CHECKSUM VERIFICATION"],
    en_alerts=[
        {
            "title": "PRODUCTION CERTIFIED // COMPONENT 2 FULLY IMPLEMENTED",
            "bodyHtml": "<code>CASCloudSyncer</code> and S3/R2/MinIO cloud storage backends are <strong>fully implemented and verified</strong> in v0.30.0 with 100% test pass rates across AC2.1-AC2.7, zero-boto minimal install validation, and unconditional SSRF guards."
        }
    ],
    id_h1="Matriks Ancaman Sinkronisasi Cloud CAS",
    id_desc="Spesifikasi pertahanan berlapis, verifikasi kriptografis, dan pencegahan SSRF untuk backend penyimpanan S3 / Cloudflare R2 / MinIO.",
    id_cards=[
        "10.3 Gambaran Desain Komponen 2",
        "10.3.1 Matriks Ancaman & Kerentanan (Komponen 2)",
        "10.3.2 Penegakan Jalur Hash Kriptografis"
    ],
    id_codeHeaders=["PYTHON // VALIDASI JALUR KUNCI CAS & VERIFIKASI CHECKSUM"],
    id_alerts=[
        {
            "title": "TERSERTIFIKASI PRODUKSI // KOMPONEN 2 TERIMPLEMENTASI LENGKAP",
            "bodyHtml": "<code>CASCloudSyncer</code> dan backend cloud storage S3/R2/MinIO telah <strong>diimplementasikan dan diverifikasi sepenuhnya</strong> pada v0.30.0 dengan tingkat kelulusan tes 100% di seluruh AC2.1-AC2.7."
        }
    ],
    zh_h1="云端 CAS 存储同步威胁矩阵 (组件 2)",
    zh_desc="面向 S3 / Cloudflare R2 / MinIO 存储后端的纵深防御体系规范、强密码学校验与严苛的 SSRF 防护机制。",
    zh_cards=[
        "10.3 组件 2 设计概览 (云端 CAS 同步)",
        "10.3.1 组件 2 威胁与漏洞矩阵",
        "10.3.2 加密哈希路径强制隔离机制"
    ],
    zh_codeHeaders=["PYTHON // CAS 存储键路径合法性校验与校验和校验"],
    zh_alerts=[
        {
            "title": "生产环境认证 // 组件 2 已完全实现并发布",
            "bodyHtml": "<code>CASCloudSyncer</code> 与 S3/R2/MinIO 对象存储云端同步组件在 v0.30.0 中已<strong>完全实现并验证通过</strong>，AC2.1-AC2.7 测试用例 100% 通过，具备零 Boto 轻量化运行与无条件 SSRF 边界拦截。"
        }
    ],
    es_h1="Matriz de Amenazas de Sincronización de CAS en la Nube",
    es_desc="Especificaciones de defensa en profundidad, verificación criptográfica y prevención de SSRF para backends S3 / Cloudflare R2 / MinIO.",
    es_cards=[
        "10.3 Resumen de diseño del componente 2",
        "10.3.1 Matriz de amenazas y vulnerabilidades (Componente 2)",
        "10.3.2 Aplicación de ruta de hash criptográfico"
    ],
    es_codeHeaders=["PYTHON // VALIDACIÓN DE RUTA DE CLAVE CAS Y VERIFICACIÓN DE SUMA DE CONTROL"],
    es_alerts=[
        {
            "title": "CERTIFICADO PARA PRODUCCIÓN // COMPONENTE 2 TOTALMENTE IMPLEMENTADO",
            "bodyHtml": "<code>CASCloudSyncer</code> y los backends de almacenamiento en la nube están <strong>totalmente implementados y verificados</strong> en v0.30.0 con tasas de aprobación del 100% en AC2.1-AC2.7."
        }
    ],
    ja_h1="クラウド CAS 同期脅威マトリックス (コンポーネント 2)",
    ja_desc="S3 / Cloudflare R2 / MinIO ストレージバックエンド向けの多層防御仕様、暗号学的検証、SSRF 防止設計。",
    ja_cards=[
        "10.3 コンポーネント 2 設計概要",
        "10.3.1 脅威および脆弱性マトリックス (コンポーネント 2)",
        "10.3.2 暗号化ハッシュパス強制保護"
    ],
    ja_codeHeaders=["PYTHON // CAS キーパス検証およびチェックサム確認"],
    ja_alerts=[
        {
            "title": "本番認定済み // コンポーネント 2 の完全実装完了",
            "bodyHtml": "<code>CASCloudSyncer</code> および S3/R2/MinIO クラウドストレージバックエンドは、AC2.1～AC2.7 のテスト合格率 100% で v0.30.0 において<strong>完全に実装および検証</strong>されています。"
        }
    ],
    ru_h1="Матрица угроз синхронизации облачного хранилища CAS (Компонент 2)",
    ru_desc="Спецификации эшелонированной обороны, криптографическая проверка и защита от SSRF для хранилищ S3 / Cloudflare R2 / MinIO.",
    ru_cards=[
        "10.3 Обзор архитектуры компонента 2",
        "10.3.1 Матрица угроз и уязвимостей (Компонент 2)",
        "10.3.2 Принудительная изоляция криптографических хэш-путей"
    ],
    ru_codeHeaders=["PYTHON // ВАЛИДАЦИЯ ПУТИ КЛЮЧА CAS И ПРОВЕРКА КОНТРОЛЬНОЙ СУММЫ"],
    ru_alerts=[
        {
            "title": "СЕРТИФИЦИРОВАНО ДЛЯ ПРОДАКШЕНА // КОМПОНЕНТ 2 ПОЛНОСТЬЮ РЕАЛИЗОВАН",
            "bodyHtml": "<code>CASCloudSyncer</code> и бэкенды S3/R2/MinIO <strong>полностью реализованы и проверены</strong> в версии v0.30.0 со 100% успешных тестов по критериям AC2.1–AC2.7."
        }
    ],
    de_h1="Cloud-CAS-Synchronisations-Bedrohungsmatrix",
    de_desc="Defense-in-Depth-Spezifikationen, kryptografische Verifikation und SSRF-Prävention für S3 / Cloudflare R2 / MinIO-Speicher-Backends.",
    de_cards=[
        "10.3 Designübersicht Komponente 2",
        "10.3.1 Bedrohungs- & Schwachstellenmatrix (Komponente 2)",
        "10.3.2 Kryptografische Hash-Pfad-Erzwingung"
    ],
    de_codeHeaders=["PYTHON // CAS-SCHLÜSSEL-PFADVALIDIERUNG & PRÜFSUMMENVERIFIKATION"],
    de_alerts=[
        {
            "title": "PRODUKTIONS-ZERTIFIZIERT // KOMPONENTE 2 VOLLSTÄNDIG IMPLEMENTIERT",
            "bodyHtml": "<code>CASCloudSyncer</code> und S3/R2/MinIO Cloud-Speicher-Backends sind in v0.30.0 mit einer Test-Bestehensquote von 100% über AC2.1-AC2.7, Zero-Boto-Minimalinstallationsvalidierung und bedingungslosen SSRF-Schutzfunktionen <strong>vollständig implementiert und verifiziert</strong>."
        }
    ]
)

add_sec(
    "sec-threat-vlm", "10_c3",
    en_h1="Vision-Language DOM Healing Threat Matrix",
    en_desc="Multimodal AI security controls, adversarial visual prompt injection defenses, and DOM interaction sandboxing for Tier 4 healing.",
    en_cards=[
        "10.4 Component 3 Design Overview",
        "10.4.1 Threat & Vulnerability Matrix (Component 3)",
        "10.4.2 Untrusted Data Framing & Output Guardrails"
    ],
    en_codeHeaders=["PROMPT ARCHITECTURE // SANDBOXED VLM SYSTEM PROMPT"],
    en_alerts=[
        {
            "title": "PRODUCTION CERTIFIED // COMPONENT 3 FULLY IMPLEMENTED",
            "bodyHtml": "<code>VisionDOMHealer</code> (Tier 4 multimodal DOM healing) is <strong>fully implemented and verified</strong> in v0.30.0 with 100% test pass rates across AC3.1-AC3.6, 75-vector prompt injection fuzzing rejection, and a structural default-deny allowlist."
        }
    ],
    id_h1="Matriks Ancaman Pemulihan DOM Vision-Language",
    id_desc="Kontrol keamanan AI multimodal, pertahanan adversarial visual prompt injection, dan sandboxing interaksi DOM untuk Tier 4 healing.",
    id_cards=[
        "10.4 Gambaran Desain Komponen 3",
        "10.4.1 Matriks Ancaman & Kerentanan (Komponen 3)",
        "10.4.2 Pembingkaian Data Tidak Tepercaya & Pembatas Output"
    ],
    id_codeHeaders=["ARSITEKTUR PROMPT // SYSTEM PROMPT VLM TERSANDBOX"],
    id_alerts=[
        {
            "title": "TERSERTIFIKASI PRODUKSI // KOMPONEN 3 TERIMPLEMENTASI LENGKAP",
            "bodyHtml": "<code>VisionDOMHealer</code> (Tier 4 multimodal DOM healing) telah <strong>diimplementasikan dan diverifikasi sepenuhnya</strong> pada v0.30.0 dengan tingkat kelulusan 100% di AC3.1-AC3.6 dan penolakan fuzzing prompt injection 75 vektor."
        }
    ],
    zh_h1="视觉大模型 DOM 自愈威胁矩阵 (组件 3)",
    zh_desc="多模态 AI 安全管控准则、对抗性视觉 Prompt 注入攻击防御规范与 Tier 4 自愈沙箱隔离机制。",
    zh_cards=[
        "10.4 组件 3 设计概览 (VLM 视觉自愈)",
        "10.4.1 组件 3 威胁与漏洞矩阵",
        "10.4.2 不信任数据隔离与输出保护栏"
    ],
    zh_codeHeaders=["PROMPT 架构 // 沙箱化隔离 VLM 系统提示词规范"],
    zh_alerts=[
        {
            "title": "生产环境认证 // 组件 3 已完全实现并发布",
            "bodyHtml": "<code>VisionDOMHealer</code> (第 4 级多模态视觉 DOM 自愈机制) 在 v0.30.0 中已<strong>完全实现并验证通过</strong>，AC3.1-AC3.6 验收测试 100% 通过，成功抵御 75 种对抗性 Prompt 注入攻击向量。"
        }
    ],
    es_h1="Matriz de Amenazas de Autorreparación DOM con Visión y Lenguaje",
    es_desc="Controles de seguridad de IA multimodal, defensas contra inyección de prompts visuales adversarios y aislamiento de interacción DOM.",
    es_cards=[
        "10.4 Resumen de diseño del componente 3",
        "10.4.1 Matriz de amenazas y vulnerabilidades (Componente 3)",
        "10.4.2 Encuadre de datos no confiables y barreras de salida"
    ],
    es_codeHeaders=["ARQUITECTURA DE PROMPT // PROMPT DEL SISTEMA VLM AISLADO"],
    es_alerts=[
        {
            "title": "CERTIFICADO PARA PRODUCCIÓN // COMPONENTE 3 TOTALMENTE IMPLEMENTADO",
            "bodyHtml": "<code>VisionDOMHealer</code> (autorreparación DOM multimodal Nivel 4) está <strong>totalmente implementado y verificado</strong> en v0.30.0 con tasas de aprobación del 100% en AC3.1-AC3.6."
        }
    ],
    ja_h1="Vision-Language DOM 自己修復脅威マトリックス (コンポーネント 3)",
    ja_desc="マルチモーダル AI セキュリティ制御、敵対的ビジュアルプロンプトインジェクション防御、DOM 操作サンドボックス。",
    ja_cards=[
        "10.4 コンポーネント 3 設計概要",
        "10.4.1 脅威および脆弱性マトリックス (コンポーネント 3)",
        "10.4.2 非信頼データのフレーミングと出力ガードレール"
    ],
    ja_codeHeaders=["プロンプトアーキテクチャ // サンドボックス化された VLM システムプロンプト"],
    ja_alerts=[
        {
            "title": "本番認定済み // コンポーネント 3 の完全実装完了",
            "bodyHtml": "<code>VisionDOMHealer</code> (Tier 4 マルチモーダル DOM 修復) は、AC3.1～AC3.6 のテスト合格率 100%、75ベクトルのプロンプトインジェクションファジング拒否率 100% で<strong>完全に実装および検証</strong>されています。"
        }
    ],
    ru_h1="Матрица угроз самовосстановления DOM через Vision-Language (Компонент 3)",
    ru_desc="Меры безопасности мультимодального ИИ, защита от визуальных prompt-инъекций и песочница взаимодействия с DOM.",
    ru_cards=[
        "10.4 Обзор архитектуры компонента 3",
        "10.4.1 Матрица угроз и уязвимостей (Компонент 3)",
        "10.4.2 Обрамление ненадежных данных и барьеры вывода"
    ],
    ru_codeHeaders=["АРХИТЕКТУРА ПРОМПТА // ИЗОЛИРОВАННЫЙ СИСТЕМНЫЙ ПРОМПТ VLM"],
    ru_alerts=[
        {
            "title": "СЕРТИФИЦИРОВАНО ДЛЯ ПРОДАКШЕНА // КОМПОНЕНТ 3 ПОЛНОСТЬЮ РЕАЛИЗОВАН",
            "bodyHtml": "<code>VisionDOMHealer</code> (мультимодальное исправление DOM уровня 4) <strong>полностью реализован и проверен</strong> в версии v0.30.0 со 100% успешных тестов по критериям AC3.1–AC3.6."
        }
    ],
    de_h1="Vision-Language-DOM-Healing-Bedrohungsmatrix",
    de_desc="Multimodale KI-Sicherheitskontrollen, Abwehr adversarieller visueller Prompt-Injections und DOM-Interaktions-Sandboxing für Tier-4-Heilung.",
    de_cards=[
        "10.4 Designübersicht Komponente 3",
        "10.4.1 Bedrohungs- & Schwachstellenmatrix (Komponente 3)",
        "10.4.2 Rahmung nicht vertrauenswürdiger Daten & Ausgabe-Leitplanken"
    ],
    de_codeHeaders=["PROMPT-ARCHITEKTUR // GESANDBOXTER VLM-SYSTEM-PROMPT"],
    de_alerts=[
        {
            "title": "PRODUKTIONS-ZERTIFIZIERT // KOMPONENTE 3 VOLLSTÄNDIG IMPLEMENTIERT",
            "bodyHtml": "<code>VisionDOMHealer</code> (Tier 4 multimodales DOM-Healing) ist in v0.30.0 mit einer 100%igen Test-Bestehensquote über AC3.1-AC3.6, 75-Vektor-Prompt-Injection-Fuzzing-Abweisung und einer strukturellen Default-Deny-Allowlist <strong>vollständig implementiert und verifiziert</strong>."
        }
    ]
)

add_sec(
    "sec-threat-ac", "10_ac",
    en_h1="Acceptance Criteria Verification Matrix (v0.30.0 Production)",
    en_desc="Empirical test specifications, verification methodologies, and audit results validating all 20 acceptance criteria for v0.30.0.",
    en_cards=[
        "10.5.1 Component 1 Acceptance Criteria (Task Leasing)",
        "10.5.2 Component 2 Acceptance Criteria (Cloud CAS)",
        "10.5.3 Component 3 Acceptance Criteria (VLM Healing)"
    ],
    en_alerts=[
        {
            "title": "ALL 20 ACCEPTANCE CRITERIA VERIFIED & CERTIFIED",
            "bodyHtml": "All 20 criteria below (AC1.1 through AC3.6) represent the <strong>core architectural contract</strong> for v0.30.0. Every single criterion is backed by automated tests in <code>tests/</code> passing 100% locally and in GitHub Actions CI matrix."
        },
        {
            "title": "VERIFICATION STANDARD",
            "bodyHtml": "No v0.30.0 pull request or release tag will be approved without 100% test coverage across all 20 acceptance criteria below, backed by unmocked local verification and full GitHub Actions matrix confirmation."
        }
    ],
    id_h1="Matriks Verifikasi Kriteria Penerimaan (v0.30.0 Produksi)",
    id_desc="Spesifikasi pengujian empiris, metodologi verifikasi, dan hasil audit yang memvalidasi seluruh 20 kriteria penerimaan v0.30.0.",
    id_cards=[
        "10.5.1 Kriteria Penerimaan Komponen 1 (Task Leasing)",
        "10.5.2 Kriteria Penerimaan Komponen 2 (Cloud CAS)",
        "10.5.3 Kriteria Penerimaan Komponen 3 (VLM Healing)"
    ],
    id_alerts=[
        {
            "title": "SELURUH 20 KRITERIA PENERIMAAN TERVERIFIKASI & TERSERTIFIKASI",
            "bodyHtml": "Seluruh 20 kriteria di bawah ini (AC1.1 hingga AC3.6) mewakili <strong>kontrak arsitektur inti</strong> untuk v0.30.0. Setiap kriteria didukung oleh tes otomatis di <code>tests/</code> yang lulus 100%."
        },
        {
            "title": "STANDAR VERIFIKASI",
            "bodyHtml": "Tidak ada pull request atau rilis v0.30.0 yang disetujui tanpa cakupan pengujian 100% di seluruh 20 kriteria penerimaan."
        }
    ],
    zh_h1="验收标准验证与实机审计矩阵 (v0.30.0 生产环境)",
    zh_desc="验证 v0.30.0 全部 20 项验收准则 (AC1.1 至 AC3.6) 的经验性测试技术规范、自动化审计结果与执行方法论。",
    zh_cards=[
        "10.5.1 组件 1 验收标准 (任务租约 AC1.1-AC1.7)",
        "10.5.2 组件 2 验收标准 (云 CAS 同步 AC2.1-AC2.7)",
        "10.5.3 组件 3 验收标准 (VLM 视觉自愈 AC3.1-AC3.6)"
    ],
    zh_alerts=[
        {
            "title": "全部 20 项验收准则已 100% 验证与认证",
            "bodyHtml": "以下所有 20 项准则 (AC1.1 至 AC3.6) 构成了 v0.30.0 版本的<strong>核心架构契约</strong>。每一条准则均有 <code>tests/</code> 中的自动化测试支撑，并在本地及 GitHub Actions CI 矩阵中达到 100% 通过率。"
        },
        {
            "title": "工程验收基准",
            "bodyHtml": "在未经实机环境完整执行并证明以下所有 20 项验收标准全部 100% 覆盖通过前，任何 v0.30.0 PR 或发布 Tag 均不得被合并批准。"
        }
    ],
    es_h1="Matriz de Verificación de Criterios de Aceptación (v0.30.0)",
    es_desc="Especificaciones de pruebas empíricas y resultados de auditoría que validan los 20 criterios de aceptación para v0.30.0.",
    es_cards=[
        "10.5.1 Criterios de aceptación del componente 1 (Task Leasing)",
        "10.5.2 Criterios de aceptación del componente 2 (Cloud CAS)",
        "10.5.3 Criterios de aceptación del componente 3 (VLM Healing)"
    ],
    es_alerts=[
        {
            "title": "LOS 20 CRITERIOS DE ACEPTACIÓN VERIFICADOS Y CERTIFICADOS",
            "bodyHtml": "Los 20 criterios siguientes (AC1.1 a AC3.6) representan el <strong>contrato arquitectónico central</strong> para v0.30.0. Cada criterio está respaldado por pruebas automatizadas en <code>tests/</code> que pasan al 100%."
        },
        {
            "title": "ESTÁNDAR DE VERIFICACIÓN",
            "bodyHtml": "No se aprobará ninguna solicitud de extracción o etiqueta de lanzamiento v0.30.0 sin una cobertura de prueba del 100% en los 20 criterios de aceptación siguientes."
        }
    ],
    ja_h1="受入基準検証マトリックス (v0.30.0 本番仕様)",
    ja_desc="v0.30.0 の全20の受入基準を検証する実証的テスト仕様、検証方法、および監査結果。",
    ja_cards=[
        "10.5.1 コンポーネント 1 受入基準 (タスクリース)",
        "10.5.2 コンポーネント 2 受入基準 (クラウド CAS)",
        "10.5.3 コンポーネント 3 受入基準 (VLM 修復)"
    ],
    ja_alerts=[
        {
            "title": "全20の受入基準の検証および認証完了",
            "bodyHtml": "以下の全20基準（AC1.1～AC3.6）は、v0.30.0 における<strong>コアアーキテクチャ契約</strong>を表しています。すべての基準は <code>tests/</code> における自動テストによって裏付けられ、100%合格しています。"
        },
        {
            "title": "検証基準",
            "bodyHtml": "以下の20の受入基準すべてにおいて100%のテストカバレッジが実証されない限り、v0.30.0 のPRまたはリリースタグは承認されません。"
        }
    ],
    ru_h1="Матрица верификации критериев приемки (v0.30.0 Production)",
    ru_desc="Спецификации эмпирических тестов, методологии проверки и результаты аудита для всех 20 критериев приемки v0.30.0.",
    ru_cards=[
        "10.5.1 Критерии приемки компонента 1 (Task Leasing)",
        "10.5.2 Критерии приемки компонента 2 (Cloud CAS)",
        "10.5.3 Критерии приемки компонента 3 (VLM Healing)"
    ],
    ru_alerts=[
        {
            "title": "ВСЕ 20 КРИТЕРИЕВ ПРИЕМКИ ПРОВЕРЕНЫ И СЕРТИФИЦИРОВАНЫ",
            "bodyHtml": "Все 20 критериев ниже (AC1.1–AC3.6) представляют собой <strong>ключевой архитектурный контракт</strong> версии v0.30.0. Каждый критерий подтвержден автоматическими тестами в <code>tests/</code> со 100% прохождением."
        },
        {
            "title": "СТАНДАРТ ВЕРИФИКАЦИИ",
            "bodyHtml": "Ни один pull request или тег релиза v0.30.0 не будет утвержден без 100% покрытия тестами всех 20 критериев приемки."
        }
    ],
    de_h1="Akzeptanzkriterien-Verifikationsmatrix (v0.30.0 Produktion)",
    de_desc="Empirische Testspezifikationen, Verifikationsmethoden und Auditergebnisse zur Validierung aller 20 Akzeptanzkriterien für v0.30.0.",
    de_cards=[
        "10.5.1 Komponente 1 Akzeptanzkriterien (Task Leasing)",
        "10.5.2 Komponente 2 Akzeptanzkriterien (Cloud CAS)",
        "10.5.3 Komponente 3 Akzeptanzkriterien (VLM Healing)"
    ],
    de_alerts=[
        {
            "title": "ALLE 20 AKZEPTANZKRITERIEN VERIFIZIERT & ZERTIFIZIERT",
            "bodyHtml": "Alle 20 nachstehenden Kriterien (AC1.1 bis AC3.6) repräsentieren den <strong>zentralen Architekturvertrag</strong> für v0.30.0. Jedes einzelne Kriterium wird durch automatisierte Tests in <code>tests/</code> gestützt, die lokal und in der GitHub Actions CI-Matrix zu 100% bestehen."
        },
        {
            "title": "VERIFIKATIONSSTANDARD",
            "bodyHtml": "Kein v0.30.0 Pull-Request oder Release-Tag wird genehmigt, ohne dass für alle 20 nachstehenden Akzeptanzkriterien eine Testabdeckung von 100% nachgewiesen wurde."
        }
    ]
)

# ==========================================
# MODULE 03: TUI & INTERACTIVE COCKPITS
# ==========================================
add_sec(
    "sec-cli-tui", "03",
    en_h1="Terminal UI (TUI) & Interactive Cockpits",
    en_desc="Rich curses terminal dashboards, wizard modes, live progress HUDs, and automated release tooling.",
    en_cards=["3.4.1 Master Launcher & Scrape Wizard", "3.4.2 Live Execution HUD & Autonomous Daemons"],
    id_h1="Terminal UI (TUI) & Kokpit Interaktif",
    id_desc="Dashboard terminal curses interaktif, mode wizard, HUD progres langsung, dan perkakas rilis otomatis.",
    id_cards=["3.4.1 Peluncur Utama & Wizard Scrape", "3.4.2 HUD Eksekusi Langsung & Daemon Otonom"],
    zh_h1="终端界面 (TUI) 与交互式控制台",
    zh_desc="富交互 Curses 终端仪表盘、向导模式、实时采集进度 HUD 与自动化发布工具。",
    zh_cards=["3.4.1 主启动器与抓取向导", "3.4.2 实时运行 HUD 与自主监控守护进程"],
    es_h1="Interfaz de Terminal (TUI) y Cabinas Interactivas",
    es_desc="Paneles de terminal curses interactivos, modos de asistente, HUD de progreso en tiempo real y herramientas de lanzamiento.",
    es_cards=["3.4.1 Lanzador Maestro y Asistente de Extracción", "3.4.2 HUD de Ejecución en Vivo y Demonios Autónomos"],
    ja_h1="ターミナル UI (TUI) と対話型コックピット",
    ja_desc="高機能 Curses ターミナルダッシュボード、ウィザードモード、リアルタイム進行 HUD、および自動リリースツール。",
    ja_cards=["3.4.1 マスターランチャー＆スクレイプウィザード", "3.4.2 リアルタイム実行 HUD と自律デーモン"],
    ru_h1="Терминальный интерфейс (TUI) и интерактивные панели",
    ru_desc="Богатые консольные дашборды на базе curses, мастер настройки, HUD реального времени и автоматизация релизов.",
    ru_cards=["3.4.1 Главный лаунчер и мастер скрейпинга", "3.4.2 HUD выполнения в реальном времени и автономные демоны"],
    de_h1="Terminal-UI (TUI) & Interaktive Cockpits",
    de_desc="Umfangreiche Curses-Terminal-Dashboards, Assistenten-Modi, Live-Fortschritts-HUDs und automatisierte Release-Tools.",
    de_cards=["3.4.1 Master-Launcher & Scrape-Assistent", "3.4.2 Live-Ausführungs-HUD & Autonome Daemons"]
)

# ==========================================
# MODULE 06: DATASET STUDIO & CONFIG MATRIX
# ==========================================
add_sec(
    "sec-webui-dataset", "06",
    en_h1="Dataset Studio & ML Export",
    en_desc="In-browser synthetic curation, automated WD14 tagging, aesthetic scoring, and Kohya/LoRA package generation.",
    en_cards=["6.6 Dataset Curation & LoRA Export Studio"],
    id_h1="Studio Dataset & Ekspor ML",
    id_desc="Kurasi visual di browser, penandaan otomatis WD14, penilaian estetika, dan pembuatan paket Kohya/LoRA.",
    id_cards=["6.6 Studio Kurasi Dataset & Ekspor LoRA"],
    zh_h1="数据集工坊与机器学习导出",
    zh_desc="浏览器端合成样本筛选、WD14 自动打标、美学评分过滤与 Kohya/LoRA 训练包一键导出。",
    zh_cards=["6.6 数据集精选与 LoRA 导出工坊"],
    es_h1="Estudio de Datasets y Exportación ML",
    es_desc="Curación en el navegador, etiquetado automático WD14, puntuación estética y generación de paquetes Kohya/LoRA.",
    es_cards=["6.6 Estudio de Curación de Datasets y Exportación LoRA"],
    ja_h1="データセットスタジオ＆MLエクスポート",
    ja_desc="ブラウザ内での合成データ選定、WD14自動タグ付け、審美性スコアリング、およびKohya/LoRAパッケージ生成。",
    ja_cards=["6.6 データセット選定＆LoRAエクスポートスタジオ"],
    ru_h1="Студия датасетов и экспорт для ML"	,
    ru_desc="Курирование в браузере, автотегирование WD14, оценка эстетичности и генерация пакетов Kohya/LoRA.",
    ru_cards=["6.6 Студия курирования датасетов и экспорта LoRA"],
    de_h1="Dataset-Studio & ML-Export",
    de_desc="In-Browser-Kuration, automatisches WD14-Tagging, ästhetische Bewertung und Kohya/LoRA-Paketgenerierung.",
    de_cards=["6.6 Dataset-Kurations- & LoRA-Export-Studio"]
)

add_sec(
    "sec-webui-config-settings", "06",
    en_h1="Configuration Matrix & Tactical Settings",
    en_desc="Dynamic domain policies, URL normalization regex rules, solver timeouts, and notification routing.",
    en_cards=["6.7.1 Domain Configuration Matrix", "6.7.2 Tactical Settings & Webhook Integrations"],
    id_h1="Matriks Konfigurasi & Pengaturan Taktis",
    id_desc="Kebijakan domain dinamis, aturan regex normalisasi URL, batas waktu solver, dan perutean notifikasi.",
    id_cards=["6.7.1 Matriks Konfigurasi Domain", "6.7.2 Pengaturan Taktis & Integrasi Webhook"],
    zh_h1="配置矩阵工作台与战术配置",
    zh_desc="动态域名爬虫策略、URL 归一化正则规则、求解器超时配置与多渠道通知路由。",
    zh_cards=["6.7.1 域名配置规则矩阵", "6.7.2 战术配置与 Webhook 告警集成"],
    es_h1="Matriz de Configuración y Ajustes Tácticos",
    es_desc="Políticas de dominio dinámicas, reglas regex de normalización de URL, tiempos de espera de resolvedores y rutas de notificación.",
    es_cards=["6.7.1 Matriz de Configuración de Dominios", "6.7.2 Ajustes Tácticos e Integraciones Webhook"],
    ja_h1="設定マトリクスと戦術設定",
    ja_desc="動的ドメインポリシー、URL正規化正規表現ルール、ソルバーのタイムアウト、および通知ルーティング。",
    ja_cards=["6.7.1 ドメイン設定マトリクス", "6.7.2 戦術設定とWebhook統合"],
    ru_h1="Матрица конфигураций и тактические настройки",
    ru_desc="Динамические политики доменов, регулярные выражения нормализации URL, таймауты солверов и маршрутизация уведомлений.",
    ru_cards=["6.7.1 Матрица конфигураций доменов", "6.7.2 Тактические настройки и интеграции с вебхуками"],
    de_h1="Konfigurationsmatrix & Taktische Einstellungen",
    de_desc="Dynamische Domain-Richtlinien, URL-Normalisierungs-Regex-Regeln, Solver-Timeouts und Benachrichtigungs-Routing.",
    de_cards=["6.7.1 Domain-Konfigurationsmatrix", "6.7.2 Taktische Einstellungen & Webhook-Integrationen"]
)

print(f"All {len(SECTIONS_DB)} sections added to SECTIONS_DB successfully.")


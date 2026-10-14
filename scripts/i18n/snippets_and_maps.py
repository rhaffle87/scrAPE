# -*- coding: utf-8 -*-
"""
Snippets, Lists, Table Headers, and Subheadings for docs/site/i18n.js
"""

SNIPPETS = {
    "en": {
        "sec-install-steps": """# 1. Clone the repository
git clone https://github.com/rhaffle87/scrAPE.git
cd scrAPE

# 2. Create and activate a virtual environment
python -m venv venv
venv\\Scripts\\activate          # Windows CMD
.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell
source venv/bin/activate       # Linux / macOS

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. (Optional) Install Crawlee Node.js bridge for Tier 6-7 stealth
cd crawlee_bridge && npm install && cd ..

# 5. Configure credentials
copy .env.example .env         # Windows
cp .env.example .env           # Linux / macOS
# Then edit .env with your API keys and webhook URLs""",
        "sec-install-launchers": """# Windows Master Launcher (Interactive Menu)
.\\run.bat

# Linux / macOS Master Launcher
./run.sh

# Direct Interactive Wizard (no menu)
python src/cli/cli_wizard.py""",
        "sec-ops-docker": """# Start scraper engine + FlareSolverr sidecar
docker compose up -d

# Check cluster logs in real time
docker compose logs -f

# Gracefully stop the stack
docker compose down""",
        "sec-ops-watchdog": """# Run Watchdog Agent via launcher wrapper
.\\run.bat watchdog

# Direct continuous monitoring invocation
python src/cli/monitor_agent.py --keyword "example_subject" --seed seeds/example_subject.txt --use-state-cache""",
        "sec-ops-sessions": """# Capture cookies via interactive browser window
python src/cli/session_auth.py --domain example.com --login-url https://example.com/login

# List stored sticky session cookies
python src/cli/session_auth.py --list-sessions""",
        "sec-test-pytest": """# Run all 378+ unit and integration tests
pytest tests/ -v

# Run with coverage report
pytest --cov=src tests/ --cov-report=term-missing""",
        "sec-test-logs": """# Check for HTTP 429 rate limits and Cloudflare blocks
Get-Content logs/crawler.log -Tail 100 | Select-String -Pattern "429|Cloudflare|WAF|BLOCKED"

# Monitor real-time crawl engine flow
Get-Content logs/crawler.log -Wait -Tail 20"""
    },
    "id": {
        "sec-install-steps": """# 1. Klon repositori
git clone https://github.com/rhaffle87/scrAPE.git
cd scrAPE

# 2. Buat dan aktifkan lingkungan virtual
python -m venv venv
venv\\Scripts\\activate          # Windows CMD
.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell
source venv/bin/activate       # Linux / macOS

# 3. Instal dependensi Python
pip install -r requirements.txt

# 4. (Opsional) Instal bridge Node.js Crawlee untuk stealth Tingkat 6-7
cd crawlee_bridge && npm install && cd ..

# 5. Konfigurasi kredensial
copy .env.example .env         # Windows
cp .env.example .env           # Linux / macOS
# Kemudian edit .env dengan API key dan URL webhook Anda""",
        "sec-install-launchers": """# Peluncur Utama Windows (Menu Interaktif)
.\\run.bat

# Peluncur Utama Linux / macOS
./run.sh

# Wizard Interaktif Langsung (tanpa menu)
python src/cli/cli_wizard.py""",
        "sec-ops-docker": """# Jalankan mesin scraper + sidecar FlareSolverr
docker compose up -d

# Pantau log kluster secara real-time
docker compose logs -f

# Hentikan stack kontainer dengan aman
docker compose down""",
        "sec-ops-watchdog": """# Jalankan Agen Pengawas melalui wrapper peluncur
.\\run.bat watchdog

# Eksekusi langsung pemantauan kontinu
python src/cli/monitor_agent.py --keyword "example_subject" --seed seeds/example_subject.txt --use-state-cache""",
        "sec-ops-sessions": """# Tangkap cookie melalui jendela browser interaktif
python src/cli/session_auth.py --domain example.com --login-url https://example.com/login

# Tampilkan daftar cookie sesi sticky tersimpan
python src/cli/session_auth.py --list-sessions""",
        "sec-test-pytest": """# Jalankan seluruh 378+ uji unit dan integrasi
pytest tests/ -v

# Jalankan dengan laporan cakupan (coverage)
pytest --cov=src tests/ --cov-report=term-missing""",
        "sec-test-logs": """# Periksa batas laju HTTP 429 dan pemblokiran Cloudflare
Get-Content logs/crawler.log -Tail 100 | Select-String -Pattern "429|Cloudflare|WAF|BLOCKED"

# Pantau alur mesin perayap secara real-time
Get-Content logs/crawler.log -Wait -Tail 20"""
    },
    "zh": {
        "sec-install-steps": """# 1. 克隆代码仓库
git clone https://github.com/rhaffle87/scrAPE.git
cd scrAPE

# 2. 创建并激活虚拟环境
python -m venv venv
venv\\Scripts\\activate          # Windows CMD
.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell
source venv/bin/activate       # Linux / macOS

# 3. 安装 Python 核心依赖项
pip install -r requirements.txt

# 4. (可选) 安装 Crawlee Node.js 桥接模块以支持 Tier 6-7 深度隐身
cd crawlee_bridge && npm install && cd ..

# 5. 配置生产凭据
copy .env.example .env         # Windows
cp .env.example .env           # Linux / macOS
# 随后在 .env 文件中填入 API 密钥与 Webhook 地址""",
        "sec-install-launchers": """# Windows 一键主启动脚本 (交互式菜单)
.\\run.bat

# Linux / macOS 主启动脚本
./run.sh

# 直接启动交互式向导 (跳过主菜单)
python src/cli/cli_wizard.py""",
        "sec-ops-docker": """# 后台启动爬虫核心引擎与 FlareSolverr 容器
docker compose up -d

# 实时查看集群运行日志
docker compose logs -f

# 优雅停止并清理容器网络
docker compose down""",
        "sec-ops-watchdog": """# 通过主启动脚本运行 Watchdog 守护进程
.\\run.bat watchdog

# 直接命令行执行持续监控
python src/cli/monitor_agent.py --keyword "example_subject" --seed seeds/example_subject.txt --use-state-cache""",
        "sec-ops-sessions": """# 弹出交互式浏览器窗口登录并抓取 Cookie
python src/cli/session_auth.py --domain example.com --login-url https://example.com/login

# 列出本地保存的持久化 Cookie 会话
python src/cli/session_auth.py --list-sessions""",
        "sec-test-pytest": """# 运行全量 378+ 单元与集成自动化测试
pytest tests/ -v

# 附带测试覆盖率报告运行
pytest --cov=src tests/ --cov-report=term-missing""",
        "sec-test-logs": """# 实时检索 HTTP 429 频控与 Cloudflare 拦截日志
Get-Content logs/crawler.log -Tail 100 | Select-String -Pattern "429|Cloudflare|WAF|BLOCKED"

# 实时监控抓取引擎日志输出
Get-Content logs/crawler.log -Wait -Tail 20"""
    },
    "es": {
        "sec-install-steps": """# 1. Clonar el repositorio
git clone https://github.com/rhaffle87/scrAPE.git
cd scrAPE

# 2. Crear y activar el entorno virtual
python -m venv venv
venv\\Scripts\\activate          # Windows CMD
.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell
source venv/bin/activate       # Linux / macOS

# 3. Instalar dependencias de Python
pip install -r requirements.txt

# 4. (Opcional) Instalar el puente Node.js de Crawlee para sigilo Nivel 6-7
cd crawlee_bridge && npm install && cd ..

# 5. Configurar credenciales
copy .env.example .env         # Windows
cp .env.example .env           # Linux / macOS
# Luego edite .env con sus claves de API y URLs de webhooks""",
        "sec-install-launchers": """# Lanzador maestro de Windows (Menú interactivo)
.\\run.bat

# Lanzador maestro de Linux / macOS
./run.sh

# Asistente interactivo directo (sin menú)
python src/cli/cli_wizard.py""",
        "sec-ops-docker": """# Iniciar el motor de raspado + sidecar FlareSolverr
docker compose up -d

# Ver los registros del clúster en tiempo real
docker compose logs -f

# Detener la pila de contenedores de forma segura
docker compose down""",
        "sec-ops-watchdog": """# Ejecutar el agente Watchdog mediante el contenedor de inicio
.\\run.bat watchdog

# Invocación directa de monitoreo continuo
python src/cli/monitor_agent.py --keyword "example_subject" --seed seeds/example_subject.txt --use-state-cache""",
        "sec-ops-sessions": """# Capturar cookies mediante una ventana de navegador interactiva
python src/cli/session_auth.py --domain example.com --login-url https://example.com/login

# Listar cookies de sesión fija almacenadas
python src/cli/session_auth.py --list-sessions""",
        "sec-test-pytest": """# Ejecutar las más de 378 pruebas unitarias y de integración
pytest tests/ -v

# Ejecutar con informe de cobertura
pytest --cov=src tests/ --cov-report=term-missing""",
        "sec-test-logs": """# Verificar límites de tasa HTTP 429 y bloqueos de Cloudflare
Get-Content logs/crawler.log -Tail 100 | Select-String -Pattern "429|Cloudflare|WAF|BLOCKED"

# Monitorear el flujo del motor de rastreo en tiempo real
Get-Content logs/crawler.log -Wait -Tail 20"""
    },
    "ja": {
        "sec-install-steps": """# 1. リポジトリをクローン
git clone https://github.com/rhaffle87/scrAPE.git
cd scrAPE

# 2. 仮想環境を作成して有効化
python -m venv venv
venv\\Scripts\\activate          # Windows CMD
.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell
source venv/bin/activate       # Linux / macOS

# 3. Python 依存関係をインストール
pip install -r requirements.txt

# 4. (任意) Tier 6-7 ステルス用の Crawlee Node.js ブリッジをインストール
cd crawlee_bridge && npm install && cd ..

# 5. 認証情報を設定
copy .env.example .env         # Windows
cp .env.example .env           # Linux / macOS
# 続いて .env を編集して API キーと Webhook URL を設定します""",
        "sec-install-launchers": """# Windows マスターランチャー (対話型メニュー)
.\\run.bat

# Linux / macOS マスターランチャー
./run.sh

# 対話型ウィザードの直接起動 (メニューなし)
python src/cli/cli_wizard.py""",
        "sec-ops-docker": """# スクレイパーエンジンと FlareSolverr サイドカーを起動
docker compose up -d

# クラスタログをリアルタイムで監視
docker compose logs -f

# スタックを正常に停止
docker compose down""",
        "sec-ops-watchdog": """# ランチャー経由で Watchdog エージェントを実行
.\\run.bat watchdog

# 継続的監視ループの直接呼び出し
python src/cli/monitor_agent.py --keyword "example_subject" --seed seeds/example_subject.txt --use-state-cache""",
        "sec-ops-sessions": """# 対話型ブラウザウィンドウでクッキーをキャプチャ
python src/cli/session_auth.py --domain example.com --login-url https://example.com/login

# 保存されたスティッキーセッションクッキーを一覧表示
python src/cli/session_auth.py --list-sessions""",
        "sec-test-pytest": """# 全378以上の単体および統合テストを実行
pytest tests/ -v

# カバレッジレポート付きで実行
pytest --cov=src tests/ --cov-report=term-missing""",
        "sec-test-logs": """# HTTP 429 レート制限と Cloudflare ブロックを確認
Get-Content logs/crawler.log -Tail 100 | Select-String -Pattern "429|Cloudflare|WAF|BLOCKED"

# クロールエンジンのログ出力をリアルタイム監視
Get-Content logs/crawler.log -Wait -Tail 20"""
    },
    "ru": {
        "sec-install-steps": """# 1. Клонировать репозиторий
git clone https://github.com/rhaffle87/scrAPE.git
cd scrAPE

# 2. Создать и активировать виртуальное окружение
python -m venv venv
venv\\Scripts\\activate          # Windows CMD
.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell
source venv/bin/activate       # Linux / macOS

# 3. Установить зависимости Python
pip install -r requirements.txt

# 4. (Опционально) Установить Node.js-мост Crawlee для стелс-уровней 6-7
cd crawlee_bridge && npm install && cd ..

# 5. Настроить учетные данные
copy .env.example .env         # Windows
cp .env.example .env           # Linux / macOS
# Затем отредактируйте .env с вашими ключами API и URL вебхуков""",
        "sec-install-launchers": """# Основной скрипт запуска Windows (Интерактивное меню)
.\\run.bat

# Основной скрипт запуска Linux / macOS
./run.sh

# Прямой запуск интерактивного мастера (без меню)
python src/cli/cli_wizard.py""",
        "sec-ops-docker": """# Запуск ядра скрейпера + контейнер FlareSolverr
docker compose up -d

# Просмотр логов кластера в реальном времени
docker compose logs -f

# Корректная остановка контейнеров
docker compose down""",
        "sec-ops-watchdog": """# Запуск агента Watchdog через оболочку запуска
.\\run.bat watchdog

# Прямой запуск непрерывного мониторинга
python src/cli/monitor_agent.py --keyword "example_subject" --seed seeds/example_subject.txt --use-state-cache""",
        "sec-ops-sessions": """# Захват cookie через интерактивное окно браузера
python src/cli/session_auth.py --domain example.com --login-url https://example.com/login

# Список сохраненных постоянных сессий cookie
python src/cli/session_auth.py --list-sessions""",
        "sec-test-pytest": """# Запуск всех 378+ модульных и интеграционных тестов
pytest tests/ -v

# Запуск с отчетом о покрытии кода
pytest --cov=src tests/ --cov-report=term-missing""",
        "sec-test-logs": """# Поиск лимитов HTTP 429 и блокировок Cloudflare в логах
Get-Content logs/crawler.log -Tail 100 | Select-String -Pattern "429|Cloudflare|WAF|BLOCKED"

# Мониторинг логов скрейпера в реальном времени
Get-Content logs/crawler.log -Wait -Tail 20"""
    },
    "de": {
        "sec-install-steps": """# 1. Repository klonen
git clone https://github.com/rhaffle87/scrAPE.git
cd scrAPE

# 2. Virtuelle Umgebung erstellen und aktivieren
python -m venv venv
venv\\Scripts\\activate          # Windows CMD
.\\venv\\Scripts\\Activate.ps1    # Windows PowerShell
source venv/bin/activate       # Linux / macOS

# 3. Python-Abhängigkeiten installieren
pip install -r requirements.txt

# 4. (Optional) Crawlee Node.js-Bridge für Stealth Stufe 6-7 installieren
cd crawlee_bridge && npm install && cd ..

# 5. Zugangsdaten konfigurieren
copy .env.example .env         # Windows
cp .env.example .env           # Linux / macOS
# Bearbeiten Sie anschließend .env mit Ihren API-Schlüsseln und Webhook-URLs""",
        "sec-install-launchers": """# Windows-Master-Starter (Interaktives Menü)
.\\run.bat

# Linux / macOS Master-Starter
./run.sh

# Direkter interaktiver Assistent (ohne Menü)
python src/cli/cli_wizard.py""",
        "sec-ops-docker": """# Scraper-Engine + FlareSolverr-Sidecar starten
docker compose up -d

# Cluster-Logs in Echtzeit überwachen
docker compose logs -f

# Container-Stack ordnungsgemäß stoppen
docker compose down""",
        "sec-ops-watchdog": """# Watchdog-Agent über Starter-Wrapper ausführen
.\\run.bat watchdog

# Direkter Start der kontinuierlichen Überwachung
python src/cli/monitor_agent.py --keyword "example_subject" --seed seeds/example_subject.txt --use-state-cache""",
        "sec-ops-sessions": """# Cookies über interaktives Browserfenster erfassen
python src/cli/session_auth.py --domain example.com --login-url https://example.com/login

# Gespeicherte Sticky-Session-Cookies auflisten
python src/cli/session_auth.py --list-sessions""",
        "sec-test-pytest": """# Alle 378+ Unit- und Integrationstests ausführen
pytest tests/ -v

# Mit Coverage-Bericht ausführen
pytest --cov=src tests/ --cov-report=term-missing""",
        "sec-test-logs": """# Auf HTTP-429-Ratenbegrenzungen und Cloudflare-Blockaden prüfen
Get-Content logs/crawler.log -Tail 100 | Select-String -Pattern "429|Cloudflare|WAF|BLOCKED"

# Echtzeit-Ausgabe der Crawler-Engine überwachen
Get-Content logs/crawler.log -Wait -Tail 20"""
    }
}

# Lists
LISTS = {
    "en": {
        "sec-install-launchers": [
            "<strong>Broad Search Scraping</strong> -- Automated search queries with recursive crawling.",
            "<strong>Targeted Manifest Scraping</strong> -- Structured crawls against selected seed manifests.",
            "<strong>Continuous Watchdog Agent</strong> -- Long-running monitoring loops with SQLite WAL caching.",
            "<strong>Create Structured AI Dataset</strong> -- Package run output into consolidated, domain-grouped, or media-type-grouped structures.",
            "<strong>Enterprise LLM RAG Ingestion</strong> -- Export page data as consolidated Markdown, chunked page-level <code>.md</code> files, or JSONL embeddings format."
        ]
    },
    "id": {
        "sec-install-launchers": [
            "<strong>Scraping Pencarian Luas</strong> -- Kueri pencarian otomatis dengan crawling rekursif.",
            "<strong>Scraping Manifest Tertarget</strong> -- Crawl terstruktur terhadap manifest seed yang dipilih.",
            "<strong>Agen Pengawas Kontinu (Watchdog)</strong> -- Loop pemantauan jangka panjang dengan cache SQLite WAL.",
            "<strong>Buat Dataset AI Terstruktur</strong> -- Kemas output crawl ke dalam struktur terkonsolidasi, dikelompokkan per domain, atau per jenis media.",
            "<strong>Ingesti RAG LLM Enterprise</strong> -- Ekspor data halaman sebagai Markdown terkonsolidasi, file <code>.md</code> per halaman, atau format embedding JSONL."
        ]
    },
    "zh": {
        "sec-install-launchers": [
            "<strong>全网广泛搜索抓取</strong> —— 基于搜索引擎关键词与递归链接遍历的自主抓取。",
            "<strong>指定种子清单定向抓取</strong> —— 针对所选 seeds/*.txt 种子清单执行高精度结构化抓取。",
            "<strong>持续运行监控守护进程 (Watchdog)</strong> —— 支持 SQLite WAL 缓存的长周期常驻监控。",
            "<strong>构建高质量结构化 AI 训练集</strong> —— 成果物一键规整打包，支持按域名或按媒体格式智能分组归档。",
            "<strong>大模型 RAG 知识库摄取导出</strong> —— 将网页全文清洗导出为规整 Markdown、分块切片 <code>.md</code> 文件或 JSONL 向量嵌入格式。"
        ]
    },
    "es": {
        "sec-install-launchers": [
            "<strong>Raspado de búsqueda amplia</strong> -- Consultas de búsqueda automatizadas con rastreo recursivo.",
            "<strong>Raspado de manifiesto dirigido</strong> -- Rastreo estructurado contra manifiestos seed seleccionados.",
            "<strong>Agente Watchdog continuo</strong> -- Bucles de monitoreo de larga duración con caché SQLite WAL.",
            "<strong>Crear conjunto de datos de IA estructurado</strong> -- Empaquete la salida en estructuras consolidadas o agrupadas por dominio.",
            "<strong>Ingesta RAG para LLM empresarial</strong> -- Exporte páginas como Markdown consolidado, archivos <code>.md</code> divididos o JSONL."
        ]
    },
    "ja": {
        "sec-install-launchers": [
            "<strong>広域検索スクレイピング</strong> -- 再帰的クロールを伴う自動検索クエリ実行。",
            "<strong>ターゲットマニフェストスクレイピング</strong> -- 選択されたシードマニフェストに対する構造化クロール。",
            "<strong>継続的監視エージェント (Watchdog)</strong> -- SQLite WAL キャッシュを備えた長期監視ループ。",
            "<strong>構造化 AI データセット作成</strong> -- 実行結果をドメイン別またはメディアタイプ別に統合・パッケージ化。",
            "<strong>エンタープライズ LLM RAG 投入用エクスポート</strong> -- 統合 Markdown、チャンク分割された <code>.md</code>、または JSONL 形式で出力。"
        ]
    },
    "ru": {
        "sec-install-launchers": [
            "<strong>Широкий поисковый сбор</strong> -- Автоматизированные поисковые запросы с рекурсивным обходом ссылок.",
            "<strong>Целевой сбор по манифесту</strong> -- Структурированный сбор по выбранным файлам начальных ссылок seeds/*.txt.",
            "<strong>Непрерывный агент-наблюдатель (Watchdog)</strong> -- Долговременный цикл мониторинга с кэшированием в SQLite WAL.",
            "<strong>Создание структурированного датасета для ИИ</strong> -- Упаковка выходных данных с группировкой по доменам или типам файлов.",
            "<strong>Импорт в корпоративные RAG-системы для LLM</strong> -- Экспорт страниц в виде единого Markdown, фрагментов <code>.md</code> или эмбеддингов JSONL."
        ]
    },
    "de": {
        "sec-install-launchers": [
            "<strong>Breite Such-Scraping-Abfrage</strong> -- Automatisierte Suchanfragen mit rekursivem Crawling.",
            "<strong>Gezieltes Manifest-Scraping</strong> -- Strukturierte Crawls gegen ausgewählte Seed-Manifeste.",
            "<strong>Kontinuierlicher Watchdog-Agent</strong> -- Langlebige Überwachungsschleifen mit SQLite-WAL-Caching.",
            "<strong>Strukturierten KI-Datensatz erstellen</strong> -- Zusammenfassung der Ausgabe in konsolidierte oder nach Domains gruppierte Strukturen.",
            "<strong>Enterprise-LLM-RAG-Ingestion</strong> -- Export von Seitendaten als konsolidiertes Markdown, fragmentierte <code>.md</code>-Dateien oder JSONL-Embeddings."
        ]
    }
}

# Subheadings inside cards
H3_MAP = {
    "de": {
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
    "id": {
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
    "zh": {
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
    "es": {
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
    "ja": {
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
    "ru": {
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
    }
}

# Table headers map
TH_MAP = {
    "de": {
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
    },
    "id": {
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
    },
    "zh": {
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
    },
    "es": {
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
    },
    "ja": {
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
    },
    "ru": {
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
}

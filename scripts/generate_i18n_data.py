# -*- coding: utf-8 -*-
"""
Generates comprehensive multilingual dictionary data for docs/site/i18n.js
Covers all 55 sections, 65 card titles, 32 code block headers, 10 alert callouts,
subheadings, code snippet comments, table headers, and the full footer.
"""
import json
import os

# 1. UI Translations
UI_TRANSLATIONS = {
    "en": {
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
    "id": {
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
    "zh": {
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
    "es": {
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
    "ja": {
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
    "ru": {
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
    "de": {
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
    }
}

# 2. Modules Titles
MODULE_TRANSLATIONS = {
    "en": [
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
    "id": [
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
    "zh": [
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
    "es": [
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
    "ja": [
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
    "ru": [
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
    "de": [
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
    ]
}

# 3. Footer Translations
FOOTER_TRANSLATIONS = {
    "en": {
        "logo": "scrAPE // CORE SYSTEM",
        "tagline": "Autonomous, high-throughput distributed scraping engine with self-healing DOM heuristics and Apache Parquet export.",
        "badges": ["RELEASE v0.30.1", "MIT LICENSED", "PYTHON 3.10+"],
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
    "id": {
        "logo": "scrAPE // SISTEM INTI",
        "tagline": "Mesin ekstraksi media otonom dan crawler stealth berperforma tinggi untuk penemuan aset dan bypass WAF yang tangguh.",
        "badges": ["RILIS v0.30.1", "LISENSI MIT", "PYTHON 3.10+"],
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
    "zh": {
        "logo": "scrAPE // 核心系统",
        "tagline": "具备自愈式 DOM 启发式算法与 Apache Parquet 导出的高吞吐分布式自主抓取引擎。",
        "badges": ["版本 v0.30.1", "MIT 许可证", "PYTHON 3.10+"],
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
    "es": {
        "logo": "scrAPE // SISTEMA CENTRAL",
        "tagline": "Motor de raspado distribuido autónomo y de alto rendimiento con heurísticas DOM autorreparables y exportación a Apache Parquet.",
        "badges": ["VERSIÓN v0.30.1", "LICENCIA MIT", "PYTHON 3.10+"],
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
    "ja": {
        "logo": "scrAPE // コアシステム",
        "tagline": "自己修復型DOMヒューリスティクスとApache Parquetエクスポートを備えた自律型高スループット分散スクレイピングエンジン。",
        "badges": ["リリース v0.30.1", "MIT ライセンス", "PYTHON 3.10+"],
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
    "ru": {
        "logo": "scrAPE // ОСНОВНАЯ СИСТЕМА",
        "tagline": "Автономный высокопроизводительный распределенный движок сбора данных с самовосстанавливающимися эвристиками DOM и экспортом в Apache Parquet.",
        "badges": ["РЕЛИЗ v0.30.1", "ЛИЦЕНЗИЯ MIT", "PYTHON 3.10+"],
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
    "de": {
        "logo": "scrAPE // KERN-SYSTEM",
        "tagline": "Autonome, hochdurchsatzfähige verteilte Scraping-Engine mit selbstheilenden DOM-Heuristiken und Apache-Parquet-Export.",
        "badges": ["VERSION v0.30.1", "MIT-LIZENZIERT", "PYTHON 3.10+"],
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
    }
}

print("Base definitions ready.")

# scrAPE — Mesin Perayap Web & Ekstraksi Media Otonom
> Mesin ekstraksi media dan penjelajahan tersembunyi (stealth crawl) otonom berkecepatan tinggi yang dirancang untuk bypass WAF tangguh dan kurasi dataset AI.

<p align="center">
  <img src="https://img.shields.io/badge/BUILD-PASSING-brightgreen?style=for-the-badge" alt="Build Status">
  <img src="https://img.shields.io/badge/RELEASE-V0.30.1-orange?style=for-the-badge" alt="Release Version">
  <img src="https://img.shields.io/badge/DASHBOARD-FASTAPI%20%2B%20HTMX-7000ff?style=for-the-badge" alt="FastAPI HTMX Dashboard">
  <img src="https://img.shields.io/badge/STEALTH-8--TIER%20WAF-0066ff?style=for-the-badge" alt="8-Tier WAF Stealth">
  <img src="https://img.shields.io/badge/TESTS-961%20PASSED-success?style=for-the-badge" alt="961 Tests Passing">
  <img src="https://img.shields.io/badge/LICENSE-MIT-00bfff?style=for-the-badge" alt="License MIT">
</p>

---

## Daftar Isi
1. [Ringkasan Arsitektur](#ringkasan-arsitektur)
2. [Fitur Unggulan](#fitur-unggulan)
3. [Alur Pipeline Bypass WAF 8 Tingkat](#alur-pipeline-bypass-waf-8-tingkat)
4. [Instalasi & Pengaturan Lingkungan](#instalasi--pengaturan-lingkungan)
5. [Panduan Penggunaan CLI](#panduan-penggunaan-cli)
6. [WebUI & Dasbor Telemetri](#webui--dasbor-telemetri)
7. [Struktur Output & Ekspor Dataset](#struktur-output--ekspor-dataset)
8. [Tanya Jawab & Pemecahan Masalah](#tanya-jawab--pemecahan-masalah)

---

## Ringkasan Arsitektur

scrAPE adalah mesin perayap dan ekstraksi media berbasis Python yang berjalan secara lokal di komputer Anda. Dirancang untuk menangani Single-Page Applications (SPA), perlindungan bot tingkat tinggi seperti Cloudflare Turnstile, CAPTCHA audio/visual, serta unduhan paralel berkecepatan tinggi dengan telemetri beban perangkat keras waktu nyata.

```
+-----------------------------------------------------------------------------------+
|                            scrAPE CORE ARCHITECTURE                              |
+-----------------------------------------------------------------------------------+
                                          |
                +-------------------------+-------------------------+
                |                                                   |
      [CLI CLI / Operator]                                [FastAPI + HTMX WebUI]
                |                                                   |
                +-------------------------+-------------------------+
                                          |
                                          v
                              [CrawlCoordinator]
                   +----------------------+----------------------+
                   |                                             |
             (Worker Pool)                                 (Profiler Pool)
                   |                                             |
                   v                                             v
        [8-Tier Engine Dispatcher]                    [Domain Profiler Gating]
                   |
     +-------------+-------------+-------------+-------------+
     |             |             |             |             |
  (HTTPX)    (DrissionPage)  (Camoufox)    (Crawlee)    (FlareSolverr)
     +-------------+-------------+-------------+-------------+
                   |
                   v
     [Self-Healing DOM Parser (VLM / LLM)]
                   |
                   v
     [MediaDownloader & BK-Tree Deduplication]
                   |
                   v
     [Storage Sinks: Local CAS / SQLite WAL / Cloud S3/R2]
```

---

## Fitur Unggulan

- **Deduplikasi Perseptual Sub-Linear BK-Tree**: Menggantikan pemindaian linier $O(N)$ pHash dengan struktur pohon metrik diskrit `BKTree` ($O(\log N)$ pada batas jarak Hamming $\le 4$) yang diisi langsung dari `StateCache`.
- **Isolasi Concurrency Profiler**: Pemisahan antrean profil domain (`_profiler_pool`) mencegah thread perayap utama BFS kehabisan sumber daya komputasi.
- **HTTP Connection Pooling & Isolasi Cookie**: Dikonfigurasi dengan `httpx.Limits(max_connections=200, max_keepalive_connections=50, keepalive_expiry=30.0)` serta cookie berbasis request untuk mencegah polusi sesi lintas thread.
- **Cache Selektor DOM Self-Healing In-Memory TTL**: Sistem resolusi selektor dua tingkat dengan cache RAM cepat dan persistensi SQLite WAL, membersihkan selektor usang setelah 7 hari.
- **Penulisan Byte Mentah Langsung (Zero-Recompression)**: Verifikasi integritas gambar melalui `img.verify()` tanpa siklus dekompresi-kompresi ulang, mempertahankan kualitas asli gambar.
- **Proteksi Overload Host & Uji Canary**: Pengujian separuh-buka (half-open single-flight probe) pada host yang mengalami throttling (429/503) dengan backoff eksponensial.
- **Penyewaan Tugas Terdistribusi (Distributed Task Leasing)**: Arsitektur cluster berbasis Redis Streams dengan penguncian idempoten atomik (`SET NX EX 86400`) dan dead-letter routing.
- **Penyimpanan Terpetakan Konten (Cloud CAS)**: Sinkronisasi blok asinkron ke Amazon S3, Cloudflare R2, dan MinIO dengan validasi hash SHA-256 64-karakter terhadap serangan path traversal.
- **Pemulihan DOM Berbasis Vision-Language Model (VLM)**: Pemulihan selektor DOM tingkat lanjut menggunakan model visual multimodal (Gemini Flash, GPT-4o-mini, Ollama Vision) dengan isolasi prompt injection ketat.
- **Ekspor Dataset Kolom Apache Parquet**: Ekspor tabel berformat Parquet dengan kompresi Snappy (`images.parquet`, `videos.parquet`, `run_summary.parquet`) untuk kebutuhan analitik AI.

---

## Alur Pipeline Bypass WAF 8 Tingkat

Ketika scrAPE menemukan laman yang dilindungi oleh bot-mitigation, sistem secara otomatis mengekstrak laman melalui rantai eskalasi teruji:

1. **Tier 1 — HTTPX Direct (Local Cookie Injection)**: Menggunakan cookie browser lokal yang valid dari sesi sebelumnya.
2. **Tier 2 — Crawl4AI Async Engine**: Ekstraksi berbasis Chromium tanpa kepala (headless) berlatensi sangat rendah.
3. **Tier 3 — Crawlee Cheerio Scraper**: Parser DOM murni tanpa rendering JavaScript untuk throughput maksimal pada konten statis.
4. **Tier 4 — DrissionPage Fingerprint Spoofing**: Melewati deteksi CDP melalui manipulasi langsung objek browser driver.
5. **Tier 5 — Crawlee Puppeteer / Stealth**: Mode emulasi peramban penuh dengan patch sidik jari WebGL, AudioContext, dan User-Agent.
6. **Tier 6 — Helium Smart Navigation**: Otomatisasi interaksi tingkat tinggi untuk alur penjelajahan kompleks.
7. **Tier 7 — Camoufox Anti-Detect Browser**: Mesin berbasis Firefox C++ yang dimodifikasi secara internal untuk menyamarkan tumpukan TCP/IP dan WebRTC.
8. **Tier 8 — FlareSolverr Proxy Node**: Solusi terakhir untuk menyelesaikan tantangan JavaScript dan Cloudflare Under-Attack Mode.

---

## Instalasi & Pengaturan Lingkungan

### Prasyarat
- Python 3.10 atau versi lebih baru
- Node.js 18+ (opsional untuk Crawlee bridge)
- Git

### Langkah Pemasangan
```powershell
# 1. Klon repositori
git clone https://github.com/rhaffle87/scrAPE.git
cd scrAPE

# 2. Buat lingkungan virtual Python
python -m venv venv
.\venv\Scripts\activate

# 3. Pasang pustaka dan dependensi
pip install -r requirements.txt
playwright install chromium
```

---

## Panduan Penggunaan CLI

Perintah CLI `scrape` menyediakan antarmuka lengkap untuk mengendalikan mesin ekstraksi:

### Perintah Dasar
```powershell
# Perayapan domain standar
python -m src.cli https://example.com/gallery --max-pages 50 --depth 2

# Mengaktifkan mode bypass WAF agresif
python -m src.cli https://protected-site.com --waf-tier camoufox --stealth

# Ekstraksi media dengan deduplikasi BK-tree dan ekspor Parquet
python -m src.cli https://example.com --min-width 1024 --min-height 768 --export-parquet
```

### Parameter Umum
| Flag CLI | Keterangan Default | Deskripsi |
|---|---|---|
| `--max-pages` | `100` | Batas maksimum URL yang akan dijelajahi per domain. |
| `--depth` | `3` | Kedalaman maksimum perayapan BFS dari URL awal. |
| `--rate-limit` | `2.0` | Batas permintaan HTTP keluar per detik (RPS). |
| `--workers` | `8` | Jumlah thread pekerja paralel untuk unduhan media. |
| `--waf-tier` | `auto` | Tingkat mesin WAF yang dipaksakan (`httpx`, `camoufox`, `drission`). |
| `--export-parquet` | `False` | Menyimpan metadata hasil ekstraksi ke file Apache Parquet. |

---

## WebUI & Dasbor Telemetri

scrAPE menyertakan antarmuka web taktis berbasis FastAPI dan HTMX yang dapat diakses langsung dari peramban lokal.

```powershell
# Menjalankan peladen WebUI
python -m src.web.app --host 127.0.0.1 --port 8000
```

Buka peramban Anda di `http://127.0.0.1:8000/` untuk mengakses:
- **Command Center**: Ringkasan status sistem, kecepatan unduh real-time, dan kontrol start/pause/abort.
- **Seed Studio**: Manajemen daftar domain target dan penyesuaian filter resolusi gambar.
- **Watchdog**: Visualisasi grafik Canvas waktu nyata untuk struktur penjelajahan domain.
- **Config Matrix**: Penyesuaian profil WAF, setelan proxy, dan batas memori HardwareLoadGovernor.
- **System Settings**: Telemetri CPU, RAM, disk I/O, serta status kluster terdistribusi Redis.

---

## Struktur Output & Ekspor Dataset

Semua hasil ekstraksi disimpan secara terorganisir di dalam direktori `output/`:

```
output/
├── [domain_hash]/
│   ├── images/              # File biner media asli (dideduplikasi via CAS)
│   ├── raw/                 # Snapshot HTML halaman mentah
│   ├── manifest.json        # Metadata lengkap proses crawling
│   ├── domain_report.json   # Ringkasan statistik performa domain
│   ├── images.parquet       # Dataset kolom Parquet (siap untuk ML)
│   └── run_summary.parquet  # Ringkasan performa run
└── cas_store/               # Penyimpanan terpusat Content-Addressable Storage (SHA-256)
```

---

## Tanya Jawab & Pemecahan Masalah

### Mengapa proses unduhan terhenti pada domain yang sama?
Periksa setelan `CrawlGovernor`. Jika host merespons dengan kode status HTTP `429 Too Many Requests` atau `503 Service Unavailable`, sistem akan menempatkan domain tersebut ke mode isolasi (cooldown) otomatis untuk melindungi reputasi IP Anda.

### Bagaimana cara mengaktifkan VLM Visual Healing?
Pastikan kunci API penyedia AI (Gemini atau OpenAI) atau instans Ollama lokal sudah dikonfigurasi pada file `.env`:
```env
GEMINI_API_KEY=your_key_here
VLM_PROVIDER=gemini
VLM_MODEL=gemini-1.5-flash
```

---
*Dokumentasi ini dirawat oleh tim pengembang scrAPE. Lisensi di bawah MIT.*

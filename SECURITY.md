# Security & Stealth Policy — scrAPE
> Security guidelines, container isolation policies, and zero-tolerance static analysis compliance rules.


**scrAPE** is engineered with strict local data privacy, container network isolation, robust anti-bot stealth standards, and enterprise-grade static analysis compliance.

## 1. Local Browser Cookie Harvesting Privacy

- **Tier 0 Local Harvest (`browser-cookie3`)**: Read-only extraction of domain-specific session cookies from local browser profiles (Chrome, Firefox, Edge, Brave, Opera).
- **In-Memory Usage Only**: Harvested cookies are decrypted in memory (`HttpClient._harvest_local_cookies()`) and sent directly to target web servers. Session cookies are never written to disk, committed to source repositories, or transmitted to third-party services.

## 2. Docker Container Network Isolation

- **FlareSolverr Service Binding**: Default `FLARESOLVERR_URL` is bound strictly to `http://127.0.0.1:8191/v1`.
- **Loopback Enforcement**: Container port mapping is configured as `127.0.0.1:8191:8191` to prevent external network exposure of the FlareSolverr endpoint.
- **Auto-Start Safety**: Background Docker container launches (`docker start flaresolverr`) execute isolated subprocess calls without shell evaluation.

## 3. Anti-Bot Stealth & Fingerprint Spoofing

- **TLS/JA3 Spoofing**: Uses `curl_cffi` and Node.js `got-scraping` to spoof modern Chrome/Firefox TLS client handshakes and JA3 fingerprints.
- **Headless Evasion**: Integrates `puppeteer-extra-plugin-stealth` and `Camoufox` (C++ stealth Firefox engine) to mask WebDriver presence (`navigator.webdriver == false`), Canvas fingerprints, and WebGL renderer strings.

## 4. Static Analysis Compliance & Path Injection Mitigations

We enforce strict security rules that govern how code interacts with the filesystem, running OSV-Scanner, Semgrep, and enterprise CodeQL static analysis.

- **Zero-Tolerance for Superficial Suppressions**: We strictly prohibit the use of `# codeql[py/path-injection]` or similar suppression comments to bypass static analysis warnings.
- **Structural Path Validation**: When resolving paths (e.g., processing URLs, generating filenames), scrAPE mathematically proves path bounds via:
  1.  **Untainted Root Generation**: Dynamically rebuilding the base drive/root prefix from the OS (`os.path.splitdrive`).
  2.  **Absolute Normalization**: Forcing inputs through `os.path.abspath(os.path.normpath(user_input))`.
  3.  **Prefix Boundary Enforcement**: Checking that the normalized path strictly begins with the safe root using `.startswith(safe_root)`.

## 5. Network Security, SSRF & Credentials Safety

- **SSRF & DNS Rebinding Defense**: Every target URL and redirect chain hop is strictly validated against `is_safe_target_url()`. Private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`), multicast, and cloud metadata services (`169.254.169.254`) are immediately rejected.
- **Redirect Hop Inspection**: HTTPX event hooks inspect every intermediate response in redirect sequences (`response.history`) to prevent open redirect SSRF pivot attacks.
- **Credential Scrubbing**: Plaintext passwords in connection strings (such as Redis broker URLs or HTTP basic auth) are automatically sanitized to `***` before logging.
- **No Secrets in Source**: No API keys, proxies with hardcoded passwords, or private access tokens are stored in the codebase.
- **Git Ignore Safeguards**: `.gitignore` strictly excludes `.cache/`, `output/`, `.env`, SQLite WAL files (`*.db-wal`, `*.db-shm`), and downloaded media datasets.

## 6. Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.29.x  | :white_check_mark: |
| 0.28.x  | :x:                |
| < 0.28  | :x:                |

## 7. Reporting Vulnerabilities

If you discover a security vulnerability or bug within scrAPE, please submit an issue or contact the maintainers directly.

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

## 5. Secret & Credentials Safety

- **No Secrets in Source**: No API keys, proxies with hardcoded passwords, or private access tokens are stored in the codebase.
- **Git Ignore Safeguards**: `.gitignore` strictly excludes `.cache/`, `output/`, `.env`, SQLite WAL files, and downloaded media datasets.

## 6. Reporting Vulnerabilities

If you discover a security vulnerability or bug within scrAPE, please submit an issue or contact the maintainers directly.

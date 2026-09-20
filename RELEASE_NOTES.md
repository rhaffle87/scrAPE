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

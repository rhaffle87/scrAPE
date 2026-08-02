# Security Policy — scrAPE

> Comprehensive overview of vulnerability mitigations, dependency management, and static analysis compliance used in the scrAPE engine.

---

## 1. Vulnerability Management & Dependencies

scrAPE relies on automated security scanners (e.g., OSV-Scanner) to track known vulnerabilities in upstream dependencies.
To maintain a hardened footprint, we adhere to the following principles:

- **Regular Dependency Bumps**: Critical dependencies like `yt-dlp`, `Pillow`, `python-multipart`, and `lxml` are actively monitored and bumped to their latest stable versions to mitigate publicly disclosed CVEs.
- **Minimal External Surface**: The engine limits external library usage where possible. Tools like `Pillow` are utilized explicitly for their sanitization capabilities (e.g., stripping EXIF data and ensuring image validity) to prevent malicious polyglot file ingestion.

---

## 2. Static Analysis Compliance (CodeQL & Semgrep)

The codebase natively complies with enterprise-grade static analysis tools without relying on superficial suppression comments (`# codeql`, `// nosemgrep`). We implement mathematical and structural validations to guarantee safe execution.

### Path Injection Prevention
A core focus is mitigating arbitrary path injections when writing files to disk (e.g., in `src/ml/dataset_tagger.py` and `src/ml/dataset_exporter.py`).

- **Untainted OS Roots**: Paths are always verified against untainted, OS-derived roots (using `os.path.splitdrive` on Windows or `os.sep` on POSIX).
- **Absolute Normalization**: User inputs and dynamically generated paths are forced through `os.path.abspath(os.path.normpath(...))` to neutralize directory traversal payloads (`../`).
- **Boundary Verification**: The final path is strictly verified against the untainted base prefix using `.startswith()`. This structural validation satisfies CodeQL and Semgrep rules out-of-the-box, ensuring zero false-positives and eliminating the need for manual rule suppressions.

---

## 3. Docker Security & Dependency Isolation

When running in containerized environments, the Node.js / Puppeteer bridge (`crawlee_bridge`) requires strict dependency isolation:

- **Playwright Chromium**: The Docker base image provides a managed, secure, and centrally patched Chromium binary via Playwright.
- **Preventing Rogue Downloads**: To prevent Puppeteer from fetching an unmanaged version of Chromium during `npm install`, the environment variable `PUPPETEER_SKIP_DOWNLOAD=true` is explicitly enforced. This guarantees that all headless browser operations execute against the validated, secure Playwright binary.

---

## 4. Reporting Vulnerabilities

If you discover a security vulnerability within scrAPE, please do not disclose it publicly. Submit an issue on the repository detailing the vulnerability, and the maintainers will prioritize a patch in the upcoming release.

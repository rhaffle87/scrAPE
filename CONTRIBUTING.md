# Contributing Guidelines — scrAPE
> Development setup, coding standards, testing requirements, and pull request workflows for scrAPE.

Thank you for contributing to **scrAPE**! 

## Quick Start (Development Setup)

1. **Clone the repository and create a feature branch**:
   ```bash
   git clone https://github.com/your-username/scraper.git
   cd scraper
   git checkout -b feature/your-feature-name
   ```

2. **Create and activate a virtual environment**:
   - **Windows**:
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install global editable CLI (optional)**:
   ```bash
   pip install -e .
   ```

5. **Run the test suite**:
   ```bash
   pytest
   ```

## Code Style & Architecture Standards

### Python Guidelines
- **Python Compatibility**: Maintain strict compatibility with Python 3.10+. Avoid deprecated APIs (e.g., use `subprocess.run(..., shell=True)` instead of `os.system`).
- **Type Annotations**: Use modern Python type hints (`str | None`, `list[dict]`, `Any`).
- **Docstrings & Comments**: Maintain existing docstrings and write clear explanations for non-obvious business logic. Avoid redundant "what" comments on self-explanatory lines.
- **Error Logging**: Inspect full log tracebacks before diagnosing runtime errors. Never swallow exceptions or patch symptoms by deleting failing assertions.

### Core Engine & File Path Rules

> [!CAUTION]
> **No Hardcoded URLs**: Never hardcode domain-specific URL normalisation regex rules in Python source files. Add all domain regex canonicalisation rules to `data/url_normalisation_rules.json`.

- **Decoupled Architecture**: Keep CLI logic (`src/cli/`), Core Engine (`src/core/`), Extractor Plugins (`src/plugins/`), and WebUI (`frontend/`) cleanly isolated.
- **`None`-Safety**: Use `filters.safe_join()` when concatenating string fields that may contain `None`.

## Security & Static Analysis Standards

We enforce strict security rules that govern how code interacts with the filesystem. Our CI/CD pipeline runs enterprise CodeQL static analysis, and we have a **zero-tolerance policy** for manual suppression of security warnings.

> [!IMPORTANT]
> **Strict Ban on `# codeql` Suppressions**
> Do **NOT** use `# codeql[py/path-injection]` or similar suppression comments to bypass static analysis warnings. If CodeQL flags a vulnerability, it must be resolved via structural mitigation.

### Path-Injection Mitigations
When resolving paths or accessing the filesystem based on user-provided input, you must mathematically prove to the analyzer that the resulting path cannot traverse outside a safe root directory.

Follow this standard pattern:
1. **Untainted Root Generation**: Dynamically rebuild the base drive or root prefix directly from the OS.
2. **Absolute Normalization**: Force the input path through `os.path.abspath(os.path.normpath(user_input))`.
3. **Prefix Boundary Enforcement**: Check that the normalized path strictly begins with the safe root using `.startswith(safe_root)`.

**Example (Compliant Code):**
```python
import os
from pathlib import Path

def process_file(user_provided_path: str):
    # 1. Generate an untainted OS-derived root
    abs_path = os.path.abspath(user_provided_path)
    safe_root = os.path.splitdrive(abs_path)[0] + os.sep  # 'C:\' on Windows, '/' on POSIX

    # 2. Normalize to absolute path
    safe_dir = Path(os.path.normpath(abs_path)).resolve()

    # 3. Enforce boundary before ANY filesystem sink
    if not str(safe_dir).startswith(safe_root):
        raise SecurityError("Path traversal blocked")
    
    # Filesystem operations are now safe
    if safe_dir.exists():
        pass
```

## Background Daemons & Thread Lifecycle

Any background threads or daemons (like WAF fallback orchestrators) must handle graceful shutdowns cleanly.
- Use `self._running` flags checked inside an interruptible loop (e.g., `event.wait(1)` or `time.sleep(1)`) rather than large blocking sleeps.
- Silently trap `ValueError` (`I/O operation on closed file`) when the Python interpreter tears down the `sys.stdout` or `sys.stderr` streams, especially during `pytest` teardown. Do not clutter CI logs with zombie thread stack traces.

## Testing Requirements

All bug fixes, scraper enhancements, and new feature additions must include unit or integration test scripts under `tests/`.

### Running Tests
```bash
# Run complete test suite
pytest tests/ -v

# Run specific test file
pytest tests/test_enhanced_features.py -v
```

### Key Test Categories
- `tests/test_enhanced_features.py` — Dynamic layout parsing, JSON API discovery, Crawl4AI fallback verification.
- `tests/test_stealth_cookie_sync.py` — In-memory WAF cookie propagation, SessionPool sync.
- `tests/test_stealth_circuit_breaker.py` — 429 rate limit circuit breaker logic.
- `tests/test_download_retries.py` — Multi-threaded downloader stream Range request resumptions.
- `tests/test_env_and_docs.py` — Credential loading, `.gitignore` safeguards.

## Documentation Updates

Whenever you make changes to core functionality, CLI flags, seed annotations, or WebUI behavior, you **must update the relevant documentation files**:

| Feature Area | Documentation File to Update |
|---|---|
| CLI options or overall features | `README.md` & `docs/USAGE.md` |
| Internal architecture or module flow | `docs/ARCHITECTURE.md` |
| Seed annotations or JSON registries | `docs/CONFIGURATION.md` |
| Filter rules or low-res algorithms | `docs/QUALITY_FILTERS.md` |
| Web UI styling or component guidelines | `DESIGN.md` |
| Release changes and version history | `docs/CHANGELOG.md` |

## Pull Request Checklist

Before submitting your pull request:

- [ ] All unit and integration tests pass cleanly (`pytest tests/ -v`).
- [ ] Code is formatted cleanly and adheres to Python 3.10+ conventions.
- [ ] No hardcoded domain rules in Python source files (used `data/url_normalisation_rules.json`).
- [ ] Updated relevant documentation files (`README.md`, `docs/`, `CHANGELOG.md`).
- [ ] Clear PR title and description outlining the problem and proposed solution.
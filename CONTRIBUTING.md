# Contributing Guidelines — scrAPE

Thank you for contributing to **scrAPE**! This guide outlines development setup, coding standards, testing requirements, and pull request workflows.

---

## 1. Getting Started

### Prerequisites
- Python 3.10+ (Python 3.12/3.13 supported)
- Node.js 18+ and `npm` (for `crawlee_bridge`)
- Git

### Development Environment Setup

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

---

## 2. Code Style & Architecture Standards

### Python Guidelines
- **Python Compatibility**: Maintain strict compatibility with Python 3.10+. Avoid deprecated APIs (e.g. use `subprocess.run(..., shell=True)` instead of `os.system`).
- **Type Annotations**: Use modern Python type hints (`str | None`, `list[dict]`, `Any`).
- **Docstrings & Comments**: Maintain existing docstrings and write clear explanations for non-obvious business logic. Avoid redundant "what" comments on self-explanatory lines.
- **Error Logging**: Inspect full log tracebacks before diagnosing runtime errors. Never swallow exceptions or patch symptoms by deleting failing assertions.

### Core Engine & File Path Rules
- **No Hardcoded URLs**: Never hardcode domain-specific URL normalisation regex rules in Python source files. Add all domain regex canonicalisation rules to `data/url_normalisation_rules.json`.
- **Decoupled Architecture**: Keep CLI logic (`src/cli/`), Core Engine (`src/core/`), Extractor Plugins (`src/plugins/`), and WebUI (`frontend/`) cleanly isolated.
- **`None`-Safety**: Use `filters.safe_join()` when concatenating string fields that may contain `None`.

---

## 3. Testing Requirements

All bug fixes, scraper enhancements, and new feature additions must include unit or integration tests under `tests/`.

### Running Tests
```bash
# Run complete test suite
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_filters.py
```

### Key Test Categories
- `tests/test_filters.py` — Relevance scoring, low-res path patterns, and rejection rules.
- `tests/test_downloader.py` — Multi-threaded downloader, Range request resumptions, and Pillow sanitization.
- `tests/test_cli.py` & `tests/test_seed_validation.py` — Seed manifest parsing and annotation validation.
- `tests/test_frontend_ux.py` — Playwright E2E WebUI tests, telemetry polling, and view routing.

---

## 4. Documentation Updates

Whenever you make changes to core functionality, CLI flags, seed annotations, or WebUI behavior, you **must update the relevant documentation files**:

| Feature Area | Documentation File to Update |
|---|---|
| CLI options or overall features | `README.md` & `docs/USAGE.md` |
| Internal architecture or module flow | `docs/ARCHITECTURE.md` |
| Seed annotations or JSON registries | `docs/CONFIGURATION.md` |
| Filter rules or low-res algorithms | `docs/QUALITY_FILTERS.md` |
| Web UI styling or component guidelines | `DESIGN.md` |
| Release changes and version history | `docs/CHANGELOG.md` |

---

## 5. Pull Request Checklist

Before submitting your pull request:

- [ ] All 103+ unit and integration tests pass cleanly (`pytest`).
- [ ] Code is formatted cleanly and adheres to Python 3.10+ conventions.
- [ ] No hardcoded domain rules in Python source files (used `data/url_normalisation_rules.json`).
- [ ] Updated relevant documentation files (`README.md`, `docs/`, `CHANGELOG.md`).
- [ ] Clear PR title and description outlining the problem and proposed solution.

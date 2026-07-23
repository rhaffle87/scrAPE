# scrAPE — AI Agent Instructions & Guidelines

This document provides project-scoped instructions and architectural rules for AI coding assistants working in the **scrAPE** workspace.

---

## 1. Codebase Architecture & Tech Stack

- **Core Engine**: Python 3.10+ (`src/core/`), FastAPI (`frontend/app.py`), HTMX, SQLite (WAL mode).
- **Stealth & Extraction**: 7-tier WAF fallback pipeline (`src/utils/http_client.py`), Crawlee Express Bridge (`crawlee_bridge/`), `yt-dlp` plugins (`src/plugins/`).
- **WebUI Design System**: Utilitarian Brutalism — strict 90° square corners (`border-radius: 0 !important`), `Oswald` headers, `JetBrains Mono` body/forms, high-contrast dark theme (`#0b0d0c` / `#ff5500` accent).

---

## 2. Mandatory Coding Guidelines

1. **Empirical Log Diagnostics**:
   - NEVER form a diagnostic hypothesis for a runtime failure or test breakage without reading the un-truncated error log.
   - Trace errors back to authoritative code before modifying files.

2. **No Hardcoded Domain Rules in Source**:
   - NEVER hardcode domain-specific URL normalisation regex rules in Python source files.
   - All URL canonicalisation rules MUST be placed in `data/url_normalisation_rules.json`.

3. **`None`-Safety in Filters & Utilities**:
   - Always use `filters.safe_join(items)` when concatenating string tokens to prevent `TypeError` when processing items with `None` fields (e.g. missing alt text or page titles).

4. **Preserve API Contracts & Backward Compatibility**:
   - Do not alter function signatures or return types without updating all invocation sites across `src/`, `frontend/`, and `tests/`.

5. **No Superficial Symptom Patches**:
   - Never resolve errors by masking symptoms, swallowing exceptions, returning dummy fallbacks, or deleting failing unit tests.

---

## 3. WebUI & Aesthetic Rules

1. **Strict Brutalist Geometry**:
   - All UI elements MUST have zero border radius (`border-radius: 0 !important`).
2. **Typography**:
   - Headers (`<h1>`, `<h2>`, `.logo-text`, `.stat-card .value`): `Oswald` font.
   - Code, Forms, Labels, Logs, Buttons: `JetBrains Mono` font.
3. **Color Tokens**:
   - Use CSS variables (`var(--accent)`, `var(--bg-base)`, `var(--bg-surface)`, `var(--text-primary)`, `var(--text-muted)`).
4. **Context-Aware Telemetry**:
   - Stat cards display global totals on Command Center view and subject-scoped totals on Media Vault view.

---

## 4. Verification Requirements

- Always run `pytest` after completing code edits to verify that all 103+ unit and integration tests pass cleanly before declaring completion.
- When modifying WebUI templates, verify HTML rendering and HTMX routes.

---

## 5. Documentation Maintenance

- Keep documentation synchronized across `README.md`, `docs/`, `DESIGN.md`, `CONTRIBUTING.md`, and `docs/CHANGELOG.md`.

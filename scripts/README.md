# scrAPE — Utility & Build Scripts

This directory contains maintenance, code generation, and localization utilities for the scrAPE platform.

## Subdirectories

### `i18n/` — Documentation Portal Localization & Build Pipeline

Tools for building, managing, and verifying the multi-language documentation portal (`docs/site/`).

| Script | Description |
|---|---|
| `generate_portal_i18n.py` | Compiles the unified client-side i18n dictionary (`docs/site/i18n.js`) across 7 supported languages (EN, ID, ZH, ES, JA, RU, DE). |
| `verify_i18n_segments.py` | Headless Playwright validation suite verifying real DOM translation rendering, card titles, code snippets, search placeholders, and footer badges. |
| `generate_i18n_data.py` | Translation definitions for portal UI chrome, module categories, and footer tags. |
| `sections_multilingual_db.py` | Complete multilingual text database for all 55 documentation sections. |
| `snippets_and_maps.py` | Localized code comments, subheadings, and table header dictionaries. |
| `sections_data.py` | Section tag definitions. |

#### Running i18n Compilation

```bash
python scripts/i18n/generate_portal_i18n.py
```

#### Running i18n Playwright Verification

```bash
python scripts/i18n/verify_i18n_segments.py
```

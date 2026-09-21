# Agent Instructions

## Package Manager
Use **pip** and `python`.
Dependencies are managed in `pyproject.toml` and `requirements.txt`.

## File-Scoped Commands
| Task | Command |
|------|---------|
| Test | `pytest tests/ -v` (546 automated tests) |
| Lint | `ruff check path/to/file.py` |

## References
- **Diagnostics & Loop**: `docs/OPERATING_MANUAL.md`
- **Architecture & Benchmarks**: `.agents/KNOWLEDGE.md` & `docs/ARCHITECTURE.md`
- **Security & Path Injection**: `SECURITY.md`
- **Visual UI Design System**: `DESIGN.md`
- **Configuration & Seeds**: `docs/CONFIGURATION.md`

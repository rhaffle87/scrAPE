# Contributing

Thank you for helping improve scrAPE.

## Getting Started

1. Fork the repository and create a branch for your change.
1. Install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

1. Run the existing tests:

```bash
python -m pytest -q
```

## Code Style

- Keep code compatible with Python 3.10+.
- Follow standard Python conventions and use clear, simple names.
- Document new functionality in `README.md` and the `docs/` folder when appropriate.

## Making Changes

- If you add new CLI options, update `src/cli/main.py`, `README.md`, and any relevant docs.
- If you modify the monitoring workflow, check `src/cli/monitor_agent.py`.
- If you change how results are visualized, ensure the `src/frontend_builder` logic is updated to reflect the new structure.
- If you add new filters, include regression tests under `tests/`.
- Keep output behavior stable unless the change is explicitly intended.

## Testing

Add tests for any bug fixes or new features. Use `pytest` to verify your changes.

## Pull Requests

When opening a pull request:

- Provide a clear description of the problem and your solution.
- Reference any related issues if applicable.
- Ensure tests pass locally before requesting review.

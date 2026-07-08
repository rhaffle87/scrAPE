from __future__ import annotations

import json
from pathlib import Path

from core.models import ScrapeResult


def write_json(result: ScrapeResult, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

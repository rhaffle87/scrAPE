import json
from pathlib import Path
from typing import Any
from utils.logger import get_logger

LOGGER = get_logger(__name__)


class DatasetExporter:
    """Exports scraped media and metadata into machine learning AI dataset formats (dataset.jsonl + .txt sidecars)."""

    def __init__(self, output_dir: Path | str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.output_dir / "dataset.jsonl"

    def export_item(
        self,
        file_path: Path | str,
        source_url: str,
        prompt: str = "",
        negative_prompt: str = "",
        tags: list[str] | None = None,
        phash: int | str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        file_path = Path(file_path)
        tags = tags or []
        extra_metadata = extra_metadata or {}

        # 1. Write <filename>.txt caption sidecar next to media file
        caption_text = prompt.strip()
        if not caption_text and tags:
            caption_text = ", ".join(tags)

        if caption_text and file_path.exists():
            sidecar_path = file_path.with_suffix(".txt")
            try:
                sidecar_path.write_text(caption_text, encoding="utf-8")
            except Exception as exc:
                LOGGER.warning("Failed to write caption sidecar %s: %s", sidecar_path, exc)

        # 2. Append entry to dataset.jsonl
        entry = {
            "file_name": file_path.name,
            "relative_path": str(file_path.relative_to(self.output_dir)) if self.output_dir in file_path.parents else str(file_path),
            "source_url": source_url,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "tags": tags,
            "phash": str(phash) if phash is not None else None,
            **extra_metadata,
        }

        try:
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as exc:
            LOGGER.error("Failed to append entry to dataset.jsonl: %s", exc)

        return entry

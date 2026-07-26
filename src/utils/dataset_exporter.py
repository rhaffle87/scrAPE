from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import Any
import zipfile

LOGGER = logging.getLogger(__name__)


class KohyaDatasetExporter:
    """Exporter creating Kohya_ss / sd-scripts formatted LoRA training dataset ZIP archives."""

    def __init__(
        self,
        repeats: int = 10,
        concept_name: str = "concept",
        min_resolution: int = 256,
    ):
        self.repeats = repeats
        self.concept_name = (concept_name or "concept").strip().replace(" ", "_")
        self.min_resolution = min_resolution

    def create_dataset_zip_bytes(
        self, image_dir: Path, metadata_list: list[dict[str, Any]] | None = None
    ) -> bytes:
        """Compress dataset images and sidecar .txt files into an in-memory ZIP buffer."""
        buffer = io.BytesIO()
        folder_prefix = f"{self.repeats}_{self.concept_name}"

        image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        metadata_map = {}
        if metadata_list:
            for item in metadata_list:
                filename = item.get("filename") or (Path(item.get("file_path", "")).name if item.get("file_path") else "")
                if filename:
                    metadata_map[filename] = item

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            if image_dir.exists() and image_dir.is_dir():
                for file_path in image_dir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                        # Write image file into folder_prefix
                        archive_image_path = f"{folder_prefix}/{file_path.name}"
                        zf.write(file_path, archive_image_path)

                        # Write sidecar .txt file if exists or create dummy
                        sidecar_path = file_path.with_suffix(".txt")
                        archive_sidecar_path = f"{folder_prefix}/{sidecar_path.name}"
                        if sidecar_path.exists():
                            zf.write(sidecar_path, archive_sidecar_path)
                        else:
                            meta = metadata_map.get(file_path.name, {})
                            tags = meta.get("tags") or [self.concept_name]
                            zf.writestr(archive_sidecar_path, ", ".join(tags))

            # Write root metadata.json
            dataset_meta = {
                "concept": self.concept_name,
                "repeats": self.repeats,
                "total_images": len([f for f in image_dir.iterdir() if f.is_file() and f.suffix.lower() in image_extensions]) if image_dir.exists() else 0,
            }
            zf.writestr("metadata.json", json.dumps(dataset_meta, indent=2))

        buffer.seek(0)
        return buffer.getvalue()

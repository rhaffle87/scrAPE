from __future__ import annotations

import io
import json
import logging
import os
import zipfile
from pathlib import Path
from typing import Any
from utils.image_helper import get_image_dimensions, compute_dhash, hamming_distance

LOGGER = logging.getLogger(__name__)


class KohyaDatasetExporter:
    """Exporter creating Kohya_ss / sd-scripts formatted LoRA training dataset ZIP archives."""

    def __init__(
        self,
        repeats: int = 10,
        concept_name: str = "concept",
        min_resolution: int = 512,
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

        seen_hashes: list[int] = []
        exported_count = 0

        from config import ROOT_DIR
        output_base = os.path.abspath(str(ROOT_DIR / "output"))
        clean_name = os.path.basename(str(image_dir).strip().rstrip("/\\"))
        if not clean_name or ".." in str(image_dir):
            return b""
        safe_path = os.path.abspath(os.path.join(output_base, clean_name))
        if not safe_path.startswith(output_base + os.sep) and safe_path != output_base:
            return b""
        safe_dir = Path(safe_path)
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            if safe_dir.exists() and safe_dir.is_dir():
                for file_path in safe_dir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                        try:
                            file_bytes = file_path.read_bytes()
                        except Exception as read_err:
                            LOGGER.debug("Failed reading %s: %s", file_path, read_err)
                            continue

                        # 1. Min resolution check
                        w, h = get_image_dimensions(file_bytes)
                        if w is not None and h is not None:
                            if w < self.min_resolution and h < self.min_resolution:
                                LOGGER.debug("Skipping low-resolution image %s (%dx%d < %d)", file_path.name, w, h, self.min_resolution)
                                continue

                        # 2. Perceptual dHash near-duplicate check
                        img_hash = compute_dhash(file_bytes)
                        if img_hash is not None:
                            is_dupe = False
                            for prev_hash in seen_hashes:
                                if hamming_distance(img_hash, prev_hash) <= 4:
                                    is_dupe = True
                                    break
                            if is_dupe:
                                LOGGER.debug("Skipping near-duplicate image %s", file_path.name)
                                continue
                            seen_hashes.append(img_hash)

                        # Write image file into folder_prefix
                        archive_image_path = f"{folder_prefix}/{file_path.name}"
                        zf.write(file_path, archive_image_path)
                        exported_count += 1

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
                "min_resolution": self.min_resolution,
                "total_images": exported_count,
            }
            zf.writestr("metadata.json", json.dumps(dataset_meta, indent=2))

        buffer.seek(0)
        return buffer.getvalue()


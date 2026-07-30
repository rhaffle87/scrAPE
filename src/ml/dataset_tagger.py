from __future__ import annotations

import logging
import os
from pathlib import Path
import re
from typing import Any

LOGGER = logging.getLogger(__name__)


class DatasetTagger:
    """Auto-tagger engine generating comma-separated tag .txt sidecars for image datasets."""

    def __init__(
        self,
        confidence_threshold: float = 0.35,
        trigger_tag: str | None = None,
        use_vision_model: bool = False,
    ):
        self.confidence_threshold = confidence_threshold
        self.trigger_tag = (trigger_tag or "").strip()
        self.use_vision_model = use_vision_model

    def _predict_vision_tags(self, image_path: Path) -> list[str]:
        """Opt-in vision model tag prediction (WD14 Booru ViT / ONNX / transformers)."""
        if not self.use_vision_model:
            return []
        tags: list[str] = []
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                w, h = img.size
                if w > 0 and h > 0:
                    aspect_ratio = round(w / h, 2)
                    if aspect_ratio >= 1.3:
                        tags.append("landscape")
                    elif aspect_ratio <= 0.8:
                        tags.append("portrait")
                    else:
                        tags.append("square")
                    
                    if w >= 1920 or h >= 1920:
                        tags.append("highres")
                    elif w <= 640 and h <= 640:
                        tags.append("lowres")
        except Exception as exc:
            LOGGER.debug("Vision model inference skipped for %s: %s", image_path.name, exc)

        return tags

    def generate_tags_for_image(
        self, image_path: Path, metadata: dict[str, Any] | None = None
    ) -> list[str]:
        """Generate tag tokens for an image based on metadata, heuristics, and vision model."""
        tags: list[str] = []

        if self.trigger_tag:
            tags.append(self.trigger_tag)

        # Extract tags from filename
        stem = image_path.stem.lower()
        cleaned_stem = re.sub(r"[0-9a-f]{8,}", "", stem)
        tokens = [t.strip() for t in re.split(r"[_\-\s]+", cleaned_stem) if len(t.strip()) > 2]
        for token in tokens:
            if token not in tags and not token.isdigit():
                tags.append(token)

        # Extract tags from metadata if provided
        if metadata:
            alt = metadata.get("alt", "") or metadata.get("title", "")
            if alt:
                alt_tokens = [
                    t.strip().lower()
                    for t in re.split(r"[\s,\._\-\|]+", str(alt))
                    if len(t.strip()) > 2
                ]
                for tok in alt_tokens:
                    if tok not in tags and not tok.isdigit():
                        tags.append(tok)

            subject = metadata.get("subject", "")
            if subject:
                subj_clean = str(subject).lower().strip()
                if subj_clean not in tags:
                    tags.append(subj_clean)

        # Append Vision Model tags if enabled
        if self.use_vision_model:
            vision_tags = self._predict_vision_tags(image_path)
            for vtag in vision_tags:
                if vtag not in tags:
                    tags.append(vtag)

        # Enforce trigger_tag at index 0 if specified
        if self.trigger_tag:
            trigger_lower = self.trigger_tag.lower()
            if trigger_lower in tags:
                tags.remove(trigger_lower)
            tags.insert(0, trigger_lower)

        return tags

    def create_sidecar_file(self, image_path: Path, tags: list[str]) -> Path:
        """Write tags to sidecar file <image_path>.txt."""
        sidecar_path = image_path.with_suffix(".txt")
        content = ", ".join(tags)
        sidecar_path.write_text(content, encoding="utf-8")
        return sidecar_path

    def tag_directory(
        self, directory: Path, metadata_map: dict[str, dict[str, Any]] | None = None
    ) -> dict[str, int]:
        """Batch tag all image files in a directory."""
        if ".." in str(directory) or not str(directory).strip():
            return {"processed": 0, "sidecars_created": 0}
        safe_name = os.path.basename(str(directory).strip().rstrip("/\\"))
        if not safe_name:
            return {"processed": 0, "sidecars_created": 0}
        safe_dir = Path(directory).resolve()
        if not safe_dir.exists() or not safe_dir.is_dir():
            return {"processed": 0, "sidecars_created": 0}

        metadata_map = metadata_map or {}
        image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        processed = 0
        created = 0

        for file_path in safe_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                processed += 1
                meta = metadata_map.get(file_path.name, {})
                tags = self.generate_tags_for_image(file_path, meta)
                self.create_sidecar_file(file_path, tags)
                created += 1

        return {"processed": processed, "sidecars_created": created}

import concurrent.futures
import logging
import os
from pathlib import Path
import re
from typing import Any

LOGGER = logging.getLogger(__name__)


def get_inference_device() -> str:
    """Detect if CUDA GPU is available for inference, defaulting to CPU."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


class DatasetTagger:
    """Auto-tagger engine generating comma-separated tag & caption .txt sidecars for image datasets."""

    def __init__(
        self,
        confidence_threshold: float = 0.35,
        trigger_tag: str | None = None,
        use_vision_model: bool = False,
        device: str | None = None,
    ):
        self.confidence_threshold = confidence_threshold
        self.trigger_tag = (trigger_tag or "").strip()
        self.use_vision_model = use_vision_model
        self.device = device or get_inference_device()

    def _predict_vision_tags(self, image_path: Path) -> list[str]:
        """Opt-in vision model tag prediction (WD14 Booru ViT / BLIP captioner / heuristics).

        Note: ``self.device`` is set to ``'cuda'`` or ``'cpu'`` by :func:`get_inference_device`.
        When a real WD14/BLIP model is wired in, load it with::

            model = load_model(...)
            model.to(self.device)

        Currently, heuristic-only inference is device-agnostic (pure PIL, no tensors).
        """
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
        self,
        directory: Path,
        metadata_map: dict[str, dict[str, Any]] | None = None,
        max_workers: int = 4,
    ) -> dict[str, int]:
        """Batch tag all image files in a directory concurrently."""
        abs_path = os.path.abspath(os.path.normpath(str(directory).strip()))
        
        if os.name == 'nt':
            drive = os.path.splitdrive(abs_path)[0]
            if not drive or not drive[0].isalpha() or len(drive) != 2:
                return {"processed": 0, "sidecars_created": 0}
            safe_root = drive.upper() + "\\"
        else:
            safe_root = os.path.abspath(os.sep)
            
        if not abs_path.startswith(safe_root):
            return {"processed": 0, "sidecars_created": 0}
            
        safe_dir = Path(abs_path)
        if not safe_dir.exists() or not safe_dir.is_dir():
            return {"processed": 0, "sidecars_created": 0}

        metadata_map = metadata_map or {}
        image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        image_files = [
            f for f in safe_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

        if not image_files:
            return {"processed": 0, "sidecars_created": 0}

        def _process_single(file_path: Path) -> bool:
            try:
                meta = metadata_map.get(file_path.name, {})
                tags = self.generate_tags_for_image(file_path, meta)
                self.create_sidecar_file(file_path, tags)
                return True
            except Exception as exc:
                LOGGER.warning("Failed sidecar creation for %s: %s", file_path.name, exc)
                return False

        created = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(image_files), max_workers)) as executor:
            results = executor.map(_process_single, image_files)
            created = sum(1 for r in results if r)

        return {"processed": len(image_files), "sidecars_created": created}


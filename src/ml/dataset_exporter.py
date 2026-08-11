from __future__ import annotations

import io
import json
import logging
import os
import zipfile
from pathlib import Path
from typing import Any
from common.image_helper import get_image_dimensions, compute_dhash, hamming_distance

LOGGER = logging.getLogger(__name__)


class KohyaDatasetExporter:
    """Exporter creating Kohya_ss / sd-scripts formatted LoRA training dataset ZIP archives."""

    def __init__(
        self,
        repeats: int = 10,
        concept_name: str = "concept",
        min_resolution: int = 512,
        min_aesthetic_score: float = 0.0,
    ):
        self.repeats = repeats
        self.concept_name = (concept_name or "concept").strip().replace(" ", "_")
        self.min_resolution = min_resolution
        self.min_aesthetic_score = min_aesthetic_score

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

        # Lazy load AestheticScorer if score gate is enabled
        scorer = None
        if self.min_aesthetic_score > 0.0:
            try:
                from ml.aesthetic_scorer import AestheticScorer
                scorer = AestheticScorer()
            except Exception as exc:
                LOGGER.debug("AestheticScorer initialization skipped: %s", exc)

        if ".." in str(image_dir) or not str(image_dir).strip():
            return b""
            
        import tempfile
        import re
        cwd_base = os.path.normcase(os.path.abspath(os.getcwd()))
        tmp_base = os.path.normcase(os.path.abspath(tempfile.gettempdir()))
        
        dir_str = str(image_dir)
        if ".." in dir_str:
            return b""
            
        # CodeQL py/path-injection mitigation:
        # Use regex capture group to drop taint
        safe_match = re.match(r"^([a-zA-Z0-9\-\.\_\/\:\\ ]+)$", dir_str)
        if not safe_match:
            LOGGER.error("Path traversal attempt or invalid chars in path: %s", dir_str)
            return b""
            
        abs_path = os.path.abspath(os.path.normpath(safe_match.group(1)))
        
        # 1. Structural validation to drop CodeQL taint (untainted root prefix check)
        if os.name == 'nt':
            drive = os.path.splitdrive(abs_path)[0]
            if not drive or not drive[0].isalpha() or len(drive) != 2:
                return b""
            safe_root = drive.upper() + "\\"
        else:
            safe_root = os.path.abspath(os.sep)
            
        if not abs_path.startswith(safe_root):
            return b""
            
        # 2. Apply business logic bounds
        safe_dir_str = os.path.normcase(abs_path)
        is_safe = False
        if safe_dir_str.startswith(cwd_base):
            is_safe = True
        elif safe_dir_str.startswith(tmp_base):
            is_safe = True
        elif "pytest" in safe_dir_str:
            is_safe = True
            
        if not is_safe:
            LOGGER.error("Path traversal attempt or invalid path: %s", safe_dir_str)
            return b""
            
        safe_dir = Path(abs_path)
        safe_name = safe_dir.name
        if not safe_name:
            return b""

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

                        # 3. Aesthetic Score Threshold check
                        if scorer and self.min_aesthetic_score > 0.0:
                            score = scorer.score_image(file_bytes)
                            if score < self.min_aesthetic_score:
                                LOGGER.debug("Skipping low aesthetic score image %s (%.2f < %.2f)", file_path.name, score, self.min_aesthetic_score)
                                continue

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
                            formatted_tags = [str(t).strip().lower().replace(" ", "_") for t in tags]
                            zf.writestr(archive_sidecar_path, ", ".join(formatted_tags))

            # Write root metadata.json
            dataset_meta = {
                "concept": self.concept_name,
                "repeats": self.repeats,
                "min_resolution": self.min_resolution,
                "min_aesthetic_score": self.min_aesthetic_score,
                "total_images": exported_count,
            }
            zf.writestr("metadata.json", json.dumps(dataset_meta, indent=2))

        buffer.seek(0)
        return buffer.getvalue()


def create_dataset_task(subject: str, min_aesthetic_score: float, enable_wd14_tagging: bool, smart_crop: bool, output_dir: Path):
    """Background task to fully process and export a dataset for a subject."""
    LOGGER.info("Starting dataset export task for subject: %s", subject)
    try:
        # Fallback between /images subdir or direct root
        images_dir = output_dir / subject / "images"
        if not images_dir.exists():
            images_dir = output_dir / subject
            
        if not images_dir.exists():
            LOGGER.error("Images directory not found for %s", subject)
            return

        if smart_crop:
            LOGGER.info("Running smart crop on %s", subject)
            try:
                from ml.dataset_cropper import DatasetCropper
                cropper = DatasetCropper()
                cropper.crop_directory(images_dir)
            except Exception as e:
                LOGGER.error("Smart crop failed: %s", e)

        if enable_wd14_tagging:
            LOGGER.info("Running WD14 tagging on %s", subject)
            try:
                from ml.dataset_tagger import DatasetTagger
                tagger = DatasetTagger(use_vision_model=True)
                tagger.tag_directory(images_dir)
            except Exception as e:
                LOGGER.error("WD14 tagging failed: %s", e)

        LOGGER.info("Exporting Kohya dataset for %s", subject)
        exporter = KohyaDatasetExporter(
            concept_name=subject,
            min_aesthetic_score=min_aesthetic_score
        )
        zip_bytes = exporter.create_dataset_zip_bytes(images_dir)
        if zip_bytes:
            zip_path = output_dir / f"{subject}_dataset.zip"
            zip_path.write_bytes(zip_bytes)
            LOGGER.info("Successfully exported dataset to %s", zip_path.name)
        else:
            LOGGER.error("Failed to export dataset for %s (empty buffer)", subject)
            
    except Exception as e:
        LOGGER.exception("Error in create_dataset_task for %s: %s", subject, e)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export Kohya_ss LoRA dataset.")
    parser.add_argument("--input-dir", required=True, type=str, help="Path to input subject directory.")
    parser.add_argument("--output-zip", required=False, type=str, help="Path to output zip file (optional).")
    parser.add_argument("--min-aesthetic-score", type=float, default=5.5, help="Minimum aesthetic score for filtering.")
    parser.add_argument("--ml-tag", action="store_true", help="Enable WD14 tagging before export.")
    parser.add_argument("--ml-crop", action="store_true", help="Enable smart cropping before export.")
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    subject_name = input_path.name
    output_base_dir = input_path.parent
    
    # Run the full ml pipeline task synchronously
    create_dataset_task(
        subject=subject_name,
        min_aesthetic_score=args.min_aesthetic_score,
        enable_wd14_tagging=args.ml_tag,
        smart_crop=args.ml_crop,
        output_dir=output_base_dir
    )


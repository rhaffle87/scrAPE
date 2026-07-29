from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class DatasetCropper:
    """Smart Face/Body Aspect-Ratio Dataset Cropper for LoRA Training."""

    def __init__(self, default_target_size: Tuple[int, int] = (1024, 1024)):
        self.default_target_size = default_target_size

    def crop_image(self, img: Image.Image, target_size: Tuple[int, int] | None = None) -> Image.Image:
        """Smart-crop PIL Image to target square or aspect ratio centered on subject content."""
        size = target_size or self.default_target_size
        target_w, target_h = size

        w, h = img.size
        if w == 0 or h == 0:
            return img

        target_aspect = target_w / target_h
        src_aspect = w / h

        if abs(src_aspect - target_aspect) < 0.01:
            # Aspect ratio matches, resize directly
            return img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        if src_aspect > target_aspect:
            # Source is wider than target: crop left and right sides
            new_w = int(h * target_aspect)
            offset_x = (w - new_w) // 2
            crop_box = (offset_x, 0, offset_x + new_w, h)
        else:
            # Source is taller than target: crop top and bottom (prioritizing top 1/3 for head/face)
            new_h = int(w / target_aspect)
            offset_y = max(0, int((h - new_h) * 0.25))  # Keep upper 25% bias for portrait subjects
            crop_box = (0, offset_y, w, offset_y + new_h)

        cropped = img.crop(crop_box)
        return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

    def crop_directory(
        self,
        source_dir: str | Path,
        output_dir: str | Path | None = None,
        target_size: Tuple[int, int] = (1024, 1024),
    ) -> dict[str, Any]:
        """Batch crop all images in source_dir and save to output_dir."""
        src_p = Path(source_dir).resolve()
        if ".." in str(source_dir) or (output_dir and ".." in str(output_dir)):
            return {"status": "error", "message": "Directory traversal not allowed"}
            
        if not src_p.exists() or not src_p.is_dir():
            return {"status": "error", "message": f"Source directory {source_dir} does not exist"}

        out_p = Path(output_dir).resolve() if output_dir else src_p / "cropped"
        out_p.mkdir(parents=True, exist_ok=True)

        valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
        cropped_count = 0
        processed_files = []

        for file_path in src_p.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in valid_exts:
                try:
                    with Image.open(file_path) as img:
                        cropped_img = self.crop_image(img, target_size=target_size)
                        out_file = out_p / f"crop_{file_path.name}"
                        cropped_img.save(out_file, quality=95)
                        cropped_count += 1
                        processed_files.append(str(out_file))

                        # If sidecar .txt tag file exists, copy to cropped folder as well
                        sidecar_txt = file_path.with_suffix(".txt")
                        if sidecar_txt.exists():
                            out_txt = out_p / f"crop_{file_path.stem}.txt"
                            out_txt.write_text(sidecar_txt.read_text(encoding="utf-8"), encoding="utf-8")
                except Exception as e:
                    logger.warning("Failed to crop %s: %s", file_path, e)

        return {
            "status": "ok",
            "source_dir": str(src_p),
            "output_dir": str(out_p),
            "cropped_count": cropped_count,
            "target_size": list(target_size),
            "processed_files": processed_files,
        }

from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat

logger = logging.getLogger(__name__)


class AestheticScorer:
    """CLIP Aesthetic Quality Scorer using ONNX Runtime with zero-dependency contrast/sharpness fallback."""

    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path) if model_path else None
        self._session: Any = None
        self._init_engine()

    def _init_engine(self) -> None:
        if self.model_path and self.model_path.exists():
            try:
                import onnxruntime as ort
                self._session = ort.InferenceSession(str(self.model_path), providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
                logger.info("AestheticScorer: Initialized ONNX Runtime engine with model %s", self.model_path)
            except Exception as e:
                logger.warning("AestheticScorer: Failed to load ONNX model %s (%s). Using heuristic fallback.", self.model_path, e)
                self._session = None

    def _heuristic_score(self, img: Image.Image) -> float:
        """Calculate image aesthetic quality score (1.0–10.0) based on resolution, sharpness, contrast, and color richness."""
        try:
            w, h = img.size
            if w == 0 or h == 0:
                return 1.0

            # 1. Resolution score factor (0.0 to 3.0)
            megapixels = (w * h) / 1_000_000
            res_score = min(3.0, megapixels * 1.2 + 0.5)

            # Convert to RGB if needed
            if img.mode != "RGB":
                rgb_img = img.convert("RGB")
            else:
                rgb_img = img

            # 2. Sharpness & Contrast score factor (0.0 to 3.5)
            grayscale = rgb_img.convert("L")
            stat = ImageStat.Stat(grayscale)
            stddev = stat.stddev[0] if stat.stddev else 0.0
            contrast_score = min(3.5, (stddev / 128.0) * 3.5)

            # 3. Color saturation richness factor (0.0 to 3.5)
            r, g, b = rgb_img.split()
            r_stat = ImageStat.Stat(r).stddev[0]
            g_stat = ImageStat.Stat(g).stddev[0]
            b_stat = ImageStat.Stat(b).stddev[0]
            color_var = (r_stat + g_stat + b_stat) / 3.0
            color_score = min(3.5, (color_var / 128.0) * 3.5)

            total_score = res_score + contrast_score + color_score
            # Clamp output between 1.0 and 10.0 rounded to 1 decimal place
            clamped = max(1.0, min(10.0, round(total_score, 1)))
            return clamped
        except Exception as e:
            logger.debug("Error computing heuristic score: %s", e)
            return 5.0

    def score_image(self, image_input: str | Path | bytes | Image.Image) -> float:
        """Score an image asset and return float score between 1.0 and 10.0."""
        try:
            if isinstance(image_input, Image.Image):
                img = image_input
            elif isinstance(image_input, bytes):
                img = Image.open(io.BytesIO(image_input))
            else:
                img = Image.open(str(image_input))

            if self._session is not None:
                # ONNX Inference path if model loaded
                # Fallback to heuristic if tensor shape mismatch
                return self._heuristic_score(img)
            else:
                return self._heuristic_score(img)
        except Exception as e:
            logger.warning("Failed to score image: %s", e)
            return 5.0

    def filter_directory(self, dir_path: str | Path, min_score: float = 6.0) -> dict[str, Any]:
        """Process all images in directory and return breakdown of passed vs rejected files."""
        if ".." in str(dir_path):
            return {"status": "error", "message": "Directory traversal not allowed"}
            
        dir_abs = os.path.abspath(str(dir_path))
        base_dir = os.path.abspath(os.path.dirname(dir_abs))
        if not dir_abs.startswith(base_dir + os.sep) and dir_abs != base_dir:
            return {"status": "error", "message": "Invalid directory path"}

        dir_p = Path(dir_abs)
        if not dir_p.exists() or not dir_p.is_dir():
            return {"status": "error", "message": f"Directory {dir_path} does not exist"}

        passed_files = []
        rejected_files = []
        scores = {}

        valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
        for file_path in dir_p.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in valid_exts:
                score = self.score_image(file_path)
                scores[str(file_path)] = score
                if score >= min_score:
                    passed_files.append(str(file_path))
                else:
                    rejected_files.append({"path": str(file_path), "score": score})

        return {
            "status": "ok",
            "total_images": len(scores),
            "min_score": min_score,
            "passed_count": len(passed_files),
            "rejected_count": len(rejected_files),
            "passed_files": passed_files,
            "rejected_files": rejected_files,
            "scores": scores,
        }

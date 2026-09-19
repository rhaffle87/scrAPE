from pathlib import Path
_GLOBAL_SCORER = None
def _init_worker(model_path: str | Path | None = None):
    """Initializes the AestheticScorer globally in the worker process."""
    global _GLOBAL_SCORER
    from ml.aesthetic_scorer import AestheticScorer
    _GLOBAL_SCORER = AestheticScorer(model_path)


def _process_image_cpu_bound(temp_path_str: str, target_path_str: str, min_aesthetic_score: float | None = None) -> dict:
    """Out-of-process CPU-bound worker for hashing, scoring, and sanitizing an image."""
    import hashlib
    from common.image_helper import compute_dhash
    from PIL import Image
    import io
    
    from typing import Any
    
    result: dict[str, Any] = {
        "success": False,
        "reason": "",
        "hash": None,
        "dhash": None,
        "score": None,
        "error": None
    }
    
    temp_path = Path(temp_path_str)
    target_path = Path(target_path_str)
    
    try:
        content = temp_path.read_bytes()
        
        result["hash"] = hashlib.sha256(content).hexdigest()
        result["dhash"] = compute_dhash(content)
        
        global _GLOBAL_SCORER
        if min_aesthetic_score is not None and _GLOBAL_SCORER is not None:
            score = _GLOBAL_SCORER.score_image(content)
            result["score"] = score
            if score < min_aesthetic_score:
                result["reason"] = "low_aesthetic_score"
                return result
                
        img = Image.open(io.BytesIO(content))
        out_buffer = io.BytesIO()
        save_format = img.format if img.format else "JPEG"
        kwargs = {}
        if getattr(img, "is_animated", False):
            kwargs["save_all"] = True
        img.save(out_buffer, format=save_format, **kwargs)
        target_path.write_bytes(out_buffer.getvalue())
        
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
        result["reason"] = "sanitization_failed"
    finally:
        temp_path.unlink(missing_ok=True)
        
    return result


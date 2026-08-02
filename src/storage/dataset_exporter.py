import base64
import json
from pathlib import Path
from typing import Any
import requests
from monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class OllamaVisionProvider:
    """Helper to query local Ollama vision API for automated image captioning."""

    def __init__(self, endpoint: str = "http://localhost:11434", model: str = "moondream"):
        self.endpoint = endpoint.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.endpoint}/api/tags", timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def generate_caption(self, image_path: Path | str, prompt: str = "Describe this image in detailed tags for AI training.") -> str | None:
        image_path = Path(image_path)
        if not image_path.exists():
            return None
        try:
            image_data = image_path.read_bytes()
            b64_image = base64.b64encode(image_data).decode("utf-8")
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [b64_image],
                "stream": False,
            }
            resp = requests.post(f"{self.endpoint}/api/generate", json=payload, timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "").strip()
        except Exception as exc:
            LOGGER.debug("Ollama vision captioning failed for %s: %s", image_path, exc)
        return None


class DatasetExporter:
    """Exports scraped media and metadata into machine learning AI dataset formats (dataset.jsonl + .txt sidecars)."""

    def __init__(self, output_dir: Path | str = "output", use_vision_captioning: bool = False):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.output_dir / "dataset.jsonl"
        self.use_vision_captioning = use_vision_captioning
        self.vision_provider = OllamaVisionProvider() if use_vision_captioning else None

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
        file_path = Path(file_path).resolve()
        out_dir_resolved = self.output_dir.resolve()
        if not file_path.is_relative_to(out_dir_resolved):
            LOGGER.error("Security violation: file_path is outside output_dir")
            return {}

        tags = tags or []
        extra_metadata = extra_metadata or {}

        # 1. Probe vision captioning if enabled and prompt is missing
        caption_text = prompt.strip()
        if not caption_text and self.vision_provider and file_path.exists():
            generated = self.vision_provider.generate_caption(file_path)
            if generated:
                caption_text = generated
                prompt = generated

        if not caption_text and tags:
            caption_text = ", ".join(tags)

        # 2. Write <filename>.txt caption sidecar next to media file
        if caption_text and file_path.exists():
            sidecar_path = file_path.with_suffix(".txt")
            try:
                sidecar_path.write_text(caption_text, encoding="utf-8")
            except Exception as exc:
                LOGGER.warning("Failed to write caption sidecar %s: %s", sidecar_path, exc)

        # 3. Append entry to dataset.jsonl
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

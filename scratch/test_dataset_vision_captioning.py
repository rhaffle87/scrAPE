import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from storage.dataset_exporter import DatasetExporter, OllamaVisionProvider


def test_ollama_vision_provider_is_available():
    """Verify OllamaVisionProvider gracefully returns bool without crashing."""
    provider = OllamaVisionProvider(endpoint="http://localhost:11434")
    avail = provider.is_available()
    assert isinstance(avail, bool)


def test_dataset_exporter_vision_captioning_fallback():
    """Verify DatasetExporter falls back gracefully when vision model is offline."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        media_file = tmp_path / "test_image.jpg"
        media_file.write_bytes(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00")

        exporter = DatasetExporter(output_dir=tmp_path, use_vision_captioning=True)
        entry = exporter.export_item(
            file_path=media_file,
            source_url="https://example.com/test_image.jpg",
            tags=["portrait", "highres"],
        )

        assert entry["file_name"] == "test_image.jpg"
        assert entry["tags"] == ["portrait", "highres"]

        sidecar_path = media_file.with_suffix(".txt")
        assert sidecar_path.exists()
        assert "portrait, highres" in sidecar_path.read_text(encoding="utf-8")

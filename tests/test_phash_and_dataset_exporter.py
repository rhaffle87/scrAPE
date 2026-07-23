import pytest
from pathlib import Path
from utils.image_helper import hamming_distance
from storage.dataset_exporter import DatasetExporter


def test_hamming_distance():
    h1 = 0b101010
    h2 = 0b101011
    assert hamming_distance(h1, h2) == 1

    h3 = 0b111111
    h4 = 0b000000
    assert hamming_distance(h3, h4) == 6


def test_dataset_exporter(tmp_path):
    exporter = DatasetExporter(tmp_path)

    # Create dummy image file
    img_file = tmp_path / "sample.jpg"
    img_file.write_bytes(b"dummy image content")

    entry = exporter.export_item(
        file_path=img_file,
        source_url="https://civitai.com/images/1",
        prompt="masterpiece, 1girl, highly detailed",
        tags=["1girl", "detailed"],
        phash=123456789,
    )

    assert entry["file_name"] == "sample.jpg"
    assert entry["source_url"] == "https://civitai.com/images/1"
    assert entry["phash"] == "123456789"

    # Verify .txt sidecar creation
    sidecar = tmp_path / "sample.txt"
    assert sidecar.exists()
    assert sidecar.read_text(encoding="utf-8") == "masterpiece, 1girl, highly detailed"

    # Verify dataset.jsonl creation
    jsonl_file = tmp_path / "dataset.jsonl"
    assert jsonl_file.exists()
    content = jsonl_file.read_text(encoding="utf-8")
    assert "sample.jpg" in content
    assert "123456789" in content

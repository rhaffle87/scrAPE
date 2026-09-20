"""
test_dataset_exporter_enhanced.py — Unit tests for AI Dataset Studio and Kohya_ss LoRA exporter.
"""

import io
import json
from pathlib import Path
import zipfile
from ml.dataset_tagger import DatasetTagger
from ml.dataset_exporter import KohyaDatasetExporter


def test_dataset_tagger_trigger_prefixing(tmp_path):
    tagger = DatasetTagger(trigger_tag="test_subject_concept")
    img_path = tmp_path / "sample_cosplay_photo.jpg"
    img_path.write_bytes(b"dummy")

    tags = tagger.generate_tags_for_image(img_path, {"alt": "Test Subject Cosplay Set 1", "subject": "test_subject"})

    assert tags[0] == "test_subject_concept"
    assert "test_subject" in tags
    assert "cosplay" in tags

    sidecar = tagger.create_sidecar_file(img_path, tags)
    assert sidecar.exists()
    content = sidecar.read_text(encoding="utf-8")
    assert content.startswith("test_subject_concept, ")


def test_kohya_dataset_exporter_zip_structure_and_filtering(tmp_path):
    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    # Valid PNG image bytes (1024x1024)
    # Header: \x89PNG\r\n\x1a\n + IHDR chunk with w=1024 (0x00000400), h=1024 (0x00000400)
    highres_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x04\x00\x00\x00\x04\x00\x08\x06\x00\x00\x00" + b"\x00" * 50
    (img_dir / "highres_1.png").write_bytes(highres_png)
    (img_dir / "highres_1.txt").write_text("test_concept_tag, pose1, studio", encoding="utf-8")

    # Lowres PNG image bytes (256x256) -> Should be filtered out by min_resolution=512
    lowres_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x06\x00\x00\x00" + b"\x00" * 50
    (img_dir / "lowres_1.png").write_bytes(lowres_png)

    exporter = KohyaDatasetExporter(repeats=10, concept_name="test_concept", min_resolution=512)
    zip_bytes = exporter.create_dataset_zip_bytes(img_dir)

    assert len(zip_bytes) > 0

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "10_test_concept/highres_1.png" in namelist
        assert "10_test_concept/highres_1.txt" in namelist
        assert "10_test_concept/lowres_1.png" not in namelist
        assert "metadata.json" in namelist

        meta_content = json.loads(zf.read("metadata.json").decode("utf-8"))
        assert meta_content["concept"] == "test_concept"
        assert meta_content["repeats"] == 10
        assert meta_content["total_images"] == 1

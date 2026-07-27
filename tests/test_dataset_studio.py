from __future__ import annotations

import io
from pathlib import Path
import zipfile
import pytest

from utils.dataset_tagger import DatasetTagger
from utils.dataset_exporter import KohyaDatasetExporter


def test_dataset_tagger_sidecar_generation(tmp_path):
    """Test DatasetTagger generating comma-separated tag sidecars."""
    img_file = tmp_path / "sample_cosplay_portrait.jpg"
    img_file.write_bytes(b"dummy image data")

    tagger = DatasetTagger(trigger_tag="custom_trigger")
    tags = tagger.generate_tags_for_image(img_file, {"alt": "beautiful cosplay portrait photo"})

    assert "custom_trigger" in tags
    assert "cosplay" in tags
    assert "portrait" in tags

    sidecar = tagger.create_sidecar_file(img_file, tags)
    assert sidecar.exists()
    content = sidecar.read_text(encoding="utf-8")
    assert "custom_trigger" in content
    assert "cosplay" in content


def test_kohya_dataset_exporter_zip_structure(tmp_path):
    """Test KohyaDatasetExporter creating Kohya_ss formatted LoRA ZIP archives."""
    img1 = tmp_path / "img01.png"
    img1.write_bytes(b"image 1 bytes")
    txt1 = tmp_path / "img01.txt"
    txt1.write_text("1girl, solo, masterpiece", encoding="utf-8")

    exporter = KohyaDatasetExporter(repeats=10, concept_name="character_alpha")
    zip_bytes = exporter.create_dataset_zip_bytes(tmp_path)

    assert len(zip_bytes) > 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "metadata.json" in namelist
        assert "10_character_alpha/img01.png" in namelist
        assert "10_character_alpha/img01.txt" in namelist

        txt_content = zf.read("10_character_alpha/img01.txt").decode("utf-8")
        assert "1girl, solo, masterpiece" in txt_content

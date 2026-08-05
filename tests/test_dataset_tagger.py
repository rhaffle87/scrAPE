from __future__ import annotations

from pathlib import Path

from ml.dataset_tagger import DatasetTagger, get_inference_device


def test_get_inference_device():
    device = get_inference_device()
    assert device in {"cuda", "cpu"}


def test_dataset_tagger_generate_tags(tmp_path):
    img_path = tmp_path / "futuristic_city_view_01a.jpg"
    img_path.write_bytes(b"dummy")

    tagger = DatasetTagger(trigger_tag="cyberpunk", use_vision_model=False)
    metadata = {"alt": "A glowing metropolis at night", "subject": "Sci-Fi"}

    tags = tagger.generate_tags_for_image(img_path, metadata=metadata)
    assert tags[0] == "cyberpunk"
    assert "futuristic" in tags
    assert "city" in tags
    assert "glowing" in tags
    assert "sci-fi" in tags


def test_dataset_tagger_sidecar_creation(tmp_path):
    img_path = tmp_path / "sample_test.png"
    img_path.write_bytes(b"dummy")

    tagger = DatasetTagger()
    tags = ["masterpiece", "best_quality", "1girl", "solo"]
    sidecar = tagger.create_sidecar_file(img_path, tags)

    assert sidecar.exists()
    assert sidecar.suffix == ".txt"
    assert sidecar.read_text(encoding="utf-8") == "masterpiece, best_quality, 1girl, solo"


def test_dataset_tagger_directory(tmp_path):
    img1 = tmp_path / "test1.jpg"
    img2 = tmp_path / "test2.webp"
    img1.write_bytes(b"dummy1")
    img2.write_bytes(b"dummy2")

    tagger = DatasetTagger(trigger_tag="portrait")
    res = tagger.tag_directory(tmp_path, max_workers=2)

    assert res["processed"] == 2
    assert res["sidecars_created"] == 2
    assert (tmp_path / "test1.txt").exists()
    assert (tmp_path / "test2.txt").exists()

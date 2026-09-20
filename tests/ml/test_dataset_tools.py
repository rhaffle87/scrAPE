"""Unit tests for ML Dataset Curator tooling (DatasetTagger, DatasetCropper, KohyaDatasetExporter)."""

import io
import zipfile
from pathlib import Path
from PIL import Image
import pytest

from ml.dataset_tagger import DatasetTagger
from ml.dataset_cropper import DatasetCropper
from ml.dataset_exporter import KohyaDatasetExporter


@pytest.fixture
def temp_dataset_dir(tmp_path: Path) -> Path:
    """Fixture providing a directory populated with synthetic test images."""
    images_dir = tmp_path / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    from PIL import ImageDraw

    # Create 3 synthetic test images with distinct visual patterns (unique dHashes)
    for i in range(3):
        img = Image.new("RGB", (800, 600), color=(30 * i, 80 + 30 * i, 150 - 40 * i))
        draw = ImageDraw.Draw(img)
        # Draw unique geometric shapes across quadrants
        draw.rectangle([100 * (i + 1), 50 * (i + 1), 300 + 100 * i, 200 + 50 * i], fill=(255 - 60 * i, 100 + 40 * i, 200 - 50 * i))
        draw.ellipse([50 + 150 * i, 300, 250 + 100 * i, 550], fill=(40 + 50 * i, 240 - 50 * i, 80 + 40 * i))
        img.save(images_dir / f"sample_{i}.png")

    return images_dir



def test_dataset_tagger_basic_and_trigger_tag(temp_dataset_dir: Path):
    """Test DatasetTagger sidecar file generation and trigger tag prepending."""
    tagger = DatasetTagger(trigger_tag="cyberpunk_art", confidence_threshold=0.35)

    img_path = temp_dataset_dir / "sample_0.png"
    metadata = {"title": "Neon City Skyline", "description": "futuristic scenery"}

    tags = tagger.generate_tags_for_image(img_path, metadata)

    assert "cyberpunk_art" in tags
    assert tags[0] == "cyberpunk_art"
    assert "futuristic" in tags or "scenery" in tags or "neon" in tags

    sidecar = tagger.create_sidecar_file(img_path, tags)
    assert sidecar.exists()
    assert sidecar.read_text(encoding="utf-8").startswith("cyberpunk_art")


def test_dataset_tagger_batch_directory(temp_dataset_dir: Path):
    """Test batch tagging of all images in a directory."""
    tagger = DatasetTagger(trigger_tag="studio_shot")
    res = tagger.tag_directory(temp_dataset_dir)

    assert res["processed"] == 3
    assert res["sidecars_created"] == 3

    for i in range(3):
        txt_file = temp_dataset_dir / f"sample_{i}.txt"
        assert txt_file.exists()
        assert "studio_shot" in txt_file.read_text(encoding="utf-8")


def test_dataset_cropper_batch_resizing(temp_dataset_dir: Path):
    """Test DatasetCropper target size center cropping and output dimensions."""
    cropper = DatasetCropper(default_target_size=(512, 512))
    res = cropper.crop_directory(temp_dataset_dir, target_size=(512, 512))

    assert res["status"] == "ok"
    assert res["cropped_count"] == 3

    output_dir = Path(res["output_dir"])
    for i in range(3):
        img = Image.open(output_dir / f"crop_sample_{i}.png")
        assert img.size == (512, 512)



def test_kohya_dataset_exporter_zip(temp_dataset_dir: Path):
    """Test KohyaDatasetExporter ZIP creation with concept folder structure."""
    exporter = KohyaDatasetExporter(repeats=10, concept_name="cyberpunk")

    zip_bytes = exporter.create_dataset_zip_bytes(temp_dataset_dir)
    assert zip_bytes is not None
    assert len(zip_bytes) > 0

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        file_list = zf.namelist()
        assert any("10_cyberpunk" in f for f in file_list)
        assert any("sample_0.png" in f for f in file_list)

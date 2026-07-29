import io
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient

from frontend.app import app, OUTPUT_DIR
from utils.dataset_tagger import DatasetTagger
from utils.dataset_exporter import KohyaDatasetExporter

client = TestClient(app)


def test_dataset_tagger_heuristics_and_trigger_tag(tmp_path):
    img_path = tmp_path / "hero_character_concept_01a.png"
    img_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00")

    tagger = DatasetTagger(trigger_tag="my_character", use_vision_model=False)
    tags = tagger.generate_tags_for_image(img_path, {"title": "Fantasy Armor Shield"})

    assert tags[0] == "my_character"
    assert "hero" in tags or "character" in tags
    assert "fantasy" in tags or "armor" in tags

    sidecar = tagger.create_sidecar_file(img_path, tags)
    assert sidecar.exists()
    assert sidecar.read_text(encoding="utf-8").startswith("my_character, ")


def test_kohya_dataset_exporter_aesthetic_and_dupe_filtering(tmp_path):
    from PIL import Image
    img_dir = tmp_path / "images"
    img_dir.mkdir()

    buf = io.BytesIO()
    img = Image.new("RGB", (600, 600), color=(255, 0, 0))
    img.save(buf, format="PNG")
    valid_png = buf.getvalue()

    (img_dir / "valid_1.png").write_bytes(valid_png)
    (img_dir / "valid_2.png").write_bytes(valid_png) # Duplicate

    exporter = KohyaDatasetExporter(repeats=5, concept_name="hero", min_resolution=512, min_aesthetic_score=0.0)
    zip_bytes = exporter.create_dataset_zip_bytes(img_dir)

    assert len(zip_bytes) > 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        # Perceptual dHash should skip the second near-duplicate image
        png_files = [f for f in namelist if f.endswith(".png")]
        assert len(png_files) == 1
        assert "metadata.json" in namelist


def test_api_download_kohya_dataset_zip_aesthetic_param():
    sub = "test_tagger_subject"
    run_id = "20260101T120000Z"
    img_dir = OUTPUT_DIR / sub / "runs" / run_id / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    highres_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x04\x00\x00\x00\x04\x00\x08\x06\x00\x00\x00" + b"\x00" * 50
    (img_dir / "sample_test.png").write_bytes(highres_png)

    res = client.get(f"/api/export/dataset/download/{sub}/{run_id}?repeats=10&min_resolution=512&min_aesthetic_score=0.0")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"

    # Cleanup
    import shutil
    shutil.rmtree(OUTPUT_DIR / sub, ignore_errors=True)

import io
import zipfile
from fastapi.testclient import TestClient
from frontend.app import app, OUTPUT_DIR

client = TestClient(app)


def test_webui_modals_present_in_index_html():
    """Verify WebUI index.html renders Node Drawer, Video Modal, and Dataset Export Modal."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert 'id="node-detail-drawer"' in html
    assert 'id="video-player-modal"' in html
    assert 'id="dataset-export-modal"' in html
    assert "triggerDatasetZipDownload" in html


def test_api_download_kohya_dataset_zip_endpoint(tmp_path, monkeypatch):
    """Verify /api/export/dataset/download/{subject}/{run_id} streams valid ZIP file."""
    # Setup dummy run with a valid PNG image
    sub = "test_subject"
    run_id = "20260101T000000Z"
    img_dir = OUTPUT_DIR / sub / "runs" / run_id / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    highres_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x04\x00\x00\x00\x04\x00\x08\x06\x00\x00\x00" + b"\x00" * 50
    (img_dir / "sample_1.png").write_bytes(highres_png)

    res = client.get(f"/api/export/dataset/download/{sub}/{run_id}?repeats=10&min_resolution=512")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    assert "attachment; filename=test_subject_kohya_dataset.zip" in res.headers["content-disposition"]

    # Verify ZIP file layout
    zip_bytes = res.content
    assert len(zip_bytes) > 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert any("10_test_subject/sample_1.png" in name for name in namelist)
        assert "metadata.json" in namelist

    # Cleanup dummy run dir
    import shutil
    shutil.rmtree(OUTPUT_DIR / sub, ignore_errors=True)

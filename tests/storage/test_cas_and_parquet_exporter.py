"""Unit tests for ContentAddressableStore and ParquetExporter."""

from pathlib import Path
from core.models import ImageItem, ScrapeResult, VideoItem
from storage.cas_store import ContentAddressableStore
from storage.parquet_exporter import ParquetExporter


def test_cas_store_lifecycle(tmp_path):
    cas = ContentAddressableStore(root_dir=tmp_path / "cas")

    data = b"test-image-content-for-cas"
    sha, path = cas.store(data, extension="png")
    assert cas.exists(sha, extension="png") is True
    assert path.is_file()
    assert path.read_bytes() == data

    # Re-store same data (deduplication)
    sha2, path2 = cas.store(data, extension="png")
    assert sha == sha2
    assert path == path2

    # Link to run folder
    run_dir = tmp_path / "run_output" / "images" / "domain.com"
    run_file = run_dir / f"{sha}.png"
    linked = cas.link_to_run(sha, run_file, extension="png")
    assert linked.is_file()
    assert linked.read_bytes() == data


def test_parquet_exporter_lifecycle(tmp_path):
    exporter = ParquetExporter(output_dir=tmp_path / "parquet_out", dataset_name="test_results")

    result = ScrapeResult(keyword="test")
    result.images.append(
        ImageItem(
            url="https://example.com/art.jpg",
            source_page="https://example.com/post/1",
            page_title="Sample Post",
            score=0.95,
            aesthetic_score=6.2,
            tags=["1girl", "solo", "digital_art"],
        )
    )
    result.videos.append(
        VideoItem(
            url="https://example.com/clip.mp4",
            source_page="https://example.com/video/1",
            type="direct",
            page_title="Video Clip",
            score=88,
        )
    )

    out_file = exporter.export(result)
    assert out_file.is_file()
    assert out_file.stat().st_size > 0
    # Extension should be either .parquet or .jsonl (fallback)
    assert out_file.suffix in (".parquet", ".jsonl")


def test_analytics_exporter_parquet(tmp_path):
    import sqlite3
    from storage.analytics_exporter import export_analytics

    db_path = tmp_path / "database.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE images (url TEXT, score REAL, width INT, height INT)")
        conn.execute("INSERT INTO images VALUES ('https://example.com/1.jpg', 0.9, 1024, 768)")
        conn.execute("CREATE TABLE videos (url TEXT, title TEXT)")
        conn.execute("INSERT INTO videos VALUES ('https://example.com/1.mp4', 'Test Video')")
        conn.commit()
    finally:
        conn.close()

    export_analytics(tmp_path, "parquet")
    # Should create images.parquet (or images_analytics.csv/analytics.json fallback)
    files = [f.name for f in tmp_path.iterdir()]
    assert any("parquet" in f or "json" in f for f in files)


def test_cas_run_directory_ingestion(tmp_path):
    from storage.cas_store import ContentAddressableStore

    cas = ContentAddressableStore(root_dir=tmp_path / "cas_root")
    output_root = tmp_path / "run_1"
    img_dir = output_root / "images" / "example.com"
    img_dir.mkdir(parents=True, exist_ok=True)

    test_file = img_dir / "test.jpg"
    test_file.write_bytes(b"sample-image-data-for-cas-ingestion")

    # Perform CAS ingestion logic as in engine.py
    for media_dir in [output_root / "images", output_root / "videos"]:
        if media_dir.exists():
            for orig_file in media_dir.rglob("*.*"):
                if orig_file.is_file() and orig_file.suffix != ".tmp":
                    data = orig_file.read_bytes()
                    ext = orig_file.suffix.lstrip(".") or "bin"
                    sha, _ = cas.store(data, extension=ext)
                    orig_file.unlink(missing_ok=True)
                    cas.link_to_run(sha, orig_file, extension=ext)

    assert test_file.is_file()
    assert test_file.read_bytes() == b"sample-image-data-for-cas-ingestion"
    assert cas.exists(cas.compute_hash(b"sample-image-data-for-cas-ingestion"), extension="jpg")


def test_cas_path_traversal_sanitization(tmp_path):
    import pytest

    cas = ContentAddressableStore(root_dir=tmp_path / "cas_root")
    # Malicious extension attempt with ../
    path = cas.get_cas_path("a1b2c3d4e5f60000000000000000000000000000000000000000000000000000", extension="../../evil.png")
    # Must be sanitized to alphanumeric and contained within root_dir
    assert "evilpng" in path.name
    assert str(path).startswith(str(tmp_path / "cas_root"))

    # Invalid short hash should raise ValueError
    with pytest.raises(ValueError):
        cas.get_cas_path("../")


def test_parquet_path_traversal_sanitization(tmp_path):
    exporter = ParquetExporter(output_dir=tmp_path / "parquet_out", dataset_name="../../malicious_dataset")
    assert ".." not in exporter.dataset_name
    result = ScrapeResult(keyword="test")
    out = exporter.export(result)
    assert str(out).startswith(str(tmp_path / "parquet_out"))




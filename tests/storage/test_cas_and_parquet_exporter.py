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

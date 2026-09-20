"""Unit tests for AsyncMLPipelineWorker verifying non-blocking aesthetic scoring, cropping, and tagging."""

from pathlib import Path
from PIL import Image
from core.models import ImageItem
from core.ml_worker import AsyncMLPipelineWorker


def test_async_ml_pipeline_worker_aesthetic_scoring_and_culling(tmp_path: Path):
    # Create sample image
    img_path = tmp_path / "sample.jpg"
    img = Image.new("RGB", (200, 200), color=(128, 64, 32))
    img.save(img_path)

    item = ImageItem(url="http://example.com/sample.jpg", source_page="http://example.com", file_path=str(img_path))

    # Test 1: lenient threshold -> image kept
    worker = AsyncMLPipelineWorker(min_aesthetic_score=1.0)
    worker.start()
    worker.enqueue(item, img_path)
    worker.join_and_finish(timeout=5.0)

    assert item.status == "pending"
    assert item.aesthetic_score is not None
    assert item.aesthetic_score >= 1.0
    assert img_path.exists()

    # Test 2: strict impossible threshold (10.0) -> image culled
    culled_items = []
    worker_strict = AsyncMLPipelineWorker(
        min_aesthetic_score=10.0,
        cull_rejected=True,
        on_item_culled=lambda itm, rsn: culled_items.append((itm, rsn)),
    )
    worker_strict.start()
    worker_strict.enqueue(item, img_path)
    worker_strict.join_and_finish(timeout=5.0)

    assert item.status == "rejected"
    assert "low_aesthetic_score" in item.failure_reason
    assert len(culled_items) == 1
    assert not img_path.exists()


def test_async_ml_pipeline_worker_auto_crop_and_tag(tmp_path: Path):
    img_path = tmp_path / "photo.png"
    img = Image.new("RGB", (300, 600), color=(200, 100, 50))
    img.save(img_path)

    item = ImageItem(url="http://example.com/photo.png", source_page="http://example.com", file_path=str(img_path))

    worker = AsyncMLPipelineWorker(auto_crop=True, auto_tag=True)
    worker.start()
    worker.enqueue(item, img_path)
    worker.join_and_finish(timeout=5.0)

    assert item.crop_box is not None
    assert item.crop_box["width"] > 0
    assert item.crop_box["height"] > 0

    # Sidecar .txt check
    sidecar = img_path.with_suffix(".txt")
    assert sidecar.exists()
    assert len(item.tags) > 0

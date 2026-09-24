"""Standalone integration smoke test suite executing all 10 previously dormant subsystems without mocks."""

from pathlib import Path
import sqlite3
from PIL import Image

from core.models import ImageItem, ScrapeResult, VideoItem


def _create_sample_image(path: Path) -> Path:
    img = Image.new("RGB", (256, 256), color=(120, 150, 200))
    img.save(path, format="JPEG")
    return path


def test_smoke_01_dataset_tagger(tmp_path):
    from ml.dataset_tagger import DatasetTagger

    sample_img = _create_sample_image(tmp_path / "test_tagger.jpg")
    tagger = DatasetTagger()
    tags = tagger.tag_image(sample_img)
    assert isinstance(tags, list)


def test_smoke_02_dataset_cropper(tmp_path):
    from ml.dataset_cropper import DatasetCropper

    sample_img = _create_sample_image(tmp_path / "test_crop.jpg")
    cropper = DatasetCropper(default_target_size=(128, 128))
    with Image.open(sample_img) as img:
        cropped = cropper.crop_image(img, target_size=(128, 128))
        assert cropped.size == (128, 128)
        out_p = tmp_path / "cropped.jpg"
        cropped.save(out_p)
        assert out_p.is_file()


def test_smoke_03_aesthetic_scorer(tmp_path):
    from ml.aesthetic_scorer import AestheticScorer

    sample_img = _create_sample_image(tmp_path / "test_aesthetic.jpg")
    scorer = AestheticScorer()
    score = scorer.score_image(sample_img)
    assert isinstance(score, float)
    assert 0.0 <= score <= 10.0


def test_smoke_04_rag_exporter(tmp_path):
    from ml.rag_exporter import RagExporter

    exporter = RagExporter(output_dir=tmp_path / "rag_out")
    entries = exporter.export_page(
        page_url="https://example.com/character-lore",
        page_title="Character Lore Profile",
        text_content="Genshin Impact features extensive regional story arcs and elemental combat mechanics.",
    )
    assert isinstance(entries, list)
    assert len(entries) > 0
    assert exporter.jsonl_path.is_file()
    assert exporter.jsonl_path.stat().st_size > 0


def test_smoke_05_database_exporter(tmp_path):
    from storage.database_exporter import DatabaseExporter

    db_file = tmp_path / "smoke_results.db"
    exporter = DatabaseExporter(db_path=db_file)

    res = ScrapeResult(keyword="smoke_test")
    res.images.append(
        ImageItem(
            url="https://example.com/asset.jpg",
            source_page="https://example.com/page1",
            page_title="Asset One",
            score=0.92,
            aesthetic_score=7.1,
            tags=["character", "art"],
        )
    )
    res.videos.append(
        VideoItem(
            url="https://example.com/video.mp4",
            source_page="https://example.com/page2",
            type="direct",
            page_title="Video Asset",
            score=85,
        )
    )

    exporter.export(res)
    assert db_file.is_file()

    conn = sqlite3.connect(db_file)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM images")
        img_count = cursor.fetchone()[0]
        assert img_count == 1

        cursor.execute("SELECT count(*) FROM videos")
        vid_count = cursor.fetchone()[0]
        assert vid_count == 1
    finally:
        conn.close()


def test_smoke_06_reddit_extractor():
    from plugins.reddit_extractor import RedditExtractor

    extractor = RedditExtractor()
    assert extractor.can_handle("https://www.reddit.com/r/EarthPorn/comments/abc123/mountains/") is True
    assert extractor.can_handle("https://example.com/page") is False


def test_smoke_07_twocaptcha_provider():
    from captcha.captcha_solvers.twocaptcha_provider import TwoCaptchaProvider

    # Instantiate provider without key - should be unconfigured but not crash
    provider = TwoCaptchaProvider(api_key=None)
    assert provider.is_available() is False


def test_smoke_08_anticaptcha_provider():
    from captcha.captcha_solvers.anticaptcha_provider import AntiCaptchaProvider

    provider = AntiCaptchaProvider(api_key=None)
    assert provider.is_available() is False


def test_smoke_09_free_audio_provider():
    from captcha.captcha_solvers.free_audio_provider import FreeAudioCaptchaProvider

    provider = FreeAudioCaptchaProvider()
    # Should safely check whisper/ffmpeg availability
    available = provider.is_available()
    assert isinstance(available, bool)


def test_smoke_10_hardware_governor():
    from monitoring.hardware_governor import HardwareLoadGovernor

    gov = HardwareLoadGovernor()
    metrics = gov.get_metrics()
    assert "cpu_percent" in metrics
    assert "ram_percent_available" in metrics
    assert "disk_percent_available" in metrics

    scale = gov.get_concurrency_scale_factor()
    assert isinstance(scale, float)
    assert 0.0 < scale <= 1.0

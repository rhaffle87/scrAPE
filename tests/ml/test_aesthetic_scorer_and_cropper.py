from __future__ import annotations

import io
from pathlib import Path
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from frontend.app import app, OUTPUT_DIR
from src.ml.aesthetic_scorer import AestheticScorer
from src.ml.dataset_cropper import DatasetCropper
from src.cli.main import build_parser


def test_aesthetic_scorer_basic(tmp_path: Path):
    # Create test image
    img = Image.new("RGB", (800, 600), color=(200, 100, 50))
    img_path = tmp_path / "test.jpg"
    img.save(img_path)

    scorer = AestheticScorer()
    score = scorer.score_image(img_path)

    assert isinstance(score, float)
    assert 1.0 <= score <= 10.0

    res = scorer.filter_directory(tmp_path, min_score=5.0)
    assert res["status"] == "ok"
    assert res["total_images"] == 1


def test_dataset_cropper_basic(tmp_path: Path):
    img = Image.new("RGB", (1920, 1080), color=(50, 150, 200))
    img_path = tmp_path / "portrait.png"
    img.save(img_path)

    cropper = DatasetCropper()
    cropped_img = cropper.crop_image(img, target_size=(1024, 1024))

    assert cropped_img.size == (1024, 1024)

    batch_res = cropper.crop_directory(tmp_path, target_size=(512, 512))
    assert batch_res["status"] == "ok"
    assert batch_res["cropped_count"] == 1


def test_cli_parser_aesthetic_and_crop_flags():
    parser = build_parser()
    args = parser.parse_args(["--keyword", "test", "--aesthetic-score", "6.5", "--auto-crop"])

    assert args.aesthetic_score == 6.5
    assert args.auto_crop is True


def test_api_dataset_score_and_crop_endpoints(tmp_path: Path, monkeypatch):
    client = TestClient(app)

    # Mock output directory structure using generic subject name
    subject_name = "sample_subject"
    subject_dir = OUTPUT_DIR / subject_name / "images"
    subject_dir.mkdir(parents=True, exist_ok=True)
    sample_img = Image.new("RGB", (1200, 800), color=(100, 200, 100))
    sample_img.save(subject_dir / "sample.jpg")

    monkeypatch.chdir(tmp_path)

    res_score = client.post("/api/dataset/score", data={"subject": subject_name, "min_score": "4.0"})
    assert res_score.status_code == 200
    data_score = res_score.json()
    assert data_score["status"] == "ok"
    assert data_score["total_images"] >= 1

    res_crop = client.post("/api/dataset/crop", data={"subject": subject_name, "width": "512", "height": "512"})
    assert res_crop.status_code == 200
    data_crop = res_crop.json()
    assert data_crop["status"] == "ok"
    assert data_crop["cropped_count"] >= 1

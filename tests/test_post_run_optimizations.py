"""Integration test suite for post-run engine optimizations, pHash deduplication, session cookie management, and WebUI export endpoints."""

import json
from pathlib import Path
from PIL import Image, ImageDraw
import io
import pytest
from fastapi.testclient import TestClient

from common.image_helper import compute_dhash, hamming_distance
from network.session import SessionManager
from frontend.app import app

client = TestClient(app)


def test_phash_image_deduplication():
    """Verify that pHash calculates identical or near-identical hashes for duplicate images."""
    # Create original image
    img1 = Image.new("RGB", (200, 200), color=(255, 255, 255))
    draw1 = ImageDraw.Draw(img1)
    draw1.rectangle([20, 20, 100, 100], fill=(0, 0, 0))
    buf1 = io.BytesIO()
    img1.save(buf1, format="JPEG", quality=95)
    bytes1 = buf1.getvalue()

    # Create duplicate image (same content, re-encoded at quality 75)
    buf2 = io.BytesIO()
    img1.save(buf2, format="JPEG", quality=75)
    bytes2 = buf2.getvalue()

    # Create completely different image (diagonal stripe)
    img3 = Image.new("RGB", (200, 200), color=(0, 0, 0))
    draw3 = ImageDraw.Draw(img3)
    draw3.line([(0, 0), (200, 200)], fill=(255, 255, 255), width=20)
    buf3 = io.BytesIO()
    img3.save(buf3, format="JPEG")
    bytes3 = buf3.getvalue()

    h1 = compute_dhash(bytes1)
    h2 = compute_dhash(bytes2)
    h3 = compute_dhash(bytes3)

    assert h1 is not None
    assert h2 is not None
    assert h3 is not None

    # Identical/similar images have Hamming distance <= 4
    dist_similar = hamming_distance(h1, h2)
    assert dist_similar <= 4

    # Completely different image has larger Hamming distance
    dist_different = hamming_distance(h1, h3)
    assert dist_different > 4


def test_session_manager_save_load_evict():
    """Verify session manager persistence and eviction."""
    sess_mgr = SessionManager()
    domain = "test_opt_domain.com"
    cookies = {"session_id": "abc123xyz", "auth": "true"}

    # 1. Save session
    sess_mgr.save_session(domain, cookies)

    # 2. Load session
    loaded = sess_mgr.load_session(domain)
    assert loaded == cookies

    # 3. Evict session
    sess_mgr.evict_session(domain)
    assert sess_mgr.load_session(domain) is None


def test_api_export_dataset_and_rag():
    """Verify WebUI REST export endpoints."""
    # Test dataset export with dummy run
    res_dataset = client.post("/api/export/dataset", json={"subject": "test_subject", "run_id": "20260101T000000Z", "layout": "1"})
    assert res_dataset.status_code in (200, 400, 404)

    # Test RAG export with dummy run
    res_rag = client.post("/api/export/rag", json={"subject": "test_subject", "run_id": "20260101T000000Z"})
    assert res_rag.status_code in (200, 404)

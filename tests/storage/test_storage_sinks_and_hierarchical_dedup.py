"""Unit tests for pluggable storage sinks and the 3-tier hierarchical deduplication engine."""

import io
import pytest
from pathlib import Path

from storage.storage_backend import LocalStorageSink, S3StorageSink, get_storage_sink
from storage.hierarchical_dedup import HierarchicalDedupEngine, hamming_distance, cosine_similarity


def test_local_storage_sink_atomic_and_path_safety(tmp_path: Path):
    sink = LocalStorageSink(tmp_path)

    # Save bytes
    test_data = b"hello world media content"
    saved_path = sink.save_bytes(test_data, "images/test1.txt")
    assert Path(saved_path).exists()
    assert Path(saved_path).read_bytes() == test_data
    assert sink.exists("images/test1.txt")

    # Save stream
    stream_data = io.BytesIO(b"streamed media data chunk")
    stream_path = sink.save_stream(stream_data, "media/stream.bin")
    assert Path(stream_path).exists()
    assert Path(stream_path).read_bytes() == b"streamed media data chunk"
    assert sink.exists("media/stream.bin")

    # Prevent path traversal
    with pytest.raises(ValueError, match="Path traversal detected"):
        sink._resolve_target("../../outside.txt")


def test_s3_storage_sink_spillover_resilience(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SCRAPE_ALLOW_LOCAL_S3_ENDPOINT", "true")
    spillover_dir = tmp_path / "spillover"
    # Provide dummy S3 config without network; should initialize and spillover locally
    sink = S3StorageSink(
        bucket_name="test-bucket",
        prefix="scrapes",
        spillover_dir=spillover_dir,
        endpoint_url="http://127.0.0.1:59998",
        aws_access_key_id="mock-key",
        aws_secret_access_key="mock-secret",
    )
    try:
        test_bytes = b"image content for s3"
        out_uri = sink.save_bytes(test_bytes, "apple/img1.jpg")
        assert Path(out_uri).exists()
        assert Path(out_uri).read_bytes() == test_bytes
    finally:
        sink.close()


def test_storage_sink_factory(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SCRAPE_ALLOW_LOCAL_S3_ENDPOINT", "true")
    local_sink = get_storage_sink("local", root_dir=tmp_path)
    assert isinstance(local_sink, LocalStorageSink)

    s3_sink = get_storage_sink(
        "s3",
        s3_bucket="my-bucket",
        root_dir=tmp_path,
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id="mock-key",
        aws_secret_access_key="mock-secret",
    )
    try:
        assert isinstance(s3_sink, S3StorageSink)
    finally:
        if hasattr(s3_sink, "close"):
            s3_sink.close()


def test_hierarchical_dedup_engine_l1_sha256():
    engine = HierarchicalDedupEngine()
    sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    is_dup, reason, _ = engine.check_duplicate(sha256=sha)
    assert not is_dup

    engine.record_asset(sha256=sha)

    is_dup, reason, matched = engine.check_duplicate(sha256=sha)
    assert is_dup
    assert reason == "exact_sha256_match"
    assert matched == sha


def test_hierarchical_dedup_engine_l2_bktree_phash():
    engine = HierarchicalDedupEngine(hamming_threshold=4)
    hash_base = 0b1111000011110000111100001111000011110000111100001111000011110000

    engine.record_asset(sha256="dummy_sha_1", phash=hash_base, identifier="asset_base")

    # Near duplicate with Hamming distance 2 (2 bits flipped)
    near_dup_hash = hash_base ^ 0b11
    assert hamming_distance(hash_base, near_dup_hash) == 2

    is_dup, reason, matched = engine.check_duplicate(phash=near_dup_hash)
    assert is_dup
    assert "phash_hamming_distance_2" in reason
    assert matched == "asset_base"

    # Distant hash with Hamming distance 10
    distant_hash = hash_base ^ 0b1111111111
    assert hamming_distance(hash_base, distant_hash) == 10

    is_dup, _, _ = engine.check_duplicate(phash=distant_hash)
    assert not is_dup


def test_hierarchical_dedup_engine_l3_vector_similarity():
    engine = HierarchicalDedupEngine(similarity_threshold=0.95)
    v1 = [1.0, 0.0, 0.5, 0.2]
    # v2 is almost identical to v1
    v2 = [0.99, 0.01, 0.49, 0.21]
    # v3 is orthogonal
    v3 = [0.0, 1.0, 0.0, 0.0]

    engine.record_asset(sha256="vec_sha_1", embedding=v1, identifier="vec_asset_1")

    # Check v2 (high cosine similarity)
    is_dup, reason, matched = engine.check_duplicate(embedding=v2)
    assert is_dup
    assert "vector_cosine_similarity" in reason
    assert matched == "vec_asset_1"

    # Check v3 (low similarity)
    is_dup, _, _ = engine.check_duplicate(embedding=v3)
    assert not is_dup

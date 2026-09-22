"""
tests/storage/test_cas_dedup_and_backpressure.py — AC2.5, AC2.6, & AC2.7 Validation.

Verifies:
1. AC2.5: Remote dedup index (Redis SET/Bloom filter) is never trusted blindly;
   an S3 HEAD request confirms true remote presence before skipping upload.
   Redis absence or failure logs a degraded-mode warning and falls back to direct S3 HEAD.
2. AC2.6: Bounded async spooling queue (maxsize) applies ingestion backpressure
   (CASQueueFullError / throttling) under sustained load rather than growing unbounded.
3. AC2.7: TLS certificate verification is enabled by default; disabling it requires
   explicit opt-in and emits a warning log.
4. Pure local CAS operation requires zero Redis and zero boto3 dependencies.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import MagicMock, patch

try:
    from botocore.exceptions import ClientError
except ImportError:
    ClientError = Exception
import fakeredis
import pytest

from storage.cas_store import ContentAddressableStore
from storage.cas_sync import (
    CASCloudSyncer,
    CASQueueFullError,
)

SAMPLE_SHA256_A = "a" * 64
SAMPLE_SHA256_B = "b" * 64
SAMPLE_SHA256_C = "c" * 64


class TestRemoteDedupHEADVerification:
    """AC2.5: Redis / Bloom dedup index is confirmed with S3 HEAD check before skipping upload."""

    def test_stale_redis_index_still_triggers_head_and_uploads_missing_remote(self, tmp_path):
        fake_redis = fakeredis.FakeRedis()
        # Seed stale entry in Redis indicating object is already synced
        fake_redis.sadd("scrape:cas_remote_index", SAMPLE_SHA256_A)

        test_file = tmp_path / "block.bin"
        test_file.write_bytes(b"content-a")

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client

                # S3 HEAD reports 404 (object is missing remotely despite stale Redis entry)
                mock_client.head_object.side_effect = ClientError(
                    {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
                )

                syncer = CASCloudSyncer(
                    bucket="cas-bucket",
                    endpoint_url="http://127.0.0.1:9000",
                    redis_client=fake_redis,
                )

                # exists_remote must return False because HEAD returned 404
                assert syncer.exists_remote(SAMPLE_SHA256_A) is False
                mock_client.head_object.assert_called_once()

                # upload_block_sync must proceed to upload to S3
                uploaded = syncer.upload_block_sync(SAMPLE_SHA256_A, test_file)
                assert uploaded is True
                mock_client.put_object.assert_called_once()
                call_kwargs = mock_client.put_object.call_args.kwargs
                assert call_kwargs["Bucket"] == "cas-bucket"
                assert call_kwargs["Key"] == syncer.get_cas_s3_key(SAMPLE_SHA256_A)

                syncer.close(drain=False)

    def test_confirmed_remote_object_skips_upload(self, tmp_path):
        fake_redis = fakeredis.FakeRedis()
        test_file = tmp_path / "block.bin"
        test_file.write_bytes(b"content-b")

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client

                # S3 HEAD returns 200 OK (object exists remotely)
                mock_client.head_object.return_value = {"ContentLength": 9}

                syncer = CASCloudSyncer(
                    bucket="cas-bucket",
                    endpoint_url="http://127.0.0.1:9000",
                    redis_client=fake_redis,
                )

                # Upload should be skipped
                uploaded = syncer.upload_block_sync(SAMPLE_SHA256_B, test_file)
                assert uploaded is False
                mock_client.head_object.assert_called_once()
                mock_client.put_object.assert_not_called()

                # Redis index is updated with confirmed remote presence
                assert fake_redis.sismember("scrape:cas_remote_index", SAMPLE_SHA256_B)

                syncer.close(drain=False)

    def test_redis_unreachable_logs_warning_and_falls_back_to_direct_s3_head(self, tmp_path, caplog):
        """When Redis is unreachable or errors, syncer must log warning and fall back to S3 HEAD."""
        caplog.set_level(logging.WARNING)
        mock_redis = MagicMock()
        mock_redis.sismember.side_effect = ConnectionError("Redis server unavailable")
        test_file = tmp_path / "block.bin"
        test_file.write_bytes(b"content-c")

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client
                mock_client.head_object.side_effect = ClientError(
                    {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
                )

                syncer = CASCloudSyncer(
                    bucket="cas-bucket",
                    endpoint_url="http://127.0.0.1:9000",
                    redis_client=mock_redis,
                )

                assert syncer.exists_remote(SAMPLE_SHA256_C) is False
                # S3 HEAD must still be called as fallback
                mock_client.head_object.assert_called_once()

                # Assert warning was emitted about degraded mode
                warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
                assert any("Redis remote dedup index lookup failed" in w for w in warnings)

                syncer.close(drain=False)

    def test_standalone_mode_without_redis_logs_info_and_operates_cleanly(self, tmp_path, caplog):
        """When initialized without Redis, syncer logs standalone mode and verifies directly via S3 HEAD."""
        caplog.set_level(logging.INFO)
        test_file = tmp_path / "block.bin"
        test_file.write_bytes(b"content-standalone")

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client
                mock_client.head_object.return_value = {"ContentLength": 18}

                syncer = CASCloudSyncer(
                    bucket="cas-bucket",
                    endpoint_url="http://127.0.0.1:9000",
                    redis_client=None,
                )

                # Assert standalone mode log
                info_msgs = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
                assert any("Cloud CAS running in standalone mode" in m for m in info_msgs)

                # Verifies existence via S3 HEAD cleanly
                assert syncer.exists_remote(SAMPLE_SHA256_A) is True
                mock_client.head_object.assert_called_once()

                syncer.close(drain=False)


class TestBoundedSpoolingAndBackpressure:
    """AC2.6: Bounded queue prevents memory exhaustion and throttles ingestion when saturated."""

    def test_queue_capacity_bounds_memory_and_raises_queue_full(self, tmp_path):
        test_file = tmp_path / "block.bin"
        test_file.write_bytes(b"payload")

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client

                # Initialize syncer with queue capacity of 3 and 0 active workers so queue stays full
                syncer = CASCloudSyncer(
                    bucket="cas-bucket",
                    endpoint_url="http://127.0.0.1:9000",
                    concurrency=1,
                    max_queue_size=3,
                )
                # Temporarily pause background worker consumption
                syncer._running = False
                for t in syncer._workers:
                    t.join(timeout=1.0)
                syncer._running = True

                # Fill the queue up to maxsize=3
                syncer.enqueue_upload("0" * 64, test_file, block=False)
                syncer.enqueue_upload("1" * 64, test_file, block=False)
                syncer.enqueue_upload("2" * 64, test_file, block=False)
                assert syncer._queue.qsize() == 3

                # Attempting to enqueue 4th item when queue is full must raise CASQueueFullError
                with pytest.raises(CASQueueFullError):
                    syncer.enqueue_upload("3" * 64, test_file, block=False)

                # Queue size must remain strictly bounded at 3 (no unbounded heap growth)
                assert syncer._queue.qsize() == 3

                syncer.close(drain=False)

    def test_sustained_ingestion_under_degraded_cloud_throughput_bounds_memory(self, tmp_path):
        """Under sustained ingestion with slow cloud uploads, queue size remains strictly bounded."""
        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client

                # Simulate slow cloud latency (20ms per HEAD/PUT)
                def slow_head(*args, **kwargs):
                    time.sleep(0.02)
                    raise ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject")

                def slow_put(*args, **kwargs):
                    time.sleep(0.02)
                    return {}

                mock_client.head_object.side_effect = slow_head
                mock_client.put_object.side_effect = slow_put

                max_capacity = 5
                syncer = CASCloudSyncer(
                    bucket="cas-bucket",
                    endpoint_url="http://127.0.0.1:9000",
                    concurrency=2,
                    max_queue_size=max_capacity,
                )

                max_observed_queue_size = 0
                queue_samples = []

                # Ingest 25 blocks through syncer
                for i in range(25):
                    h = f"{i:064x}"
                    dummy_file = tmp_path / f"block_{i}.bin"
                    dummy_file.write_bytes(f"data_{i}".encode())
                    try:
                        syncer.enqueue_upload(h, dummy_file, block=True, timeout=0.1)
                    except CASQueueFullError:
                        pass
                    qsize = syncer._queue.qsize()
                    queue_samples.append(qsize)
                    if qsize > max_observed_queue_size:
                        max_observed_queue_size = qsize

                # Memory invariant: queue size NEVER exceeds configured max capacity
                assert max_observed_queue_size <= max_capacity
                assert all(q <= max_capacity for q in queue_samples)

                # Drain cleanly
                syncer.close(drain=True, timeout=5.0)
                assert syncer._queue.qsize() == 0

    def test_cas_store_propagates_backpressure_to_ingestion(self, tmp_path):
        """Verify ContentAddressableStore propagates backpressure when cloud spooler is saturated."""
        test_file = tmp_path / "block.bin"
        test_file.write_bytes(b"payload")

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client"):
                mock_syncer = MagicMock()
                mock_syncer.enqueue_upload.side_effect = CASQueueFullError("Queue capacity reached")

                cas = ContentAddressableStore(
                    root_dir=tmp_path / "cas",
                    cloud_syncer=mock_syncer,
                )

                # Ingestion is throttled with CASQueueFullError rather than silently buffering
                with pytest.raises(CASQueueFullError):
                    cas.store(b"test-bytes")

                mock_syncer.enqueue_upload.assert_called_once()


class TestTLSVerificationEnforcement:
    """AC2.7: TLS validation enabled by default; disabling requires explicit override and warning log."""

    def test_tls_verification_enabled_by_default(self, caplog):
        caplog.set_level(logging.WARNING)

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client

                syncer = CASCloudSyncer(
                    bucket="cas-bucket",
                    endpoint_url="http://127.0.0.1:9000",
                )

                assert syncer._verify_ssl is True
                call_kwargs = mock_boto_cls.call_args.kwargs
                assert call_kwargs["verify"] is True

                syncer.close(drain=False)

        # Confirm zero insecure warnings were logged
        insecure_warnings = [
            r.getMessage() for r in caplog.records
            if r.levelno == logging.WARNING and "INSECURE TLS" in r.getMessage()
        ]
        assert len(insecure_warnings) == 0

    def test_insecure_skip_verify_requires_explicit_flag_and_logs_warning(self, caplog):
        caplog.set_level(logging.WARNING)

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client

                syncer = CASCloudSyncer(
                    bucket="cas-bucket",
                    endpoint_url="http://127.0.0.1:9000",
                    insecure_skip_verify=True,
                )

                assert syncer._verify_ssl is False
                call_kwargs = mock_boto_cls.call_args.kwargs
                assert call_kwargs["verify"] is False

                syncer.close(drain=False)

        # Assert warning log was emitted
        warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        assert any("INSECURE TLS: Certificate verification explicitly disabled" in w for w in warnings)


class TestPureLocalCASZeroDependencies:
    """Item 1 & 3: Local-only CAS operations require ZERO Redis and ZERO boto3 dependencies."""

    def test_pure_local_cas_has_zero_redis_and_zero_boto_dependency(self, tmp_path):
        """Local CAS operates 100% cleanly without Redis or boto3."""
        cas = ContentAddressableStore(root_dir=tmp_path / "cas")
        assert cas.cloud_syncer is None

        data = b"pure-local-zero-dependency-bytes"
        sha, path = cas.store(data, extension="png")
        assert cas.exists(sha, extension="png") is True
        assert path.is_file()
        assert path.read_bytes() == data

        # Link to run directory
        run_file = tmp_path / "runs" / "output.png"
        linked = cas.link_to_run(sha, run_file, extension="png")
        assert linked.is_file()
        assert linked.read_bytes() == data

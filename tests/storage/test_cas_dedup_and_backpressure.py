"""
tests/storage/test_cas_dedup_and_backpressure.py — AC2.5, AC2.6, & AC2.7 Validation.

Verifies:
1. AC2.5: Remote dedup index (Redis SET/Bloom filter) is never trusted blindly;
   an S3 HEAD request confirms true remote presence before skipping upload.
2. AC2.6: Bounded async spooling queue (maxsize) applies ingestion backpressure
   (CASQueueFullError / throttling) under throughput degradation rather than OOMing.
3. AC2.7: TLS certificate verification is enabled by default; disabling it requires
   explicit opt-in and emits a warning log.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
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


class TestBoundedSpoolingAndBackpressure:
    """AC2.6: Bounded queue prevents memory exhaustion and throttles ingestion when saturated."""

    def test_queue_capacity_bounds_memory_and_raises_queue_full(self, tmp_path):
        test_file = tmp_path / "block.bin"
        test_file.write_bytes(b"payload")

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client

                # Initialize syncer with queue capacity of 3 and 0 workers so queue stays full
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

    def test_tls_verification_enabled_by_default(self):
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

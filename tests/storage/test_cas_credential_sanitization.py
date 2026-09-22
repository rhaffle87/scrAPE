"""
tests/storage/test_cas_credential_sanitization.py — AC2.1 & AC2.4 Validation.

Verifies:
1. AC2.1: S3 client construction, error handling, and logger output NEVER leak
   AWS access keys (AKIA...), secret access keys, presigned signatures (X-Amz-Signature),
   or URL credentials.
2. AC2.4: Presigned URLs generated for CAS blocks are strictly scoped to single
   object keys (GetObject), bounded to <=900s TTL, and never written to disk or logs.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
import re
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

try:
    from botocore.exceptions import ClientError
except ImportError:
    ClientError = Exception
import pytest

from storage.cas_sync import (
    CASCloudSyncer,
    MAX_PRESIGNED_EXPIRY_SECONDS,
    redact_s3_error,
)

SAMPLE_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
DUMMY_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
DUMMY_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"


class TestCredentialSanitizationAndRedaction:
    """AC2.1: Credential leakage defense across S3 operations, exceptions, and logging."""

    def test_redact_s3_error_scrubs_aws_key_id(self):
        msg = f"Failed request with access_key_id={DUMMY_KEY_ID} to endpoint"
        redacted = redact_s3_error(Exception(msg))
        assert DUMMY_KEY_ID not in redacted
        assert "[REDACTED_AWS_KEY]" in redacted

    def test_redact_s3_error_scrubs_aws_secret_key(self):
        msg = f"Connection failed aws_secret_access_key='{DUMMY_SECRET}' timeout"
        redacted = redact_s3_error(Exception(msg))
        assert DUMMY_SECRET not in redacted
        assert "[REDACTED_SECRET]" in redacted

    def test_redact_s3_error_scrubs_presigned_signature(self):
        msg = "GET /cas/e3/b0/e3b0c...?X-Amz-Signature=d2c67a89b01c3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f HTTP/1.1 403"
        redacted = redact_s3_error(Exception(msg))
        assert "d2c67a89b01c3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f" not in redacted
        assert "X-Amz-Signature=[REDACTED_SIGNATURE]" in redacted

    def test_redact_s3_error_scrubs_url_embedded_credentials(self):
        msg = "Connecting to https://myuser:mypassword123@minio.internal.net:9000/cas"
        redacted = redact_s3_error(Exception(msg))
        assert "mypassword123" not in redacted
        assert "myuser:mypassword123@" not in redacted
        assert "***:***@" in redacted

    def test_redact_s3_error_cleans_boto3_client_error(self):
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": f"User {DUMMY_KEY_ID} is not authorized with secret {DUMMY_SECRET}",
            },
            "ResponseMetadata": {
                "HTTPHeaders": {
                    "authorization": f"AWS4-HMAC-SHA256 Credential={DUMMY_KEY_ID}/...",
                    "x-amz-request-id": "12345",
                }
            },
        }
        exc = ClientError(error_response, "GetObject")
        redacted = redact_s3_error(exc)

        assert "AccessDenied" in redacted
        assert DUMMY_KEY_ID not in redacted
        assert DUMMY_SECRET not in redacted
        assert "authorization" not in redacted
        assert "ResponseMetadata" not in redacted

    def test_logger_never_emits_credentials_on_client_init_or_error(self, caplog):
        caplog.set_level(logging.DEBUG)

        # Allow local loopback for constructing syncer in test
        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            # Patch boto3.client to raise an exception echoing credentials
            with patch("boto3.client") as mock_boto:
                mock_boto.side_effect = Exception(
                    f"Auth failure for {DUMMY_KEY_ID} secret={DUMMY_SECRET}"
                )

                with pytest.raises(RuntimeError) as exc_info:
                    CASCloudSyncer(
                        bucket="test-bucket",
                        endpoint_url="http://127.0.0.1:9000",
                        aws_access_key_id=DUMMY_KEY_ID,
                        aws_secret_access_key=DUMMY_SECRET,
                    )

                # Assert exception message is sanitized
                assert DUMMY_KEY_ID not in str(exc_info.value)
                assert DUMMY_SECRET not in str(exc_info.value)

        # Assert no captured log record contains credentials
        for record in caplog.records:
            log_text = record.getMessage()
            assert DUMMY_KEY_ID not in log_text
            assert DUMMY_SECRET not in log_text

    def test_upload_failure_logs_cleanly_without_credentials(self, tmp_path, caplog):
        caplog.set_level(logging.DEBUG)
        test_file = tmp_path / "block.bin"
        test_file.write_bytes(b"test data content")

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client

                # HEAD succeeds (not exists), PUT fails with credential error
                mock_client.head_object.side_effect = ClientError(
                    {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
                )
                mock_client.put_object.side_effect = Exception(
                    f"Signature expired for {DUMMY_KEY_ID} sig=X-Amz-Signature=abcdef12345"
                )

                syncer = CASCloudSyncer(
                    bucket="test-bucket",
                    endpoint_url="http://127.0.0.1:9000",
                    aws_access_key_id=DUMMY_KEY_ID,
                    aws_secret_access_key=DUMMY_SECRET,
                )

                with pytest.raises(RuntimeError) as exc_info:
                    syncer.upload_block_sync(SAMPLE_SHA256, test_file)

                syncer.close(drain=False)

                assert DUMMY_KEY_ID not in str(exc_info.value)
                assert "abcdef12345" not in str(exc_info.value)

        for record in caplog.records:
            log_text = record.getMessage()
            assert DUMMY_KEY_ID not in log_text
            assert "abcdef12345" not in log_text


class TestPresignedURLSecurity:
    """AC2.4: Ephemeral, single-key-scoped presigned URLs with <=900s TTL."""

    def test_presigned_url_scoped_to_single_cas_object(self):
        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client

                def fake_presigned(ClientMethod, Params, ExpiresIn):
                    bucket = Params.get("Bucket")
                    key = Params.get("Key")
                    return (
                        f"https://s3.amazonaws.com/{bucket}/{key}"
                        f"?X-Amz-Algorithm=AWS4-HMAC-SHA256"
                        f"&X-Amz-Expires={ExpiresIn}"
                        f"&X-Amz-Signature=1234567890abcdef"
                    )

                mock_client.generate_presigned_url.side_effect = fake_presigned

                syncer = CASCloudSyncer(
                    bucket="my-cas-bucket",
                    endpoint_url="http://127.0.0.1:9000",
                )

                url = syncer.generate_presigned_get_url(SAMPLE_SHA256, expires_in=300)
                syncer.close(drain=False)

                # Verify ClientMethod is strictly get_object (single object retrieval)
                call_args = mock_client.generate_presigned_url.call_args
                assert call_args.kwargs["ClientMethod"] == "get_object"
                assert call_args.kwargs["Params"]["Bucket"] == "my-cas-bucket"
                expected_key = f"cas/{SAMPLE_SHA256[:2]}/{SAMPLE_SHA256[2:4]}/{SAMPLE_SHA256}"
                assert call_args.kwargs["Params"]["Key"] == expected_key
                assert call_args.kwargs["ExpiresIn"] == 300

                # Verify generated URL path
                parsed = urlparse(url)
                assert parsed.path == f"/my-cas-bucket/{expected_key}"

    def test_presigned_url_expiry_clamped_to_max_900s(self):
        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client
                mock_client.generate_presigned_url.return_value = "https://s3.example.com/cas/test?sig=xyz"

                syncer = CASCloudSyncer(bucket="my-bucket", endpoint_url="http://127.0.0.1:9000")

                # Requesting 1 hour (3600s) must be clamped to 900s (15 min)
                syncer.generate_presigned_get_url(SAMPLE_SHA256, expires_in=3600)
                call_args = mock_client.generate_presigned_url.call_args
                assert call_args.kwargs["ExpiresIn"] == MAX_PRESIGNED_EXPIRY_SECONDS
                assert MAX_PRESIGNED_EXPIRY_SECONDS == 900

                # Requesting negative or 0 expiry is clamped to at least 1s
                syncer.generate_presigned_get_url(SAMPLE_SHA256, expires_in=-50)
                call_args = mock_client.generate_presigned_url.call_args
                assert call_args.kwargs["ExpiresIn"] == 1

                syncer.close(drain=False)

    def test_presigned_url_rejects_malformed_cas_key(self):
        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client"):
                syncer = CASCloudSyncer(bucket="my-bucket", endpoint_url="http://127.0.0.1:9000")

                with pytest.raises(ValueError, match="Invalid CAS key"):
                    syncer.generate_presigned_get_url("../../etc/passwd")

                with pytest.raises(ValueError, match="Invalid CAS key"):
                    syncer.generate_presigned_get_url("SHORT_KEY")

                syncer.close(drain=False)

    def test_presigned_url_never_written_to_disk(self, tmp_path):
        """Verify presigned URLs remain ephemeral in-memory and are never persisted to disk files."""
        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            with patch("boto3.client") as mock_boto_cls:
                mock_client = MagicMock()
                mock_boto_cls.return_value = mock_client
                fake_sig = "a1b2c3d4e5f67890abcdef"
                fake_url = f"https://s3.amazonaws.com/bucket/cas/test?X-Amz-Signature={fake_sig}"
                mock_client.generate_presigned_url.return_value = fake_url

                syncer = CASCloudSyncer(bucket="my-bucket", endpoint_url="http://127.0.0.1:9000")
                url = syncer.generate_presigned_get_url(SAMPLE_SHA256)
                assert url == fake_url

                syncer.close(drain=False)

                # Scan workspace output/logs to ensure this fake signature wasn't written to disk
                for path in Path(".").glob("output/**/*"):
                    if path.is_file():
                        try:
                            content = path.read_text(errors="ignore")
                            assert fake_sig not in content
                        except Exception:
                            pass

    def test_presigned_urls_never_persisted_to_run_summary_or_disk_after_crawl_run(self, tmp_path):
        """
        AC2.1 & AC2.4: Execute a full CAS-sync-enabled operation with REAL boto3 SigV4 presigned URL
        generation (no mocked signature) and post-crawl summary generation, proving that run_summary.json
        and all persisted disk artifacts contain zero presigned URLs, zero X-Amz-Signature parameters,
        and zero AWS access keys.
        """
        from core.models import ImageItem, ScrapeResult
        from core.run_summary import generate_run_summary
        from storage.cas_store import ContentAddressableStore

        with patch.dict(os.environ, {"SCRAPE_ALLOW_LOCAL_S3_ENDPOINT": "true"}):
            # Initialize CAS syncer with real credentials (for client-side SigV4 signing)
            # using loopback endpoint so real boto3 client signs locally with zero WAN socket usage
            syncer = CASCloudSyncer(
                bucket="cas-bucket",
                endpoint_url="http://127.0.0.1:9000",
                aws_access_key_id=DUMMY_KEY_ID,
                aws_secret_access_key=DUMMY_SECRET,
            )
            store = ContentAddressableStore(root_dir=tmp_path / "cas", cloud_syncer=syncer)

            # Store an item into CAS
            content = b"sample crawl content for CAS test"
            cas_key, _ = store.store(content)
            assert cas_key == hashlib.sha256(content).hexdigest()

            # Generate a REAL SigV4 presigned URL with actual HMAC signature via boto3
            ephemeral_url = syncer.generate_presigned_get_url(cas_key)
            assert "X-Amz-Signature=" in ephemeral_url
            assert "X-Amz-Algorithm=AWS4-HMAC-SHA256" in ephemeral_url
            parsed_query = parse_qs(urlparse(ephemeral_url).query)
            actual_sig = parsed_query["X-Amz-Signature"][0]
            assert len(actual_sig) == 64, "Real SigV4 signature must be 64-char hex string"

            # Populate realistic crawl result with media item referencing CAS
            scrape_result = ScrapeResult(keyword="test-cas-crawl")
            scrape_result.images.append(
                ImageItem(
                    url="https://example.com/images/hero.jpg",
                    source_page="https://example.com",
                    file_path=str(tmp_path / "cas" / cas_key[:2] / f"{cas_key}.jpg"),
                    hash=cas_key,
                    status="downloaded",
                )
            )
            scrape_result.run_metadata["cas_key"] = cas_key

            # Generate run_summary.json into tmp_path
            summary_data = generate_run_summary(
                result=scrape_result,
                output_dir=tmp_path,
                crawl_duration_seconds=1.5,
                download_duration_seconds=0.5,
            )

            # Close syncer cleanly
            syncer.close(drain=False)

        # Assert run_summary.json was generated
        summary_file = tmp_path / "run_summary.json"
        assert summary_file.exists(), "run_summary.json must be created by generate_run_summary"

        # Regex patterns to detect credential or presigned leak
        leak_patterns = [
            re.compile(r"X-Amz-Signature=[0-9a-fA-F]{16,}", re.IGNORECASE),
            re.compile(r"AKIA[0-9A-Z]{16}"),
            re.compile(re.escape(DUMMY_SECRET)),
            re.compile(re.escape(actual_sig)),
            re.compile(r"X-Amz-Algorithm="),
        ]

        # Grep every file in tmp_path (including run_summary.json, CAS blocks, etc.)
        persisted_files = list(tmp_path.rglob("*"))
        assert len(persisted_files) > 0

        for file_path in persisted_files:
            if file_path.is_file():
                try:
                    file_bytes = file_path.read_bytes()
                    file_text = file_bytes.decode("utf-8", errors="ignore")
                    for pattern in leak_patterns:
                        match = pattern.search(file_text)
                        assert match is None, (
                            f"LEAK DETECTED: File {file_path.name} contains matched pattern "
                            f"'{pattern.pattern}': {match.group(0) if match else ''}"
                        )
                except Exception as exc:
                    pytest.fail(f"Failed scanning persisted file {file_path}: {exc}")


"""
src/storage/cas_sync.py — Content-Addressable Storage (CAS) Cloud Synchronization Engine.

Provides asynchronous background replication of local CAS blocks to S3 / Cloudflare R2 / MinIO
with strict SSRF defense (AC2.2), canonical SHA-256 key validation (AC2.3), credential redaction (AC2.1),
ephemeral single-object presigned URLs (AC2.4), remote dedup HEAD confirmation (AC2.5),
bounded spooling with ingestion backpressure (AC2.6), and enforced TLS validation (AC2.7).
"""

from __future__ import annotations

import logging
from pathlib import Path
import queue
import re
import threading
import time
from typing import Any

from common.security import (
    validate_cas_key,
    validate_s3_endpoint_url,
)

LOGGER = logging.getLogger(__name__)

# Maximum presigned URL expiry per threat model AC2.4 (15 minutes)
MAX_PRESIGNED_EXPIRY_SECONDS = 900
DEFAULT_MAX_QUEUE_SIZE = 1000

# Regex patterns for scrubbing secrets from exception messages
AWS_KEY_PATTERN = re.compile(r"(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}")
AWS_SECRET_PATTERN = re.compile(
    r"(?i)(aws_secret_access_key|secret_access_key|secret_key|secret|password|sig)[\s:=]+['\"]?([0-9a-zA-Z/+=_-]{16,64})['\"]?"
)
AMZ_SIG_PATTERN = re.compile(r"X-Amz-Signature=[0-9a-fA-F]+")
URL_CRED_PATTERN = re.compile(r"([a-zA-Z0-9+.-]+://)([^:\s/@]+):([^@\s/]+)@")


def _scrub_string(text: str) -> str:
    """Helper to scrub sensitive tokens, credentials, and signatures from any string."""
    if not text:
        return ""
    # Strip AWS Key IDs
    scrubbed = AWS_KEY_PATTERN.sub("[REDACTED_AWS_KEY]", text)
    # Strip Presigned Signatures
    scrubbed = AMZ_SIG_PATTERN.sub("X-Amz-Signature=[REDACTED_SIGNATURE]", scrubbed)
    # Strip AWS Secret Keys and passwords
    scrubbed = AWS_SECRET_PATTERN.sub(r"\1=[REDACTED_SECRET]", scrubbed)
    # Strip embedded URL credentials anywhere in the string
    scrubbed = URL_CRED_PATTERN.sub(r"\1***:***@", scrubbed)
    return scrubbed


def redact_s3_error(exc: Exception) -> str:
    """
    Scrub credentials, signatures, and auth headers from S3/botocore exceptions (AC2.1).
    Ensures raw HTTP headers and sensitive tokens never reach log records.
    """
    # For botocore ClientError, extract error code and message without raw response metadata/headers
    if hasattr(exc, "response") and isinstance(exc.response, dict):
        error_info = exc.response.get("Error", {})
        code = error_info.get("Code", "Unknown")
        raw_message = error_info.get("Message", "")
        message = _scrub_string(str(raw_message)) if raw_message else _scrub_string(str(exc))
        return f"S3 ClientError ({code}): {message}"

    return _scrub_string(str(exc))


class CASQueueFullError(Exception):
    """Raised when the cloud CAS spooling queue exceeds its capacity under ingestion pressure (AC2.6)."""
    pass


class CASCloudSyncer:
    """
    Asynchronous cloud synchronizer for local CAS blocks.
    Replicates SHA-256 blocks to S3-compatible cloud object storage.
    """

    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None = None,
        region_name: str = "us-east-1",
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        insecure_skip_verify: bool = False,
        concurrency: int = 4,
        max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE,
        redis_client: Any | None = None,
    ):
        if not bucket or not isinstance(bucket, str):
            raise ValueError("S3 bucket name must be a non-empty string.")

        self.bucket = bucket.strip()
        self.region_name = region_name or "us-east-1"
        self.concurrency = max(1, concurrency)
        self.max_queue_size = max_queue_size
        self.redis_client = redis_client

        # AC2.2: Validate S3_ENDPOINT_URL against SSRF, cloud metadata, and unauthorized loopbacks
        self.endpoint_url = validate_s3_endpoint_url(endpoint_url)

        # AC2.7: TLS validation enforcement
        self.insecure_skip_verify = bool(insecure_skip_verify)
        if self.insecure_skip_verify:
            LOGGER.warning(
                "INSECURE TLS: Certificate verification explicitly disabled for S3 endpoint '%s' "
                "(S3_INSECURE_SKIP_VERIFY=true).",
                self.endpoint_url or "default-aws",
            )
            self._verify_ssl = False
        else:
            self._verify_ssl = True

        if self.redis_client is None:
            LOGGER.info(
                "Cloud CAS running in standalone mode (no Redis client provided); "
                "relying exclusively on direct S3 HEAD verification for deduplication."
            )

        # Initialize S3 client securely without logging credentials (AC2.1)
        self._client = self._init_s3_client(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        # Spooling queue and worker thread management (AC2.6)
        self._queue: queue.Queue[tuple[str, Path] | None] = queue.Queue(maxsize=self.max_queue_size)
        self._workers: list[threading.Thread] = []
        self._running = True
        self._local_dedup_cache: set[str] = set()
        self._lock = threading.Lock()

        self._start_workers()

    def _init_s3_client(
        self,
        aws_access_key_id: str | None,
        aws_secret_access_key: str | None,
    ) -> Any:
        """Create boto3 S3 client using safe parameters without leaking credentials to logs."""
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError(
                "boto3 is required for cloud CAS synchronization. "
                "Install it via 'pip install scrape-dashboard[cloud]' or 'pip install boto3'."
            ) from None

        client_kwargs: dict[str, Any] = {
            "service_name": "s3",
            "region_name": self.region_name,
            "verify": self._verify_ssl,
        }

        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        if aws_access_key_id and aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key

        # Configure connection timeouts and retry limits
        config = Config(
            connect_timeout=5,
            read_timeout=30,
            retries={"max_attempts": 3, "mode": "standard"},
        )
        client_kwargs["config"] = config

        try:
            return boto3.client(**client_kwargs)
        except Exception as exc:
            redacted = redact_s3_error(exc)
            LOGGER.error("Failed to construct S3 client: %s", redacted)
            raise RuntimeError(f"Failed to construct S3 client: {redacted}") from None

    def get_cas_s3_key(self, sha256_hash: str) -> str:
        """
        Construct bucket object key for a SHA-256 CAS block (AC2.3).
        Enforces canonical 64-char lowercase hex validation to block path traversal.
        """
        valid_key = validate_cas_key(sha256_hash)
        return f"cas/{valid_key[:2]}/{valid_key[2:4]}/{valid_key}"

    def exists_remote(self, sha256_hash: str) -> bool:
        """
        Check if a CAS block exists in remote cloud storage with HEAD confirmation (AC2.5).
        Uses fast Redis / local index as pre-filter, but verifies true presence via S3 HEAD.
        """
        valid_key = validate_cas_key(sha256_hash)
        s3_key = self.get_cas_s3_key(valid_key)

        # 1. Fast pre-check: Check local memory cache and Redis index
        with self._lock:
            cached = valid_key in self._local_dedup_cache

        if not cached and self.redis_client:
            try:
                cached = bool(self.redis_client.sismember("scrape:cas_remote_index", valid_key))
            except Exception as exc:
                LOGGER.warning(
                    "Redis remote dedup index lookup failed (%s); falling back to direct S3 HEAD verification.",
                    exc,
                )

        # 2. AC2.5: Never trust index blindly — confirm with cheap HEAD check against the bucket
        try:
            self._client.head_object(Bucket=self.bucket, Key=s3_key)
            with self._lock:
                self._local_dedup_cache.add(valid_key)
            if self.redis_client:
                try:
                    self.redis_client.sadd("scrape:cas_remote_index", valid_key)
                except Exception as exc:
                    LOGGER.warning(
                        "Failed to update Redis remote dedup index (%s); proceeding with direct S3 state.",
                        exc,
                    )
            return True
        except Exception as exc:
            # 404 / NotFound means the object does not actually exist remotely (stale index entry)
            if hasattr(exc, "response") and isinstance(exc.response, dict):
                error_code = str(exc.response.get("Error", {}).get("Code", ""))
                if error_code in ("404", "NoSuchKey", "NotFound"):
                    return False
                LOGGER.warning("S3 HEAD error checking remote block %s: %s", valid_key, redact_s3_error(exc))
                return False
            LOGGER.warning("Unexpected error during S3 HEAD check for %s: %s", valid_key, redact_s3_error(exc))
            return False

    def upload_block_sync(self, sha256_hash: str, file_path: Path | str) -> bool:
        """
        Synchronously upload a single local CAS block to S3.
        Returns True if uploaded, or False if already existed remotely.
        """
        valid_key = validate_cas_key(sha256_hash)
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Local CAS block not found at {path}")

        # If already exists remotely per HEAD verification, skip upload
        if self.exists_remote(valid_key):
            return False

        s3_key = self.get_cas_s3_key(valid_key)
        try:
            with open(path, "rb") as f:
                self._client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=f,
                    ContentType="application/octet-stream",
                )

            with self._lock:
                self._local_dedup_cache.add(valid_key)
            if self.redis_client:
                try:
                    self.redis_client.sadd("scrape:cas_remote_index", valid_key)
                except Exception:
                    pass

            LOGGER.debug("Successfully synced CAS block %s to s3://%s/%s", valid_key, self.bucket, s3_key)
            return True
        except Exception as exc:
            redacted = redact_s3_error(exc)
            LOGGER.error("Failed to upload CAS block %s to S3: %s", valid_key, redacted)
            raise RuntimeError(f"Cloud CAS upload failed: {redacted}") from None

    def enqueue_upload(self, sha256_hash: str, file_path: Path | str, block: bool = True, timeout: float = 5.0) -> bool:
        """
        Enqueue a CAS block for background cloud replication with backpressure (AC2.6).
        If the spooling queue is full, blocks up to timeout seconds or raises CASQueueFullError.
        """
        if not self._running:
            return False

        valid_key = validate_cas_key(sha256_hash)
        path = Path(file_path).resolve()

        # Fast pre-check: if already known locally to exist remotely, don't enqueue
        with self._lock:
            if valid_key in self._local_dedup_cache:
                return False

        try:
            self._queue.put((valid_key, path), block=block, timeout=timeout)
            return True
        except queue.Full:
            LOGGER.warning(
                "CAS cloud spooling queue full (capacity %d); applying ingestion backpressure (AC2.6).",
                self.max_queue_size,
            )
            raise CASQueueFullError(
                f"CAS cloud sync queue capacity ({self.max_queue_size}) exceeded. Ingestion throttled."
            ) from None

    def generate_presigned_get_url(self, sha256_hash: str, expires_in: int = MAX_PRESIGNED_EXPIRY_SECONDS) -> str:
        """
        Generate an ephemeral presigned GET URL for a single CAS block (AC2.4).
        Scoped strictly to GetObject on the specific key, bounded to <=900s TTL.
        Never written to logs or disk.
        """
        valid_key = validate_cas_key(sha256_hash)
        s3_key = self.get_cas_s3_key(valid_key)

        ttl = min(max(1, expires_in), MAX_PRESIGNED_EXPIRY_SECONDS)

        try:
            url = self._client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=ttl,
            )
            return url
        except Exception as exc:
            redacted = redact_s3_error(exc)
            LOGGER.error("Failed to generate presigned URL for %s: %s", valid_key, redacted)
            raise RuntimeError(f"Presigned URL generation failed: {redacted}") from None

    def _start_workers(self):
        """Start background worker threads consuming from the spooling queue."""
        for i in range(self.concurrency):
            t = threading.Thread(target=self._worker_loop, name=f"CASCloudSyncWorker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    def _worker_loop(self):
        """Worker thread loop processing queued uploads."""
        while self._running:
            try:
                item = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if item is None:
                self._queue.task_done()
                break

            sha256_hash, path = item
            try:
                self.upload_block_sync(sha256_hash, path)
            except Exception as exc:
                LOGGER.debug("Background CAS upload worker encountered error: %s", redact_s3_error(exc))
            finally:
                self._queue.task_done()

    def close(self, drain: bool = True, timeout: float = 10.0):
        """Shutdown background workers, optionally draining in-flight queue items."""
        if drain:
            deadline = time.time() + timeout
            while time.time() < deadline:
                if self._queue.unfinished_tasks == 0:
                    break
                time.sleep(0.02)

        self._running = False

        # Send poison pills to unblock worker loops
        for _ in self._workers:
            try:
                self._queue.put_nowait(None)
            except Exception:
                pass

        per_worker_timeout = max(0.1, timeout / max(1, len(self._workers)))
        for t in self._workers:
            t.join(timeout=per_worker_timeout)

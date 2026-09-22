"""Pluggable storage sink backends for scrAPE (Local disk, S3/MinIO/R2)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, BinaryIO

LOGGER = logging.getLogger(__name__)


def _sanitize_rel_path(rel_path: str) -> str:
    """Normalize relative path and prevent directory traversal."""
    normalized = os.path.normpath(rel_path).replace("\\", "/")
    parts = [p for p in normalized.split("/") if p and p != ".." and p != "."]
    safe_parts = [re.sub(r'[<>:"|?*]', "_", p) for p in parts]
    return "/".join(safe_parts)


class BaseStorageSink:
    """Abstract base protocol for storage sinks."""

    def save_bytes(self, data: bytes, relative_path: str, metadata: dict[str, Any] | None = None) -> str:
        raise NotImplementedError

    def save_stream(self, stream: BinaryIO, relative_path: str, metadata: dict[str, Any] | None = None) -> str:
        raise NotImplementedError

    def exists(self, relative_path: str) -> bool:
        raise NotImplementedError

    def get_uri(self, relative_path: str) -> str:
        raise NotImplementedError

    def close(self) -> None:
        pass


class LocalStorageSink(BaseStorageSink):
    """Local filesystem storage sink with atomic write semantics."""

    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_target(self, relative_path: str) -> Path:
        segments = relative_path.replace("\\", "/").split("/")
        if ".." in segments:
            raise ValueError(f"Path traversal detected: {relative_path}")
        safe_rel = _sanitize_rel_path(relative_path)
        target = (self.root_dir / safe_rel).resolve()
        if not str(target).startswith(str(self.root_dir)):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return target

    def save_bytes(self, data: bytes, relative_path: str, metadata: dict[str, Any] | None = None) -> str:
        target = self._resolve_target(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write via temp file
        temp_fd, temp_path = tempfile.mkstemp(dir=target.parent, prefix="tmp_scrape_")
        try:
            with os.fdopen(temp_fd, "wb") as f:
                f.write(data)
            shutil.move(temp_path, str(target))
        except Exception:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            raise

        return str(target)

    def save_stream(self, stream: BinaryIO, relative_path: str, metadata: dict[str, Any] | None = None) -> str:
        target = self._resolve_target(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(dir=target.parent, prefix="tmp_scrape_")
        try:
            with os.fdopen(temp_fd, "wb") as f:
                shutil.copyfileobj(stream, f)
            shutil.move(temp_path, str(target))
        except Exception:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            raise

        return str(target)

    def exists(self, relative_path: str) -> bool:
        try:
            target = self._resolve_target(relative_path)
            return target.exists() and target.is_file()
        except ValueError:
            return False

    def get_uri(self, relative_path: str) -> str:
        return str(self._resolve_target(relative_path))


class S3StorageSink(BaseStorageSink):
    """S3-compatible object store sink (AWS S3, MinIO, Wasabi, Cloudflare R2)."""

    def __init__(
        self,
        bucket_name: str,
        prefix: str = "",
        endpoint_url: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region_name: str | None = None,
        spillover_dir: Path | str | None = None,
    ):
        from common.security import validate_s3_endpoint_url
        from config.settings_manager import settings

        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        raw_endpoint = endpoint_url or settings.get_s3_endpoint_url()
        self.endpoint_url = validate_s3_endpoint_url(raw_endpoint) if raw_endpoint else None
        self.access_key = aws_access_key_id or settings.get_aws_access_key_id()
        self.secret_key = aws_secret_access_key or settings.get_aws_secret_access_key()
        self.region_name = region_name or settings.get_s3_region()

        self.spillover_dir = Path(spillover_dir or "output/spillover").resolve()
        self._local_fallback = LocalStorageSink(self.spillover_dir)
        self._client = None
        self._s3_available = False

        self._init_s3_client()

    def _init_s3_client(self) -> None:
        try:
            import boto3
            from botocore.config import Config

            session = boto3.session.Session()
            self._client = session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region_name,
                config=Config(retries={"max_attempts": 3, "mode": "standard"}, signature_version="s3v4"),
            )
            self._s3_available = True
            LOGGER.info("S3StorageSink initialized for bucket: %s (endpoint: %s)", self.bucket_name, self.endpoint_url)
        except Exception as exc:
            from storage.cas_sync import redact_s3_error

            LOGGER.warning(
                "boto3 client initialization failed (%s); S3StorageSink will spillover locally.",
                redact_s3_error(exc),
            )
            self._s3_available = False

    def _build_key(self, relative_path: str) -> str:
        safe_rel = _sanitize_rel_path(relative_path)
        if self.prefix:
            return f"{self.prefix}/{safe_rel}"
        return safe_rel

    def save_bytes(self, data: bytes, relative_path: str, metadata: dict[str, Any] | None = None) -> str:
        key = self._build_key(relative_path)
        if self._s3_available and self._client:
            try:
                extra_args = {}
                if metadata and "content_type" in metadata:
                    extra_args["ContentType"] = metadata["content_type"]
                self._client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=data,
                    **extra_args,
                )
                return self.get_uri(relative_path)
            except Exception as err:
                LOGGER.warning("S3 put_object failed for %s (%s). Spilling over locally.", key, err)

        # Spillover locally
        return self._local_fallback.save_bytes(data, relative_path, metadata)

    def save_stream(self, stream: BinaryIO, relative_path: str, metadata: dict[str, Any] | None = None) -> str:
        key = self._build_key(relative_path)
        if self._s3_available and self._client:
            try:
                extra_args = {}
                if metadata and "content_type" in metadata:
                    extra_args["ContentType"] = metadata["content_type"]
                self._client.upload_fileobj(
                    Fileobj=stream,
                    Bucket=self.bucket_name,
                    Key=key,
                    ExtraArgs=extra_args or None,
                )
                return self.get_uri(relative_path)
            except Exception as err:
                LOGGER.warning("S3 upload_fileobj failed for %s (%s). Spilling over locally.", key, err)
                if hasattr(stream, "seek"):
                    try:
                        stream.seek(0)
                    except Exception:
                        pass

        # Spillover locally
        return self._local_fallback.save_stream(stream, relative_path, metadata)

    def exists(self, relative_path: str) -> bool:
        key = self._build_key(relative_path)
        if self._s3_available and self._client:
            try:
                self._client.head_object(Bucket=self.bucket_name, Key=key)
                return True
            except Exception:
                pass
        return self._local_fallback.exists(relative_path)

    def get_uri(self, relative_path: str) -> str:
        key = self._build_key(relative_path)
        if self._s3_available and self.endpoint_url:
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{key}"
        elif self._s3_available:
            return f"s3://{self.bucket_name}/{key}"
        return self._local_fallback.get_uri(relative_path)


def get_storage_sink(
    backend: str = "local",
    root_dir: Path | str | None = None,
    s3_bucket: str = "",
    s3_prefix: str = "",
    **kwargs: Any,
) -> BaseStorageSink:
    """Factory creating configured storage sink."""
    if backend.lower() == "s3" and s3_bucket:
        return S3StorageSink(bucket_name=s3_bucket, prefix=s3_prefix, **kwargs)
    return LocalStorageSink(root_dir=root_dir or "output")

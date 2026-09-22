"""Content-Addressable Storage (CAS) with atomic NTFS hardlinks and cross-volume copy fallback."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
import shutil
from typing import Any, BinaryIO

LOGGER = logging.getLogger(__name__)

DEFAULT_CAS_ROOT = Path(".storage") / "cas"


class ContentAddressableStore:
    """
    Global Content-Addressable Storage (CAS) engine.
    Deduplicates media files globally by storing exactly one physical copy at:
      `.storage/cas/{sha256[:2]}/{sha256[2:]}.{ext}`
    Exposes run-specific views using atomic NTFS hardlinks (`os.link`),
    consuming 0 additional disk bytes across runs and keywords.
    """

    def __init__(
        self,
        root_dir: str | Path | None = None,
        cloud_syncer: Any | None = None,
    ) -> None:
        self.root_dir = Path(root_dir) if root_dir else DEFAULT_CAS_ROOT
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.cloud_syncer = cloud_syncer

    @classmethod
    def from_settings(
        cls,
        root_dir: str | Path | None = None,
        redis_client: Any | None = None,
    ) -> ContentAddressableStore:
        """Instantiate CAS store, automatically enabling CASCloudSyncer if ENABLE_CLOUD_CAS_SYNC is active."""
        cloud_syncer = None
        try:
            from config.settings_manager import settings

            enable_sync = settings.get("ENABLE_CLOUD_CAS_SYNC", "false").lower() in ("true", "1")
            bucket = settings.get("S3_BUCKET", "")
            if enable_sync and bucket:
                from storage.cas_sync import CASCloudSyncer

                cloud_syncer = CASCloudSyncer(
                    bucket=bucket,
                    endpoint_url=settings.get("S3_ENDPOINT_URL") or None,
                    region_name=settings.get("S3_REGION", "us-east-1"),
                    aws_access_key_id=settings.get("AWS_ACCESS_KEY_ID") or None,
                    aws_secret_access_key=settings.get("AWS_SECRET_ACCESS_KEY") or None,
                    insecure_skip_verify=settings.get("S3_INSECURE_SKIP_VERIFY", "false").lower() in ("true", "1"),
                    redis_client=redis_client,
                )
        except Exception as exc:
            LOGGER.warning("Could not initialize CASCloudSyncer from settings: %s", exc)

        return cls(root_dir=root_dir, cloud_syncer=cloud_syncer)

    def compute_hash(self, data: bytes | BinaryIO) -> str:
        h = hashlib.sha256()
        if isinstance(data, bytes):
            h.update(data)
        else:
            for chunk in iter(lambda: data.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def get_cas_path(self, sha256_hash: str, extension: str = "jpg") -> Path:
        import re
        from common.security import validate_cas_key, validate_safe_path

        clean_ext = re.sub(r"[^a-zA-Z0-9]", "", extension.lstrip(".").lower()) or "bin"
        clean_hash = re.sub(r"[^a-fA-F0-9]", "", sha256_hash).lower()
        if len(clean_hash) != 64:
            raise ValueError(f"Invalid sha256_hash: {sha256_hash}. Must be 64 hexadecimal characters.")

        valid_hash = validate_cas_key(clean_hash)
        prefix = valid_hash[:2]
        suffix = valid_hash[2:]
        bucket_dir = self.root_dir / prefix
        target = bucket_dir / f"{suffix}.{clean_ext}"
        return validate_safe_path(self.root_dir, target)

    def exists(self, sha256_hash: str, extension: str = "jpg") -> bool:
        return self.get_cas_path(sha256_hash, extension).is_file()

    def store(self, data: bytes, extension: str = "jpg") -> tuple[str, Path]:
        """Store media bytes in CAS if not already present; return (hash, cas_path)."""
        sha256_hash = self.compute_hash(data)
        cas_path = self.get_cas_path(sha256_hash, extension)

        if not cas_path.is_file():
            cas_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = cas_path.with_suffix(f".tmp_{os.getpid()}")
            tmp_path.write_bytes(data)
            tmp_path.replace(cas_path)
            LOGGER.debug("CAS: Stored new asset %s (%d bytes)", sha256_hash[:12], len(data))
        else:
            LOGGER.debug("CAS: Asset %s already exists; deduplicated.", sha256_hash[:12])

        if self.cloud_syncer is not None:
            self.cloud_syncer.enqueue_upload(sha256_hash, cas_path)

        return sha256_hash, cas_path

    def link_to_run(
        self,
        sha256_hash: str,
        destination_path: str | Path,
        extension: str = "jpg",
    ) -> Path:
        """
        Link a CAS asset into a human-readable run directory.
        Attempts atomic NTFS/POSIX hardlink (0 extra bytes); falls back to copyfile.
        """
        cas_path = self.get_cas_path(sha256_hash, extension)
        if not cas_path.is_file():
            raise FileNotFoundError(f"Asset with hash {sha256_hash} not found in CAS.")

        dst = Path(destination_path)
        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            return dst

        try:
            os.link(cas_path, dst)
            LOGGER.debug("CAS: Hardlinked %s -> %s", cas_path.name, dst)
        except (OSError, NotImplementedError) as link_err:
            LOGGER.debug("Hardlink failed (%s); falling back to copyfile.", link_err)
            shutil.copyfile(cas_path, dst)

        return dst

"""Content-Addressable Storage (CAS) with atomic NTFS hardlinks and cross-volume copy fallback."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
import shutil
from typing import BinaryIO

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

    def __init__(self, root_dir: str | Path | None = None) -> None:
        self.root_dir = Path(root_dir) if root_dir else DEFAULT_CAS_ROOT
        self.root_dir.mkdir(parents=True, exist_ok=True)

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

        clean_ext = re.sub(r"[^a-zA-Z0-9]", "", extension.lstrip(".").lower()) or "bin"
        clean_hash = re.sub(r"[^a-fA-F0-9]", "", sha256_hash)
        if len(clean_hash) < 2:
            raise ValueError(f"Invalid sha256_hash: {sha256_hash}")

        prefix = clean_hash[:2]
        suffix = clean_hash[2:]
        bucket_dir = self.root_dir / prefix
        target = Path(os.path.abspath(os.path.normpath(bucket_dir / f"{suffix}.{clean_ext}")))

        root_str = str(Path(os.path.abspath(os.path.normpath(self.root_dir))))
        target_str = str(target)
        if not (target_str == root_str or target_str.startswith(root_str + os.sep)):
            raise ValueError(f"Path traversal detected: {target_str} outside {root_str}")
        return target

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

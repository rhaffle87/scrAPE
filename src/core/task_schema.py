"""
task_schema.py — Strict Pydantic schemas for distributed crawl and download tasks.

Enforces AC1.3:
  - Rejects path-traversal sequences (../, ..\\) in all filesystem fields.
  - Rejects SSRF target URLs (loopback, link-local, cloud metadata) via is_safe_target_url.
  - Enforces field bounds, alphanumeric task identifiers, and SHA-256 digest formats.
"""

from __future__ import annotations

from pathlib import Path
import re
import time
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

from common.security import is_safe_target_url, validate_safe_path

TASK_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,128}$")
SHA256_REGEX = re.compile(r"^[0-9a-f]{64}$")
SAFE_DOMAIN_REGEX = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$")


class BaseTaskPayload(BaseModel):
    """Base model for distributed cluster tasks."""
    task_id: str = Field(..., description="Unique alphanumeric task identifier.")
    task_type: Literal["crawl", "download"] = Field(..., description="Task classification.")
    lease_ttl: int = Field(default=30, ge=5, le=3600, description="Task lease duration in seconds.")
    delivery_count: int = Field(default=0, ge=0, le=100, description="Delivery attempt counter.")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp.")

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("task_id must be a non-empty string.")
        if "\x00" in v or ".." in v or "/" in v or "\\" in v:
            raise ValueError(f"task_id contains forbidden characters: {v!r}")
        if not TASK_ID_REGEX.match(v):
            raise ValueError(f"task_id must be alphanumeric (hyphens/underscores allowed, 1-128 chars): {v!r}")
        return v


def _validate_safe_task_filesystem_path(field_name: str, v: str) -> str:
    if not v or not isinstance(v, str):
        raise ValueError(f"{field_name} must be a non-empty string.")
    if "\x00" in v:
        raise ValueError(f"{field_name} contains null byte.")

    v_lower = v.lower()
    if ".." in v or "%2e%2e" in v_lower or "%2f" in v_lower or "%5c" in v_lower or "..;" in v:
        raise ValueError(f"Path traversal sequence detected in {field_name}: {v!r}")

    # Explicitly check for UNC shares (e.g., \\attacker\share) on all platforms
    if v.startswith(r"\\") or v.startswith("//"):
        raise ValueError(f"UNC network share paths not allowed in {field_name}: {v!r}")

    # Absolute Windows paths on POSIX systems:
    # On POSIX, Path("C:\Windows") treats "C:\Windows" as a relative path inside current directory.
    # Explicitly reject Windows drive letters and leading backslashes on non-Windows platforms.
    import os
    if os.name != "nt":
        if re.match(r"^[a-zA-Z]:", v):
            raise ValueError(f"Windows drive-letter paths not allowed on POSIX systems in {field_name}: {v!r}")
        if v.startswith("\\"):
            raise ValueError(f"Leading backslash paths not allowed on POSIX systems in {field_name}: {v!r}")
        if "\\" in v:
            normalized_posix = v.replace("\\", "/")
            if normalized_posix.startswith("/"):
                raise ValueError(f"Absolute path escape in {field_name}: {v!r}")

    import tempfile
    candidate = Path(v).resolve()

    allowed_roots = [
        Path(".").resolve(),
        Path(tempfile.gettempdir()).resolve(),
    ]
    try:
        import config
        if hasattr(config, "OUTPUT_DIR"):
            allowed_roots.append(Path(config.OUTPUT_DIR).resolve())
    except Exception:
        pass

    safe = False
    for root in allowed_roots:
        try:
            validate_safe_path(root, candidate)
            safe = True
            break
        except Exception:
            continue

    if not safe:
        raise ValueError(f"{field_name} escapes workspace boundaries: {v!r}")
    return v


class CrawlTaskPayload(BaseTaskPayload):
    """Payload definition for distributed domain crawling tasks."""
    task_type: Literal["crawl"] = "crawl"
    seed_url: str = Field(..., max_length=2048, description="Target seed URL to crawl.")
    output_dir: str = Field(default="output", max_length=512, description="Target output directory.")
    page_limit: int = Field(default=10, ge=1, le=10000, description="Maximum pages to visit.")
    depth_limit: int = Field(default=2, ge=0, le=20, description="Maximum link crawl depth.")
    domain_whitelist: list[str] = Field(default_factory=list, max_length=100, description="Allowed domains.")

    @field_validator("seed_url")
    @classmethod
    def validate_seed_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("seed_url must be a non-empty string.")
        if "\x00" in v or "\r" in v or "\n" in v:
            raise ValueError("seed_url contains control characters.")
        if not is_safe_target_url(v):
            raise ValueError(f"seed_url rejected by SSRF security policy: {v!r}")
        return v

    @field_validator("output_dir")
    @classmethod
    def validate_output_directory(cls, v: str) -> str:
        return _validate_safe_task_filesystem_path("output_dir", v)

    @field_validator("domain_whitelist")
    @classmethod
    def validate_domains(cls, v: list[str]) -> list[str]:
        cleaned = []
        for domain in v:
            d = domain.strip().lower()
            if not d or len(d) > 253 or not SAFE_DOMAIN_REGEX.match(d):
                raise ValueError(f"Invalid domain format in whitelist: {domain!r}")
            cleaned.append(d)
        return cleaned


class DownloadTaskPayload(BaseTaskPayload):
    """Payload definition for distributed media download tasks."""
    task_type: Literal["download"] = "download"
    media_url: str = Field(..., max_length=2048, description="Target media URL to download.")
    destination_path: str = Field(..., max_length=512, description="Target destination file path.")
    sha256_hint: str | None = Field(default=None, description="Expected SHA-256 hex digest.")

    @field_validator("media_url")
    @classmethod
    def validate_media_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("media_url must be a non-empty string.")
        if "\x00" in v or "\r" in v or "\n" in v:
            raise ValueError("media_url contains control characters.")
        if not is_safe_target_url(v):
            raise ValueError(f"media_url rejected by SSRF security policy: {v!r}")
        return v

    @field_validator("destination_path")
    @classmethod
    def validate_dest_path(cls, v: str) -> str:
        return _validate_safe_task_filesystem_path("destination_path", v)

    @field_validator("sha256_hint")
    @classmethod
    def validate_hash_hint(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip().lower()
        if not SHA256_REGEX.match(cleaned):
            raise ValueError(f"sha256_hint must be a 64-character lowercase hex digest: {v!r}")
        return cleaned


def parse_task_payload(data: dict[str, Any]) -> CrawlTaskPayload | DownloadTaskPayload:
    """Parses and validates a task payload dictionary into its typed model."""
    if not isinstance(data, dict):
        raise ValueError("Task payload must be a JSON object dictionary.")

    task_type = data.get("task_type")
    if task_type == "crawl":
        return CrawlTaskPayload.model_validate(data)
    elif task_type == "download":
        return DownloadTaskPayload.model_validate(data)
    else:
        # If task_type is unspecified, infer from fields
        if "seed_url" in data:
            return CrawlTaskPayload.model_validate({**data, "task_type": "crawl"})
        elif "media_url" in data:
            return DownloadTaskPayload.model_validate({**data, "task_type": "download"})
        raise ValueError(f"Unrecognized task_type: {task_type!r}")

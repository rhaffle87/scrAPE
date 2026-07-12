from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.seed_manifest import DomainProfile, SeedManifest


@dataclass(slots=True)
class ImageItem:
    url: str
    source_page: str
    alt_text: str = ""
    score: int = 0
    page_title: str = ""
    mime_type: str = ""
    width: int | None = None
    height: int | None = None
    file_size_bytes: int | None = None
    in_layout_container: bool = False
    parent_anchor_text: str = ""
    parent_anchor_href: str = ""
    status: str = "pending"
    file_path: str = ""
    failure_reason: str = ""
    hash: str = ""
    source_domain: str = ""


@dataclass(slots=True)
class VideoItem:
    url: str
    source_page: str
    type: str
    score: int = 0
    page_title: str = ""
    mime_type: str = ""
    file_size_bytes: int | None = None
    duration_seconds: int | None = None
    in_layout_container: bool = False
    parent_anchor_text: str = ""
    parent_anchor_href: str = ""
    status: str = "pending"
    file_path: str = ""
    failure_reason: str = ""
    hash: str = ""
    source_domain: str = ""


@dataclass(slots=True)
class PageReport:
    url: str
    depth: int
    status: str
    reason: str = ""
    discovered_links: int = 0
    images_found: int = 0
    videos_found: int = 0


@dataclass(slots=True)
class RejectedItem:
    kind: str
    url: str
    source_page: str
    reason: str
    score: int = 0


@dataclass(slots=True)
class ScrapeResult:
    keyword: str
    run_id: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    scanned_pages: list[str] = field(default_factory=list)
    page_reports: list[PageReport] = field(default_factory=list)
    rejected_items: list[RejectedItem] = field(default_factory=list)
    images: list[ImageItem] = field(default_factory=list)
    videos: list[VideoItem] = field(default_factory=list)
    domain_stats: dict[str, dict[str, int]] = field(default_factory=dict)
    download_stats: dict[str, int] = field(default_factory=dict)
    duration_seconds: int | None = None
    run_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def keyword_slug(self) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", self.keyword.strip().lower())
        safe = normalized.strip("_")
        return safe or "query"

    def to_dict(self) -> dict[str, Any]:
        return {
            "keyword": self.keyword,
            "run_id": self.run_id,
            "duration_seconds": self.duration_seconds,
            "run_metadata": self.run_metadata,
            "page_count": len(self.scanned_pages),
            "scanned_pages": self.scanned_pages,
            "page_reports": [asdict(item) for item in self.page_reports],
            "rejected_items": [asdict(item) for item in self.rejected_items],
            "images": [asdict(item) for item in self.images],
            "videos": [asdict(item) for item in self.videos],
            "domain_stats": self.domain_stats,
            "download_stats": self.download_stats,
        }


@dataclass(slots=True)
class EngineOptions:
    keyword: str
    max_results: int
    output_format: str
    download_media: bool
    output_dir: Path
    seed_urls: list[str] = field(default_factory=list)
    seed_domains: list[str] = field(default_factory=list)
    allow_domains: list[str] = field(default_factory=list)
    block_domains: list[str] = field(default_factory=list)
    entity_tokens: list[str] = field(default_factory=list)
    use_search: bool = True
    strict_domain: bool = False
    site_tree_only: bool = False
    ignore_robots: bool = False
    # Seed manifest — populated by main.py when a seed file is parsed
    seed_manifest: SeedManifest | None = field(default=None)
    # Flattened {hostname: DomainProfile} lookup — built from seed_manifest
    domain_profiles: dict[str, DomainProfile] = field(default_factory=dict)

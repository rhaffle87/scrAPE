from __future__ import annotations

import csv
from pathlib import Path
from core.models import ScrapeResult

def write_csv(result: ScrapeResult, output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)

    image_file = output_root / "images.csv"
    with image_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "url",
                "source_page",
                "alt_text",
                "page_title",
                "score",
                "mime_type",
                "status",
                "file_path",
                "failure_reason",
                "hash",
            ],
        )
        writer.writeheader()
        for item in result.images:
            writer.writerow(
                {
                    "url": item.url,
                    "source_page": item.source_page,
                    "alt_text": item.alt_text,
                    "page_title": item.page_title,
                    "score": item.score,
                    "mime_type": item.mime_type,
                    "status": item.status,
                    "file_path": item.file_path,
                    "failure_reason": item.failure_reason,
                    "hash": item.hash,
                }
            )

    video_file = output_root / "videos.csv"
    with video_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "url",
                "source_page",
                "type",
                "page_title",
                "score",
                "mime_type",
                "status",
                "file_path",
                "failure_reason",
                "hash",
            ],
        )
        writer.writeheader()
        for item in result.videos:
            writer.writerow(
                {
                    "url": item.url,
                    "source_page": item.source_page,
                    "type": item.type,
                    "page_title": item.page_title,
                    "score": item.score,
                    "mime_type": item.mime_type,
                    "status": item.status,
                    "file_path": item.file_path,
                    "failure_reason": item.failure_reason,
                    "hash": item.hash,
                }
            )

    page_file = output_root / "pages.csv"
    with page_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "url",
                "depth",
                "status",
                "reason",
                "discovered_links",
                "images_found",
                "videos_found",
            ],
        )
        writer.writeheader()
        for item in result.page_reports:
            writer.writerow(
                {
                    "url": item.url,
                    "depth": item.depth,
                    "status": item.status,
                    "reason": item.reason,
                    "discovered_links": item.discovered_links,
                    "images_found": item.images_found,
                    "videos_found": item.videos_found,
                }
            )

    rejected_file = output_root / "rejected.csv"
    with rejected_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["kind", "url", "source_page", "reason", "score"],
        )
        writer.writeheader()
        for item in result.rejected_items:
            writer.writerow(
                {
                    "kind": item.kind,
                    "url": item.url,
                    "source_page": item.source_page,
                    "reason": item.reason,
                    "score": item.score,
                }
            )

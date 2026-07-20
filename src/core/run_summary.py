"""
run_summary.py — Post-run summary report generator for scrAPE.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from typing import TYPE_CHECKING, Any

from utils.logger import get_logger

if TYPE_CHECKING:
    from core.models import ScrapeResult

LOGGER = get_logger(__name__)


def generate_run_summary(
    result: ScrapeResult,
    output_dir: Path,
    crawl_duration_seconds: float,
    download_duration_seconds: float,
) -> dict[str, Any]:
    """Compile post-run statistics, output a console summary, and save run_summary.json.

    Parameters
    ----------
    result:
        The ScrapeResult containing run details.
    output_dir:
        Output folder for this specific run.
    crawl_duration_seconds:
        Measured duration of the BFS crawl phase.
    download_duration_seconds:
        Measured duration of the media download phase.

    Returns
    -------
    dict[str, Any]
        The compiled summary dictionary.
    """
    total_duration = result.duration_seconds or (crawl_duration_seconds + download_duration_seconds)

    # 1. Overall stats
    total_pages_scanned = len(result.scanned_pages)
    total_images_kept = len(result.images)
    total_videos_kept = len(result.videos)
    total_rejected_items = len(result.rejected_items)

    downloaded_count = result.download_stats.get("downloaded", 0)

    # Count download failures vs skips
    failed_downloads = 0
    skipped_downloads = 0
    for key, val in result.download_stats.items():
        if key == "downloaded":
            continue
        if key.startswith("download_failed") or "exception" in key:
            failed_downloads += val
        else:
            skipped_downloads += val

    # 2. Top rejection reasons
    rejection_counts = Counter(item.reason for item in result.rejected_items)
    top_rejections = dict(rejection_counts.most_common(10))

    # 3. Domain breakdown calculations
    domain_breakdown: dict[str, dict[str, int]] = {}

    # Pre-populate domains from result.domain_stats
    for domain, stats in result.domain_stats.items():
        domain_breakdown[domain] = {
            "pages_scanned": stats.get("pages_scanned", 0),
            "images_kept": stats.get("images_kept", 0),
            "videos_kept": stats.get("videos_kept", 0),
            "rejected_count": stats.get("rejected_count", 0),
            "duplicate_hash_skips": 0,
            "wasted_requests": 0,
        }

    # Count wasted requests: pages that yielded zero kept media
    for report in result.page_reports:
        domain = urlparse(report.url).netloc.lower()
        if not domain:
            continue
        domain_breakdown.setdefault(
            domain,
            {
                "pages_scanned": 0,
                "images_kept": 0,
                "videos_kept": 0,
                "rejected_count": 0,
                "duplicate_hash_skips": 0,
                "wasted_requests": 0,
            },
        )
        if report.images_found == 0 and report.videos_found == 0:
            domain_breakdown[domain]["wasted_requests"] += 1

    # Count duplicate hash skips and dead downloads per domain
    dead_download_urls: list[dict[str, str]] = []
    duplicate_hash_skips_by_domain: dict[str, int] = {}

    for item in result.rejected_items:
        domain = urlparse(item.source_page).netloc.lower()
        if not domain:
            continue

        domain_breakdown.setdefault(
            domain,
            {
                "pages_scanned": 0,
                "images_kept": 0,
                "videos_kept": 0,
                "rejected_count": 0,
                "duplicate_hash_skips": 0,
                "wasted_requests": 0,
            },
        )

        # Duplicate hash skips
        if "duplicate" in item.reason:
            domain_breakdown[domain]["duplicate_hash_skips"] += 1
            duplicate_hash_skips_by_domain[domain] = (
                duplicate_hash_skips_by_domain.get(domain, 0) + 1
            )

        # Dead download links (failures/exceptions)
        if item.reason.startswith("download_failed") or "exception" in item.reason:
            dead_download_urls.append(
                {
                    "url": item.url,
                    "source_page": item.source_page,
                    "reason": item.reason,
                }
            )

    # 4. Identify Zero-Yield domains (crawled > 0 pages but yielded 0 kept items)
    zero_yield_domains: list[str] = []
    for domain, stats in domain_breakdown.items():
        if (
            stats["pages_scanned"] > 0
            and stats["images_kept"] == 0
            and stats["videos_kept"] == 0
        ):
            zero_yield_domains.append(domain)

    # 5. Build final summary report
    summary = {
        "run_id": result.run_id,
        "keyword": result.keyword,
        "status": "completed",
        "runtime": {
            "total_duration_seconds": int(total_duration),
            "crawl_duration_seconds": int(crawl_duration_seconds),
            "download_duration_seconds": int(download_duration_seconds),
            "idle_or_other_seconds": int(
                max(0.0, total_duration - crawl_duration_seconds - download_duration_seconds)
            ),
        },
        "overall_stats": {
            "total_pages_scanned": total_pages_scanned,
            "total_images_kept": total_images_kept,
            "total_videos_kept": total_videos_kept,
            "total_rejected_items": total_rejected_items,
            "total_downloaded_count": downloaded_count,
            "total_failed_downloads": failed_downloads,
            "total_skipped_downloads": skipped_downloads,
        },
        "domain_breakdown": domain_breakdown,
        "top_rejection_reasons": top_rejections,
        "zero_yield_domains": sorted(zero_yield_domains),
        "dead_download_urls": dead_download_urls,
        "duplicate_hash_skips_by_domain": duplicate_hash_skips_by_domain,
    }

    # Write summary.json
    summary_path = output_dir / "run_summary.json"
    try:
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        LOGGER.info("Post-run summary written to %s", summary_path.resolve())
    except Exception as exc:
        LOGGER.warning("Could not write run_summary.json: %s", exc)

    # Output clean, informative CLI/log report
    log_cli_report(summary)

    return summary


def log_cli_report(summary: dict[str, Any]) -> None:
    """Print a clean, structured post-run report to stdout/logs."""
    sep = "=" * 72
    LOGGER.info(sep)
    LOGGER.info("POST-RUN OBSERVABILITY SUMMARY")
    LOGGER.info(sep)

    runtime = summary["runtime"]
    LOGGER.info(
        "Runtime Breakdown: Total: %ds | Crawl: %ds | Download: %ds | Other: %ds",
        runtime["total_duration_seconds"],
        runtime["crawl_duration_seconds"],
        runtime["download_duration_seconds"],
        runtime["idle_or_other_seconds"],
    )

    stats = summary["overall_stats"]
    LOGGER.info(
        "Overall Yield:     Pages: %d | Images Kept: %d | Videos Kept: %d | Rejections: %d",
        stats["total_pages_scanned"],
        stats["total_images_kept"],
        stats["total_videos_kept"],
        stats["total_rejected_items"],
    )

    LOGGER.info(
        "Download Status:   Success: %d | Failed: %d | Skipped (Low-Res/Dupes): %d",
        stats["total_downloaded_count"],
        stats["total_failed_downloads"],
        stats["total_skipped_downloads"],
    )

    LOGGER.info(sep)
    LOGGER.info("DOMAIN BREAKDOWN:")
    LOGGER.info(
        "  %-30s  %-6s  %-6s  %-6s  %-6s  %-6s  %-6s",
        "Domain",
        "Pages",
        "Img",
        "Vid",
        "Rej",
        "Dupes",
        "Wasted",
    )
    LOGGER.info("  " + "-" * 68)
    for domain, db in sorted(summary["domain_breakdown"].items(), key=lambda x: x[0]):
        LOGGER.info(
            "  %-30s  %-6d  %-6d  %-6d  %-6d  %-6d  %-6d",
            domain[:30],
            db["pages_scanned"],
            db["images_kept"],
            db["videos_kept"],
            db["rejected_count"],
            db["duplicate_hash_skips"],
            db["wasted_requests"],
        )

    if summary["zero_yield_domains"]:
        LOGGER.info(sep)
        LOGGER.info("ZERO-YIELD DOMAINS:")
        for domain in summary["zero_yield_domains"]:
            LOGGER.info("  - %s", domain)

    if summary["dead_download_urls"]:
        LOGGER.info(sep)
        LOGGER.info(
            "DEAD DOWNLOAD LINKS (%d found):", len(summary["dead_download_urls"])
        )
        for dl in summary["dead_download_urls"][:10]:  # limit to first 10
            LOGGER.info("  - URL:    %s", dl["url"])
            LOGGER.info("    Source: %s", dl["source_page"])
            LOGGER.info("    Reason: %s", dl["reason"])
        if len(summary["dead_download_urls"]) > 10:
            LOGGER.info(
                "  ... and %d more (see run_summary.json)",
                len(summary["dead_download_urls"]) - 10,
            )

    LOGGER.info(sep)

"""
audit_evaluator.py — Post-crawl quality audit and diagnostic success rate evaluator.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.models import ScrapeResult
from monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class CrawlAuditEvaluator:
    """
    Evaluates scrape runs by analyzing page reports, rejection logs, and domain stats
    to produce actionable diagnostic ratings, bottleneck root-causes, and auto-tuning recommendations.
    """

    @staticmethod
    def evaluate_crawl(
        result: ScrapeResult,
        crawl_duration_s: float = 0.0,
        download_duration_s: float = 0.0,
    ) -> Dict[str, Any]:
        """Compute comprehensive crawl audit metrics and diagnostics.

        Returns a dictionary containing:
        - overall_metrics: HTTP success rate, download success rate, yield efficiency, health grade
        - domain_evaluations: Per-domain success rates, error profiles, health states, and root-causes
        - recommendations: Config suggestions for improving future crawl performance
        """
        # 1. Page attempt counts
        total_pages_attempted = len(result.page_reports)
        successful_pages = sum(1 for p in result.page_reports if p.status == "success")
        failed_pages = sum(1 for p in result.page_reports if p.status in ("failed", "skipped"))

        http_success_rate = (
            round((successful_pages / total_pages_attempted) * 100.0, 2)
            if total_pages_attempted > 0
            else 100.0
        )

        # 2. Media Yield
        kept_images = sum(1 for img in result.images if img.status not in ("skipped", "failed"))
        kept_videos = sum(1 for vid in result.videos if vid.status not in ("skipped", "failed"))
        total_kept_media = kept_images + kept_videos
        yield_efficiency = (
            round(total_kept_media / max(1, len(result.scanned_pages)), 2)
            if result.scanned_pages
            else 0.0
        )

        # 3. Download success metrics
        downloaded = result.download_stats.get("downloaded", 0)
        failed_downloads = sum(
            val
            for key, val in result.download_stats.items()
            if key.startswith("download_failed") or key.startswith("download_error") or "exception" in key
        )
        total_download_attempts = downloaded + failed_downloads
        download_success_rate = (
            round((downloaded / total_download_attempts) * 100.0, 2)
            if total_download_attempts > 0
            else 100.0
        )

        # 4. Overall Health Grade
        if http_success_rate >= 90.0 and download_success_rate >= 90.0:
            health_grade = "A+"
        elif http_success_rate >= 80.0 and download_success_rate >= 80.0:
            health_grade = "A"
        elif http_success_rate >= 70.0:
            health_grade = "B"
        elif http_success_rate >= 50.0:
            health_grade = "C"
        else:
            health_grade = "F"

        # 5. Domain-level audit & root causes
        domain_evaluations: Dict[str, Dict[str, Any]] = {}
        global_recommendations: List[str] = []

        for domain, stats in result.domain_stats.items():
            scanned = stats.get("pages_scanned", 0)
            img_kept = stats.get("images_kept", 0)
            vid_kept = stats.get("videos_kept", 0)
            err_429 = stats.get("error_429_count", 0)
            err_other = stats.get("error_other_count", 0)
            total_errs = err_429 + err_other
            total_domain_attempts = scanned + total_errs

            domain_sr = (
                round((scanned / total_domain_attempts) * 100.0, 2)
                if total_domain_attempts > 0
                else 100.0
            )

            # Health classification
            if domain_sr >= 85.0 and (img_kept + vid_kept) > 0:
                health_state = "HEALTHY"
            elif domain_sr >= 70.0:
                health_state = "DEGRADED"
            elif total_errs > 0 and scanned == 0:
                health_state = "BLOCKED"
            else:
                health_state = "CRITICAL"

            root_causes: List[str] = []
            recommendations: List[str] = []

            if err_429 > 0:
                root_causes.append(f"Rate limiting pressure ({err_429} HTTP 429 hits)")
                recommendations.append(f"Reduce request rate for '{domain}' in domain_config.json")
            if err_other > 0:
                root_causes.append(f"Network / WAF challenges ({err_other} errors)")
                recommendations.append(f"Enable stealth browser tier for '{domain}' in domain_config.json")
            if scanned >= 10 and (img_kept + vid_kept) == 0:
                root_causes.append("Zero-yield domain (no accepted media matching keyword)")
                recommendations.append(f"Audit seed URLs and keyword filters for '{domain}'")

            domain_evaluations[domain] = {
                "pages_scanned": scanned,
                "media_kept": img_kept + vid_kept,
                "error_429_count": err_429,
                "error_other_count": err_other,
                "success_rate_pct": domain_sr,
                "health_state": health_state,
                "root_causes": root_causes,
                "recommendations": recommendations,
            }

            if recommendations:
                global_recommendations.extend(recommendations)

        # De-duplicate recommendations
        unique_recs = list(dict.fromkeys(global_recommendations))

        evaluation = {
            "overall_metrics": {
                "total_pages_attempted": total_pages_attempted,
                "successful_pages": successful_pages,
                "failed_pages": failed_pages,
                "http_success_rate_pct": http_success_rate,
                "download_success_rate_pct": download_success_rate,
                "media_yield_efficiency": yield_efficiency,
                "total_media_collected": total_kept_media,
                "health_grade": health_grade,
            },
            "domain_evaluations": domain_evaluations,
            "actionable_recommendations": unique_recs,
        }

        LOGGER.info(
            "Crawl Audit Completed: Grade %s | HTTP Success Rate: %.1f%% | Download Success Rate: %.1f%%",
            health_grade,
            http_success_rate,
            download_success_rate,
        )
        return evaluation

"""
test_crawl_audit_and_success_rate.py — Unit and integration tests for crawl success rate auditing
and real-time auto-remediation (v0.27.0).
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

from core.audit_evaluator import CrawlAuditEvaluator
from core.coordinator import CrawlCoordinator
from core.governor import CrawlGovernor
from core.models import ImageItem, PageReport, ScrapeResult
from core.run_summary import generate_run_summary


class DummyOptions:
    def __init__(self, keyword="cars", max_results=10):
        self.keyword = keyword
        self.max_results = max_results


def test_audit_evaluator_health_grades():
    """Verify CrawlAuditEvaluator produces expected health grades across scenarios."""
    # Scenario 1: A+ (100% HTTP, 100% Download)
    res_a_plus = ScrapeResult(
        keyword="nature",
        run_id="run_a_plus",
        scanned_pages=["https://example.com/1", "https://example.com/2"],
        images=[
            ImageItem(url="https://example.com/img1.jpg", source_page="https://example.com/1", status="downloaded"),
            ImageItem(url="https://example.com/img2.jpg", source_page="https://example.com/2", status="downloaded"),
        ],
        page_reports=[
            PageReport(url="https://example.com/1", depth=0, status="success"),
            PageReport(url="https://example.com/2", depth=1, status="success"),
        ],
        download_stats={"downloaded": 2},
        domain_stats={
            "example.com": {
                "pages_scanned": 2,
                "images_kept": 2,
                "videos_kept": 0,
                "error_429_count": 0,
                "error_other_count": 0,
            }
        },
    )
    eval_a = CrawlAuditEvaluator.evaluate_crawl(res_a_plus, crawl_duration_s=1.0, download_duration_s=1.0)
    assert eval_a["overall_metrics"]["health_grade"] == "A+"
    assert eval_a["overall_metrics"]["http_success_rate_pct"] == 100.0
    assert eval_a["overall_metrics"]["download_success_rate_pct"] == 100.0
    assert eval_a["overall_metrics"]["media_yield_efficiency"] == 1.0

    # Scenario 2: Critical / F grade (Low success rate)
    res_f = ScrapeResult(
        keyword="error_heavy",
        run_id="run_f",
        scanned_pages=["https://bad.com/1"],
        images=[],
        page_reports=[
            PageReport(url="https://bad.com/1", depth=0, status="success"),
            PageReport(url="https://bad.com/2", depth=1, status="failed"),
            PageReport(url="https://bad.com/3", depth=1, status="failed"),
            PageReport(url="https://bad.com/4", depth=1, status="failed"),
        ],
        download_stats={"downloaded": 0, "download_failed": 3},
        domain_stats={
            "bad.com": {
                "pages_scanned": 1,
                "images_kept": 0,
                "videos_kept": 0,
                "error_429_count": 2,
                "error_other_count": 1,
            }
        },
    )
    eval_f = CrawlAuditEvaluator.evaluate_crawl(res_f, crawl_duration_s=2.0, download_duration_s=1.0)
    assert eval_f["overall_metrics"]["health_grade"] == "F"
    assert eval_f["overall_metrics"]["http_success_rate_pct"] == 25.0
    assert eval_f["domain_evaluations"]["bad.com"]["health_state"] == "CRITICAL"
    assert any("429" in rc for rc in eval_f["domain_evaluations"]["bad.com"]["root_causes"])
    assert len(eval_f["actionable_recommendations"]) > 0


def test_crawl_governor_rolling_success_rate():
    """Verify CrawlGovernor rolling window tracks outcomes and computes health states."""
    gov = CrawlGovernor(initial_concurrency=4)
    host = "testsite.com"

    # Initially without history -> HEALTHY and 1.0
    assert gov.get_host_success_rate(host) == 1.0
    assert gov.get_host_health_state(host) == "HEALTHY"

    # Report 4 successes
    for _ in range(4):
        gov.report_success(host)
    assert gov.get_host_success_rate(host) == 1.0
    assert gov.get_host_health_state(host) == "HEALTHY"

    # Report 1 error -> 4/5 = 0.80 -> DEGRADED
    gov.report_error(host)
    assert gov.get_host_success_rate(host) == 0.80
    assert gov.get_host_health_state(host) == "DEGRADED"

    # Report 2 more errors -> 4/7 = 0.571 -> CRITICAL
    gov.report_429(host)
    gov.report_error(host)
    assert round(gov.get_host_success_rate(host), 2) == 0.57
    assert gov.get_host_health_state(host) == "CRITICAL"

    # Report heavy errors -> >= 5 attempts and SR < 0.25 -> PARKED
    for _ in range(15):
        gov.report_error(host)
    assert gov.get_host_success_rate(host) < 0.25
    assert gov.get_host_health_state(host) == "PARKED"

    # PARKED hosts trigger quiet backoff in is_host_available
    assert not gov.is_host_available(host)


def test_coordinator_auto_remediation_trigger():
    """Verify coordinator triggers TLS rotation and governor latency penalty on critical health."""
    options = DummyOptions(keyword="cars", max_results=10)
    mock_search = MagicMock()
    mock_result = ScrapeResult(keyword="cars", run_id="test_run")
    coord = CrawlCoordinator(
        search_provider=mock_search,
        video_scraper=MagicMock(),
        options=options,
        result=mock_result,
        state_cache=None,
        workers=2,
    )

    host = "blocked-host.com"
    # Artificially degrade host health
    for _ in range(4):
        coord.governor.report_429(host)

    assert coord.governor.get_host_health_state(host) == "CRITICAL"

    mock_http = MagicMock()
    mock_http.rotate_tls_profile.return_value = "firefox120"
    coord.search_provider.http = mock_http

    coord._auto_remediate_host(host)

    mock_http.rotate_tls_profile.assert_called_once_with(host)
    # AIMD concurrency should be dropped
    assert coord.governor.host_concurrency[host] <= 2.0


def test_run_summary_includes_audit_evaluation():
    """Verify generate_run_summary automatically attaches audit_evaluation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        res = ScrapeResult(
            keyword="mountains",
            run_id="run_sum_test",
            scanned_pages=["https://example.org/p1"],
            images=[ImageItem(url="https://example.org/img.jpg", source_page="https://example.org/p1", status="downloaded")],
            videos=[],
            page_reports=[PageReport(url="https://example.org/p1", depth=0, status="success")],
            download_stats={"downloaded": 1},
            domain_stats={"example.org": {"pages_scanned": 1, "images_kept": 1, "videos_kept": 0}},
        )

        summary = generate_run_summary(
            result=res,
            output_dir=out_dir,
            crawl_duration_seconds=1.5,
            download_duration_seconds=0.5,
        )

        assert "audit_evaluation" in summary
        assert summary["audit_evaluation"]["overall_metrics"]["health_grade"] == "A+"
        assert summary["audit_evaluation"]["overall_metrics"]["http_success_rate_pct"] == 100.0

"""Unit tests verifying that CrawlCoordinator respects options.use_search."""
from pathlib import Path
from unittest.mock import MagicMock
from types import SimpleNamespace
from core.coordinator import CrawlCoordinator
from core.models import ScrapeResult, EngineOptions


def test_coordinator_search_gate_when_use_search_is_true(tmp_path: Path):
    mock_video_scraper = MagicMock()
    mock_video_scraper.search.return_value = []
    
    options = EngineOptions(
        keyword="test query",
        max_results=5,
        output_format="json",
        download_media=False,
        output_dir=tmp_path,
        use_search=True,
    )
    result = ScrapeResult(run_id="run-1", keyword="test query")
    
    coordinator = CrawlCoordinator(
        search_provider=MagicMock(),
        video_scraper=mock_video_scraper,
        options=options,
        result=result,
        state_cache=MagicMock(),
        workers=1,
    )
    
    coordinator.execute([])
    mock_video_scraper.search.assert_called_once_with(
        "test query", 5, allow_domains=[], block_domains=[]
    )


def test_coordinator_search_gate_when_use_search_is_false(tmp_path: Path):
    mock_video_scraper = MagicMock()
    
    options = EngineOptions(
        keyword="test query",
        max_results=5,
        output_format="json",
        download_media=False,
        output_dir=tmp_path,
        use_search=False,
    )
    result = ScrapeResult(run_id="run-2", keyword="test query")
    
    coordinator = CrawlCoordinator(
        search_provider=MagicMock(),
        video_scraper=mock_video_scraper,
        options=options,
        result=result,
        state_cache=MagicMock(),
        workers=1,
    )
    
    coordinator.execute([])
    mock_video_scraper.search.assert_not_called()


def test_coordinator_search_gate_default_when_attribute_absent():
    mock_video_scraper = MagicMock()
    mock_video_scraper.search.return_value = []
    
    # Custom namespace without use_search attribute
    options = SimpleNamespace(
        keyword="test query",
        max_results=5,
        seed_urls=[],
        allow_domains=[],
        block_domains=[],
        domain_profiles={},
        strict_domain=False,
    )
    result = ScrapeResult(run_id="run-3", keyword="test query")
    
    coordinator = CrawlCoordinator(
        search_provider=MagicMock(),
        video_scraper=mock_video_scraper,
        options=options,
        result=result,
        state_cache=MagicMock(),
        workers=1,
    )
    
    coordinator.execute([])
    mock_video_scraper.search.assert_called_once_with(
        "test query", 5, allow_domains=[], block_domains=[]
    )


def test_coordinator_search_gate_when_max_results_is_zero(tmp_path: Path):
    mock_video_scraper = MagicMock()
    
    options = EngineOptions(
        keyword="test query",
        max_results=0,
        output_format="json",
        download_media=False,
        output_dir=tmp_path,
        use_search=True,
    )
    result = ScrapeResult(run_id="run-4", keyword="test query")
    
    coordinator = CrawlCoordinator(
        search_provider=MagicMock(),
        video_scraper=mock_video_scraper,
        options=options,
        result=result,
        state_cache=MagicMock(),
        workers=1,
    )
    
    coordinator.execute([])
    mock_video_scraper.search.assert_not_called()

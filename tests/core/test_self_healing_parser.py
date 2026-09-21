"""Unit tests for SelfHealingDOMParser verifying Tier 1 cache, Tier 2 heuristics, and Tier 3 synthesis."""

from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup

from core.self_healing_parser import SelfHealingDOMParser


def test_self_healing_tier2_jsonld_recovery(tmp_path: Path):
    db_path = tmp_path / "repaired.db"
    parser = SelfHealingDOMParser(db_path=db_path, enable_llm=False)

    html = """
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Article",
          "headline": "Sample Article",
          "image": [
            "https://example.com/media/photo1.jpg",
            "https://example.com/media/photo2.jpg"
          ]
        }
        </script>
      </head>
      <body><div>Obfuscated non-standard content</div></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    items = parser.extract(soup, "https://example.com/article/1", "Sample Article")

    assert len(items) == 2
    assert items[0].url == "https://example.com/media/photo1.jpg"
    assert items[0].extraction_source == "self_healing_jsonld"


def test_self_healing_tier2_structural_recovery_and_tier1_caching(tmp_path: Path):
    db_path = tmp_path / "repaired.db"
    parser = SelfHealingDOMParser(db_path=db_path, enable_llm=False)

    html = """
    <html>
      <body>
        <main>
          <img src="/static/hero1.png" alt="Hero 1" />
          <img src="/static/hero2.png" alt="Hero 2" />
          <img src="/static/hero3.png" alt="Hero 3" />
        </main>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    # First pass: Tier 2 structural recovery triggers and saves rule
    items = parser.extract(soup, "https://target-spa.org/feed", "SPA Feed")
    assert len(items) == 3
    assert items[0].url == "https://target-spa.org/static/hero1.png"
    assert "self_healing_structural:main img" in items[0].extraction_source

    # Second pass on fresh parser instance: Tier 1 cache hit triggers
    parser2 = SelfHealingDOMParser(db_path=db_path, enable_llm=False)
    cached_items = parser2.extract(soup, "https://target-spa.org/feed2", "SPA Feed 2")
    assert len(cached_items) == 3
    assert "self_healing_cached:main img" in cached_items[0].extraction_source


def test_self_healing_tier3_llm_synthesis(tmp_path: Path):
    db_path = tmp_path / "repaired.db"
    parser = SelfHealingDOMParser(db_path=db_path, enable_llm=True)

    html = """
    <html>
      <body>
        <div class="weird-custom-feed-xyz">
          <div data-asset-url="https://obfuscated.com/img1.webp"></div>
          <div data-asset-url="https://obfuscated.com/img2.webp"></div>
        </div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    # Mock LLM call returning synthesized selector
    with patch.object(
        parser,
        "_call_llm",
        return_value='{"selector": "div[data-asset-url]", "attribute": "data-asset-url", "confidence": 0.95}',
    ):
        items = parser.extract(soup, "https://obfuscated.com/gallery", "Obfuscated Gallery")
        assert len(items) == 2
        assert items[0].url == "https://obfuscated.com/img1.webp"
        assert "self_healing_llm:div[data-asset-url]" in items[0].extraction_source


def test_self_healing_get_metrics_and_run_summary(tmp_path: Path):
    db_path = tmp_path / "repaired.db"
    parser = SelfHealingDOMParser(db_path=db_path, enable_llm=False)
    parser.save_repaired_selector("testsite.org", "div.gallery img", "src", confidence=0.9)

    metrics = parser.get_metrics()
    assert metrics["total_repaired_domains"] == 1
    assert metrics["total_cache_hits"] >= 1
    assert metrics["repaired_domains"][0]["domain"] == "testsite.org"
    assert metrics["repaired_domains"][0]["selector"] == "div.gallery img"

    # Test run_summary integration
    from core.models import ScrapeResult, ImageItem
    from core.run_summary import generate_run_summary

    fake_result = ScrapeResult(
        keyword="test",
        images=[
            ImageItem(url="https://testsite.org/1.jpg", source_page="https://testsite.org", extraction_source="self_healing_cached:div.gallery img"),
            ImageItem(url="https://testsite.org/2.jpg", source_page="https://testsite.org", extraction_source="self_healing_jsonld"),
        ],
        run_id="run_test",
    )

    with patch("core.run_summary.SelfHealingDOMParser", return_value=parser):
        summary = generate_run_summary(fake_result, tmp_path, 1.0, 1.0)
        assert "self_healing" in summary
        assert summary["self_healing"]["items_recovered_this_run"] == 2
        assert summary["self_healing"]["breakdown_by_strategy"]["self_healing_cached"] == 1
        assert summary["self_healing"]["breakdown_by_strategy"]["self_healing_jsonld"] == 1
        assert summary["self_healing"]["database_metrics"]["total_repaired_domains"] == 1

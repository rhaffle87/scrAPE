import pytest
from src.network.http_client import HttpClient
import logging

@pytest.mark.e2e
def test_waf_escalation_to_browser(e2e_mock_server):
    """
    Test that the HttpClient properly escalates to a fallback engine when hitting a 403 WAF.
    """
    client = HttpClient()
    
    # 1. The /waf_escalation endpoint returns 403 for default python-httpx User-Agent.
    # We expect HttpClient to hit this, get 403, and escalate to stealth pipeline (Crawl4AI/Crawlee etc).
    # Once it hits the fallback browser, the User-Agent changes to a generic browser one, and it bypasses the 403.
    target_url = f"{e2e_mock_server}/waf_escalation"
    
    # Enable fallback by ensuring we don't skip it (some configs might default to true)
    response = client.get(target_url, timeout=30)
    
    # Should eventually succeed because fallback browser user-agents don't contain "python-httpx"
    assert response is not None
    assert response.status_code == 200
    assert "WAF bypassed successfully" in response.text

@pytest.mark.e2e
def test_js_rendering_payload(e2e_mock_server):
    """
    Test that the fallback stealth browsers actually evaluate JS and wait for DOM updates.
    """
    client = HttpClient()
    
    # 2. The /js_challenge endpoint returns a 200 immediately, but the payload isn't there.
    # Wait, if it returns 200 immediately, HttpClient tier 0 (httpx) will just return the raw HTML.
    # To test JS rendering, we need to force HttpClient to use a fallback engine.
    # We can do this by passing `force_engine` or similar, or by having the server return a 429 
    # and then the fallback engine renders it.
    
    # Let's mock the initial request to fail, or just use the StealthPipeline directly.
    from src.network.stealth_pipeline import StealthPipeline
    
    pipeline = StealthPipeline()
    target_url = f"{e2e_mock_server}/js_challenge"
    
    # Run the pipeline. Since it's a direct pipeline call, it will use the stealth browser right away.
    # The browser should wait for network idle or selector and capture the delayed JS.
    
    result = pipeline.execute(
        url=target_url,
        client=client,
        skip_httpx=True,
    )
    
    assert result.status_code == 200
    assert "Target Content Loaded via JS!" in result.text

@pytest.mark.e2e
def test_heavy_spa_simulation(e2e_mock_server):
    """
    Test that the fallback stealth browsers wait for a complex React/Vue SPA hydration
    and dynamic API fetches.
    """
    client = HttpClient()
    from src.network.stealth_pipeline import StealthPipeline
    
    pipeline = StealthPipeline()
    target_url = f"{e2e_mock_server}/heavy-spa"
    
    # Run the pipeline forcing stealth browser (that actually executes JS)
    result = pipeline.execute(
        url=target_url,
        client=client,
        skip_httpx=True,
        preferred_engine="crawl4ai",
    )
    
    assert result.status_code == 200
    assert "Hydrated. Fetching Data..." in result.text
    # Check that the delayed fetch and DOM injection worked
    assert "lazy-video" in result.text
    assert "Dynamic Video Content" in result.text


import logging
import asyncio
from typing import Any, cast
from core.coordinator import CrawlCoordinator
from core.models import ScrapeResult

logging.basicConfig(level=logging.INFO)
from unittest.mock import patch
import pytest

def test_preflight():
    async def _run():
    # We can instantiate CrawlCoordinator with dummy values since we only test the static/async _run_preflight
        class DummyOptions:
            pass
    
        coord = CrawlCoordinator(
            search_provider=None,
            video_scraper=None,
            options=cast(Any, DummyOptions()),
            result=cast(ScrapeResult, None),
            state_cache=None,
            workers=2
        )
    
        test_urls = [
            "https://www.google.com",
            "https://thisdomainwillneverexist123xyz.com",
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404"
        ]
        with patch("httpx.AsyncClient.head") as mock_head:
            # Mock responses for the URLs
            async def mock_head_func(url, **kwargs):
                import httpx
                if url == "https://www.google.com" or url == "https://httpbin.org/status/200":
                    return httpx.Response(200, request=httpx.Request("HEAD", url))
                elif url == "https://httpbin.org/status/404":
                    return httpx.Response(404, request=httpx.Request("HEAD", url))
                else:
                    raise httpx.ConnectError("Connection failed")
                    
            mock_head.side_effect = mock_head_func
            
            valid = await coord._run_preflight(test_urls)
            
        print("Valid URLs:")
        for u in valid:
            print(f" - {u}")
            
        assert any(u == "https://www.google.com" for u in valid)
        assert any(u == "https://httpbin.org/status/200" for u in valid)
        assert any(u == "https://thisdomainwillneverexist123xyz.com" for u in valid)
        assert not any(u == "https://httpbin.org/status/404" for u in valid)
    asyncio.run(_run())

if __name__ == "__main__":
    test_preflight()

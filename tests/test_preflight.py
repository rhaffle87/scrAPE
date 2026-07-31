import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging
import asyncio
from typing import Any, cast
from core.coordinator import CrawlCoordinator
from core.models import ScrapeResult

logging.basicConfig(level=logging.INFO)

async def test_preflight():
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
    
    valid = await coord._run_preflight(test_urls)
    print("Valid URLs:")
    for u in valid:
        print(f" - {u}")

if __name__ == "__main__":
    asyncio.run(test_preflight())

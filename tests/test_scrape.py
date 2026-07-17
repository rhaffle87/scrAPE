import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.http_client import HttpClient
from src.utils.logger import get_logger, configure_logging

configure_logging()
logger = get_logger(__name__)

urls_to_test = [
    "https://example.com",
]

def main():
    client = HttpClient()
    for url in urls_to_test:
        logger.info(f"Testing URL: {url}")
        try:
            resp = client.get(url)
            if resp:
                logger.info(f"SUCCESS: {url} -> {resp.status_code}")
                logger.info(f"Content preview: {resp.text[:1000]}")
            else:
                logger.error(f"FAILED (No response returned) for {url}")
        except Exception as e:
            logger.error(f"EXCEPTION fetching {url}: {e}")

if __name__ == '__main__':
    main()

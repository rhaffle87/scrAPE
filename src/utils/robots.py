from __future__ import annotations

from functools import lru_cache
from urllib import robotparser
from urllib.parse import urljoin, urlparse

from utils.http_client import HttpClient
from utils.logger import get_logger

LOGGER = get_logger(__name__)


class RobotsChecker:
    def __init__(self, http_client: HttpClient, ignore_robots: bool = False) -> None:
        self.http_client = http_client
        self.ignore_robots = ignore_robots

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        if self.ignore_robots:
            return True
        parser = self._get_parser(url)
        if parser is None:
            return True
        return parser.can_fetch(user_agent, url)

    @lru_cache(maxsize=128)
    def _get_parser(self, url: str) -> robotparser.RobotFileParser | None:
        parsed = urlparse(url)
        robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
        try:
            response = self.http_client.get(robots_url)
        except Exception as exc:
            LOGGER.debug("Unable to fetch robots.txt from %s: %s", robots_url, exc)
            return None

        parser = robotparser.RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser

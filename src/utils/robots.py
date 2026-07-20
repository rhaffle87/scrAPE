from __future__ import annotations

from urllib import robotparser
from urllib.parse import urljoin, urlparse

from utils.http_client import HttpClient
from utils.logger import get_logger

LOGGER = get_logger(__name__)


class RobotsChecker:
    def __init__(self, http_client: HttpClient, ignore_robots: bool = False) -> None:
        self.http_client = http_client
        self.ignore_robots = ignore_robots
        self._parsers: dict[str, robotparser.RobotFileParser | None] = {}

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        if self.ignore_robots:
            return True
        parser = self._get_parser(url)
        if parser is None:
            return True
        return parser.can_fetch(user_agent, url)

    def _get_parser(self, url: str) -> robotparser.RobotFileParser | None:
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if not netloc:
                return None
        except ValueError as exc:
            LOGGER.debug("Failed to parse URL %s: %s", url, exc)
            return None

        if netloc in self._parsers:
            return self._parsers[netloc]

        robots_url = urljoin(f"{parsed.scheme}://{netloc}", "/robots.txt")
        try:
            response = self.http_client.get(robots_url)
        except Exception as exc:
            LOGGER.debug("Unable to fetch robots.txt from %s: %s", robots_url, exc)
            self._parsers[netloc] = None
            return None

        # Fix 4: A successful robots.txt fetch should not leave any residual
        # failure count that might push the domain into cooldown.  The HttpClient
        # already calls record_success() internally, so this call is a safety net
        # that is a no-op in the normal flow but guards against edge-cases where
        # a previous transient error was recorded for robots.txt itself.
        cd_state = self.http_client._cooldown_state_for(robots_url)
        cd_state.record_success()

        parser = robotparser.RobotFileParser()
        parser.parse(response.text.splitlines())
        self._parsers[netloc] = parser
        return parser

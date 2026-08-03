"""
Base64IframeExtractor — a domain-agnostic plugin for sites that embed video
players inside iframes whose query parameters hold a base64-encoded HTML payload
containing the actual <video><source> or direct .mp4 URL.

Pattern (example):
    <iframe src="/wp-content/plugins/.../player-x.php?q=<base64>"></iframe>

The base64 payload, when decoded, contains HTML with:
    <source src="https://cdn.example.com/video.mp4" type="video/mp4">
"""
from __future__ import annotations

import base64
import logging
import re
from typing import TYPE_CHECKING, Optional
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from plugins.base import ExtractorPlugin, SpecializedResult

if TYPE_CHECKING:
    from network.http_client import HttpClient

LOGGER = logging.getLogger(__name__)

# Regex to pull a base64-encoded q= parameter directly from an iframe src,
# even if BeautifulSoup hasn't been applied yet.
_Q_PARAM_RE = re.compile(r"[?&]q=([A-Za-z0-9+/=%-]{20,})")
# Match direct video file extensions in decoded payload
_VIDEO_URL_RE = re.compile(
    r'https?://[^\s"\'<>]+\.(?:mp4|webm|m4v|mov|ogv)(?:[?#][^\s"\'<>]*)?',
    re.IGNORECASE,
)


def _safe_b64decode(value: str) -> str:
    """URL-decode then base64-decode, returning empty string on failure."""
    try:
        from urllib.parse import unquote
        value = unquote(value)
        # Add padding if needed
        padding = 4 - len(value) % 4
        if padding != 4:
            value += "=" * padding
        return base64.b64decode(value).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_html_from_qs_payload(decoded: str) -> str:
    """
    Some embedded player iframes encode a URL-encoded query string as their
    base64 payload (e.g. ``post_id=123&type=video&tag=%3Cvideo...%3E``).
    This helper extracts the HTML fragment from the ``tag`` key if present,
    otherwise returns the decoded string as-is (for simpler payloads).
    """
    try:
        from urllib.parse import parse_qs, unquote
        qs = parse_qs(decoded, keep_blank_values=True)
        tag_val = qs.get("tag", None)
        if tag_val:
            return unquote(tag_val[0])
    except Exception:
        pass
    return decoded

class Base64IframeExtractor(ExtractorPlugin):
    """
    Extracts video URLs hidden inside base64-encoded iframe query parameters.

    Activates on any page containing an iframe whose ``src`` has a ``q=``
    parameter with a base64-encoded HTML payload. This is a structural pattern,
    not tied to any specific domain.
    """

    name = "Base64IframeExtractor"
    priority = 45  # Run before generic scrapers but after yt-dlp

    # Signatures that indicate this player pattern is in use
    _PLAYER_PATH_SIGNATURES = ("player-x.php", "player.php", "embed.php", "player/embed")

    def can_handle(self, url: str) -> bool:
        """
        We cannot know statically whether a page uses this pattern; this plugin
        is invoked explicitly by the engine when it encounters a matching iframe
        during DOM parsing (via ``extract_from_soup``), not via the URL alone.
        Always return False so we don't accidentally intercept arbitrary URLs.
        """
        return False

    def extract(self, url: str, http_client: Optional["HttpClient"] = None) -> SpecializedResult:
        """Fetch the page and search for base64-iframe patterns."""
        if http_client is None:
            return SpecializedResult(images=[], videos=[])
        try:
            response = http_client.get(url)
            soup = BeautifulSoup(response.text, "lxml")
            return self.extract_from_soup(soup, page_url=url)
        except Exception as exc:
            LOGGER.warning("[Base64IframeExtractor] Failed to fetch %s: %s", url, exc)
            return SpecializedResult(images=[], videos=[])

    def extract_from_soup(self, soup: BeautifulSoup, page_url: str = "") -> SpecializedResult:
        """
        Parse a pre-fetched BeautifulSoup tree and extract all video URLs found
        inside base64-encoded iframe ``q`` parameters.

        Call this from the core engine after fetching a page when you detect
        any iframe matching the player path signatures.
        """
        videos: list[str] = []

        for iframe in soup.find_all("iframe"):
            if not isinstance(iframe, Tag):
                continue
            src = iframe.get("src", "")
            if not src:
                continue
            if isinstance(src, list):
                src = src[0]

            # Only bother with iframes that look like embedded players
            if not any(sig in src for sig in self._PLAYER_PATH_SIGNATURES):
                # Still try any iframe that has a q= parameter — maybe an unknown player
                if "?q=" not in src and "&q=" not in src:
                    continue

            # Resolve relative src
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/") and page_url:
                src = urljoin(page_url, src)

            # Extract q= param
            m = _Q_PARAM_RE.search(src)
            if not m:
                continue


            # Step 1: base64 → raw decoded string
            decoded = _safe_b64decode(m.group(1))
            if not decoded:
                LOGGER.debug("[Base64IframeExtractor] Empty decode for iframe src: %s", src)
                continue

            # Step 2: if the decoded string is a URL-encoded query string (e.g.
            # post_id=...&tag=%3Cvideo...%3E), extract the HTML fragment from 'tag'
            html_payload = _extract_html_from_qs_payload(decoded)

            # Step 3a: parse as HTML — most reliable for structured payloads
            inner = BeautifulSoup(html_payload, "lxml")
            for tag in inner.find_all(["source", "video"]):
                if not isinstance(tag, Tag):
                    continue
                candidate = tag.get("src", "")
                if isinstance(candidate, list):
                    candidate = candidate[0]
                if not candidate:
                    continue
                # Percent-encode spaces (CDN URLs sometimes contain unencoded spaces)
                candidate = candidate.replace(" ", "%20")
                if candidate not in videos:
                    LOGGER.info(
                        "[Base64IframeExtractor] Found video (HTML parse): %s (from %s)",
                        candidate, page_url,
                    )
                    videos.append(candidate)

            # Step 3b: fallback regex scan on raw text for any missed URLs
            for match in _VIDEO_URL_RE.finditer(html_payload):
                video_url = match.group(0).replace(" ", "%20")
                if video_url not in videos:
                    LOGGER.info(
                        "[Base64IframeExtractor] Found video (regex): %s (from %s)",
                        video_url, page_url,
                    )
                    videos.append(video_url)

        return SpecializedResult(images=[], videos=videos)


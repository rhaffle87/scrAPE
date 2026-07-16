from __future__ import annotations

import json
import re
from urllib.parse import parse_qs, quote_plus, urlencode, urlparse

from bs4 import BeautifulSoup

from core.filters import (
    absolutize_url,
    clean_attr,
    is_allowed_domain,
    is_allowed_path,
    is_http_url,
    normalize_url,
)
from core.models import VideoItem
from utils.http_client import HttpClient

YOUTUBE_PATTERNS = [
    re.compile(r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+"),
    re.compile(r"https?://youtu\.be/[\w-]+"),
    re.compile(r"https?://(?:www\.)?youtube\.com/embed/[\w-]+"),
]
VIMEO_PATTERNS = [
    re.compile(r"https?://(?:www\.)?vimeo\.com/\d+"),
    re.compile(r"https?://player\.vimeo\.com/video/\d+"),
]
DIRECT_VIDEO_PATTERN = re.compile(
    r"https?://[^\s\"'<>]+\.(?:mp4|webm|mov|m4v|ogv)\/?(?:\?[^\s\"'<>]*)?", re.I
)
HLS_PATTERN = re.compile(r"https?://[^\s\"'<>]+\.m3u8\/?(?:\?[^\s\"'<>]*)?", re.I)
DASH_PATTERN = re.compile(r"https?://[^\s\"'<>]+\.mpd\/?(?:\?[^\s\"'<>]*)?", re.I)


def extract_videos_from_html(
    soup: BeautifulSoup, page_url: str, page_title: str = ""
) -> list[VideoItem]:
    videos: list[VideoItem] = []
    seen: set[str] = set()

    # Pre-pass: scan and block any media URLs inside layout containers
    for el in soup.find_all(lambda tag: tag and _is_in_layout_container(tag)):
        for child in [el] + el.find_all(True):
            src = child.get("src") or child.get("href")
            if src:
                try:
                    seen.add(normalize_url(absolutize_url(src, page_url)))
                except Exception:
                    pass

    def add_video(item: VideoItem) -> None:
        normalized = normalize_url(item.url)
        if normalized not in seen:
            seen.add(normalized)
            videos.append(item)

    for video in soup.find_all("video"):
        in_layout = _is_in_layout_container(video)
        if in_layout:
            continue
        parent_anchor = video.find_parent("a")
        parent_anchor_text = ""
        parent_anchor_href = ""
        if parent_anchor:
            parent_anchor_href = normalize_url(
                absolutize_url(parent_anchor.get("href", "").strip(), page_url)
            )
            parent_anchor_text = clean_attr(
                parent_anchor.get_text() or parent_anchor.get("title", "")
            )

        video_src = video.get("src")
        if video_src:
            absolute = normalize_url(absolutize_url(video_src, page_url))
            add_video(
                VideoItem(
                    url=absolute,
                    source_page=page_url,
                    type=detect_video_type(absolute) or "direct",
                    page_title=page_title,
                    in_layout_container=in_layout,
                    parent_anchor_text=parent_anchor_text,
                    parent_anchor_href=parent_anchor_href,
                )
            )

        for source in video.find_all("source"):
            source_src = source.get("src")
            if not source_src:
                continue
            absolute = normalize_url(absolutize_url(source_src, page_url))
            add_video(
                VideoItem(
                    url=absolute,
                    source_page=page_url,
                    type=detect_video_type(absolute) or "direct",
                    page_title=page_title,
                    in_layout_container=in_layout,
                    parent_anchor_text=parent_anchor_text,
                    parent_anchor_href=parent_anchor_href,
                )
            )

    for iframe in soup.find_all(["iframe", "embed", "a"]):
        src = iframe.get("src") or iframe.get("href")
        if not src:
            continue
        absolute_url = normalize_url(absolutize_url(src, page_url))
        match_type = detect_video_type(absolute_url)
        if match_type:
            in_layout = _is_in_layout_container(iframe)
            if in_layout:
                continue
            parent_anchor = iframe if iframe.name == "a" else iframe.find_parent("a")
            parent_anchor_text = ""
            parent_anchor_href = ""
            if parent_anchor:
                parent_anchor_href = normalize_url(
                    absolutize_url(parent_anchor.get("href", "").strip(), page_url)
                )
                parent_anchor_text = clean_attr(
                    parent_anchor.get_text() or parent_anchor.get("title", "")
                )

            add_video(
                VideoItem(
                    url=absolute_url,
                    source_page=page_url,
                    type=match_type,
                    page_title=page_title,
                    in_layout_container=in_layout,
                    parent_anchor_text=parent_anchor_text,
                    parent_anchor_href=parent_anchor_href,
                )
            )

    for item in _extract_video_objects_from_jsonld(soup, page_url, page_title):
        add_video(item)

    for item in _extract_videos_from_scripts(soup, page_url, page_title):
        add_video(item)

    html = str(soup)
    for pattern, video_type in (
        *((pattern, "youtube") for pattern in YOUTUBE_PATTERNS),
        *((pattern, "vimeo") for pattern in VIMEO_PATTERNS),
        (DIRECT_VIDEO_PATTERN, "direct"),
        (HLS_PATTERN, "hls"),
        (DASH_PATTERN, "dash"),
    ):
        for match in pattern.findall(html):
            absolute = normalize_url(match)
            add_video(
                VideoItem(
                    url=absolute,
                    source_page=page_url,
                    type=video_type,
                    page_title=page_title,
                )
            )

    if not videos:
        from core.semantic_selectors import extract_semantic_fallback_videos
        fallback_videos = extract_semantic_fallback_videos(soup, page_url, page_title)
        for item in fallback_videos:
            add_video(item)

    return videos


def _extract_video_objects_from_jsonld(
    soup: BeautifulSoup,
    page_url: str,
    page_title: str,
) -> list[VideoItem]:
    videos: list[VideoItem] = []
    for script in soup.select("script[type='application/ld+json']"):
        raw = script.string or script.get_text(" ", strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        for item in _walk_json(payload):
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type")
            type_names = (
                {item_type.lower()}
                if isinstance(item_type, str)
                else {value.lower() for value in item_type if isinstance(value, str)}
                if isinstance(item_type, list)
                else set()
            )
            if "videoobject" not in type_names and not any(
                key in item for key in ("contentUrl", "embedUrl", "url")
            ):
                continue
            for key in ("contentUrl", "embedUrl", "url"):
                candidate = item.get(key)
                if not isinstance(candidate, str):
                    continue
                absolute = normalize_url(absolutize_url(candidate, page_url))
                video_type = detect_video_type(absolute)
                if video_type:
                    videos.append(
                        VideoItem(
                            url=absolute,
                            source_page=page_url,
                            type=video_type,
                            page_title=page_title,
                        )
                    )
    return videos


def _extract_videos_from_scripts(
    soup: BeautifulSoup,
    page_url: str,
    page_title: str,
) -> list[VideoItem]:
    videos: list[VideoItem] = []
    patterns = [
        (DIRECT_VIDEO_PATTERN, "direct"),
        (HLS_PATTERN, "hls"),
        (DASH_PATTERN, "dash"),
    ]
    for script in soup.find_all("script"):
        script_text = script.string or script.get_text(" ", strip=True)
        if not script_text:
            continue
        for pattern, video_type in patterns:
            for match in pattern.findall(script_text):
                absolute = normalize_url(absolutize_url(match, page_url))
                videos.append(
                    VideoItem(
                        url=absolute,
                        source_page=page_url,
                        type=video_type,
                        page_title=page_title,
                    )
                )
    return videos


def _walk_json(payload: object):
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from _walk_json(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _walk_json(item)


def detect_video_type(url: str) -> str | None:
    if any(pattern.search(url) for pattern in YOUTUBE_PATTERNS):
        return "youtube"
    if any(pattern.search(url) for pattern in VIMEO_PATTERNS):
        return "vimeo"
    try:
        path = urlparse(url).path.lower().rstrip("/")
    except Exception:
        path = ""
    if path.endswith(".m3u8"):
        return "hls"
    if path.endswith(".mpd"):
        return "dash"
    if is_http_url(url):
        return (
            "direct"
            if any(
                path.endswith(ext) for ext in {".mp4", ".webm", ".mov", ".m4v", ".ogv"}
            )
            else None
        )
    return None


class VideoScraper:
    # DuckDuckGo host variants requiring browser-stealth routing.
    _DDG_HOSTS = ("duckduckgo.com", "html.duckduckgo.com")

    def __init__(self, domain_delays: dict[str, float] | None = None) -> None:
        self.http = HttpClient(domain_delays=domain_delays)
        # Route DDG through browser stealth to bypass bot-detection.
        for ddg_host in self._DDG_HOSTS:
            HttpClient.register_stealth_required(ddg_host)

    def search(
        self,
        keyword: str,
        max_results: int,
        allow_domains: list[str] | None = None,
        block_domains: list[str] | None = None,
    ) -> list[VideoItem]:
        allow_domains = allow_domains or []
        block_domains = block_domains or []
        # kp=-2 disables SafeSearch; stealth routing already registered for DDG.
        search_url: str | None = (
            "https://duckduckgo.com/html/?q="
            f"{quote_plus(keyword)}+site%3Ayoutube.com+OR+site%3Avimeo.com&kp=-2"
        )
        videos: list[VideoItem] = []
        visited: set[str] = set()

        while search_url and search_url not in visited:
            visited.add(search_url)
            try:
                response = self.http.get(search_url)
                soup = BeautifulSoup(response.text, "lxml")
            except Exception:
                break

            for anchor in soup.select("a.result__a"):
                href = self._extract_result_href(anchor.get("href", "").strip())
                if not href:
                    continue
                if not is_allowed_domain(href, allow_domains, block_domains):
                    continue
                if not is_allowed_path(href):
                    continue
                video_type = detect_video_type(href)
                if not video_type:
                    continue
                normalized = normalize_url(href)
                if not any(v.url == normalized for v in videos):
                    videos.append(
                        VideoItem(
                            url=normalized,
                            source_page=search_url,
                            type=video_type,
                        )
                    )
                if max_results > 0 and len(videos) >= max_results:
                    break

            if max_results > 0 and len(videos) >= max_results:
                break

            # Follow next-page form (extracts vqd/s/dc tokens automatically).
            search_url = self._extract_next_page_url(soup)

        return videos

    @staticmethod
    def _extract_next_page_url(soup: BeautifulSoup) -> str | None:
        """Extract the next-page URL from the DuckDuckGo HTML results form."""
        for form in soup.find_all("form"):
            action = form.get("action", "")
            if "html" not in action.lower():
                continue
            params: dict[str, str] = {}
            for inp in form.find_all("input"):
                name = inp.get("name")
                val = inp.get("value", "")
                if name:
                    params[name] = val
            if params and ("s" in params or "vqd" in params):
                return f"https://html.duckduckgo.com/html/?{urlencode(params)}"
        return None

    @staticmethod
    def _extract_result_href(href: str) -> str:
        if not href:
            return ""
        parsed = urlparse(href)
        if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
            return parse_qs(parsed.query).get("uddg", [""])[0]
        return href


def _is_in_layout_container(element: object) -> bool:
    if not hasattr(element, "parents"):
        return False
    excluded_keywords = {
        "sidebar",
        "footer",
        "widget",
        "related",
        "popular",
        "recommend",
        "header",
        "menu",
        "nav",
        "carousel",
        "ad",
        "ads",
        "advert",
        "advertisement",
        "breadcrumb",
        "pagination",
        "comment",
        "share",
        "sharing",
        "social",
    }
    for parent in element.parents:
        if parent.name in ("body", "html"):
            break
        if parent.name in ("footer", "header", "aside", "nav"):
            return True
        parent_class = parent.get("class", [])
        parent_id = parent.get("id", "")

        tokens = set()
        if parent_id:
            tokens.update(re.split(r"[-_\s]+", str(parent_id).lower()))
        if parent_class:
            classes = parent_class if isinstance(parent_class, list) else [parent_class]
            for c in classes:
                tokens.update(re.split(r"[-_\s]+", str(c).lower()))

        if any(kw in tokens for kw in excluded_keywords):
            return True
    return False

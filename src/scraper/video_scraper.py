from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlencode, urlparse

from bs4 import BeautifulSoup, Tag

from core.filters import (
    absolutize_url,
    clean_attr,
    is_allowed_domain,
    is_allowed_path,
    is_http_url,
    normalize_url,
)
from core.models import VideoItem
from network.http_client import HttpClient

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


def _get_attr_str(tag: Any, attr: str, default: str = "") -> str:
    if not isinstance(tag, Tag):
        return default
    val = tag.get(attr, default)
    if isinstance(val, list):
        first = val[0] if val else default
        return first if isinstance(first, str) else str(first)
    if val is None:
        return default
    return val if isinstance(val, str) else str(val)


def extract_videos_from_html(
    soup: BeautifulSoup, page_url: str, page_title: str = ""
) -> list[VideoItem]:
    videos: list[VideoItem] = []
    seen: set[str] = set()

    # Pre-pass: scan and block any media URLs inside layout containers
    for el in soup.find_all(lambda tag: tag and isinstance(tag, Tag) and _is_in_layout_container(tag)):
        if not isinstance(el, Tag):
            continue
        children = [el] + [c for c in el.find_all(True) if isinstance(c, Tag)]
        for child in children:
            src = _get_attr_str(child, "src") or _get_attr_str(child, "href")
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
        if not isinstance(video, Tag):
            continue
        in_layout = _is_in_layout_container(video)
        if in_layout:
            continue
        parent_anchor = video.find_parent("a")
        parent_anchor_text = ""
        parent_anchor_href = ""
        if isinstance(parent_anchor, Tag):
            parent_anchor_href = normalize_url(
                absolutize_url(_get_attr_str(parent_anchor, "href").strip(), page_url)
            )
            parent_anchor_text = clean_attr(
                parent_anchor.get_text() or _get_attr_str(parent_anchor, "title")
            )

        video_src = _get_attr_str(video, "src")
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
            if not isinstance(source, Tag):
                continue
            source_src = _get_attr_str(source, "src")
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
        if not isinstance(iframe, Tag):
            continue
        src = _get_attr_str(iframe, "src") or _get_attr_str(iframe, "href")
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
            if isinstance(parent_anchor, Tag):
                parent_anchor_href = normalize_url(
                    absolutize_url(_get_attr_str(parent_anchor, "href").strip(), page_url)
                )
                parent_anchor_text = clean_attr(
                    parent_anchor.get_text() or _get_attr_str(parent_anchor, "title")
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

    # Generalised: extract sources from any class=v-player <video> element
    for video_el in soup.select("video.v-player source[src]"):
        if not isinstance(video_el, Tag):
            continue
        src = _get_attr_str(video_el, "src")
        if src:
            absolute_url = normalize_url(absolutize_url(src, page_url))
            add_video(
                VideoItem(
                    url=absolute_url,
                    source_page=page_url,
                    type=detect_video_type(absolute_url) or "direct",
                    page_title=page_title,
                    in_layout_container=False,
                )
            )

    # Lightbox anchor extraction: <a data-fslightbox href="...mp4">
    for item in _extract_lightbox_anchor_videos(soup, page_url, page_title):
        add_video(item)

    # Nested video source extraction: <video controls loop> with CDN <source> children
    for item in _extract_nested_video_sources(soup, page_url, page_title):
        add_video(item)

    # Base64-encoded iframe player extraction (e.g. player-x.php?q=<b64>)
    for item in _extract_base64_iframe_videos(soup, page_url, page_title):
        add_video(item)

    return videos



def _extract_lightbox_anchor_videos(
    soup: BeautifulSoup,
    page_url: str,
    page_title: str,
) -> list[VideoItem]:
    """
    LightboxAnchorExtractor — finds direct .mp4 URLs wrapped in fslightbox or
    similar lightbox anchor tags that standard HTML5 video parsers miss.

    Targets:
        <a data-fslightbox="gallery" href="https://example.com/video.mp4">…</a>
        <a href="https://cdn.example.com/clip.mp4" class="…">…</a>

    This is a structural pattern; not tied to any specific domain.
    """
    videos: list[VideoItem] = []
    seen: set[str] = set()

    _VIDEO_EXTS = {".mp4", ".webm", ".m4v", ".mov", ".ogv"}

    for anchor in soup.find_all("a", href=True):
        if not isinstance(anchor, Tag):
            continue
        # Prefer explicit fslightbox markup, but also catch bare .mp4 anchors
        has_lightbox_attr = anchor.has_attr("data-fslightbox") or anchor.has_attr("data-lightbox")
        href = _get_attr_str(anchor, "href").strip()
        if not href:
            continue

        try:
            parsed_path = urlparse(href).path.lower().rstrip("/")
        except Exception:
            continue

        is_video_link = any(parsed_path.endswith(ext) for ext in _VIDEO_EXTS)
        if not (has_lightbox_attr or is_video_link):
            continue

        if _is_in_layout_container(anchor):
            continue

        absolute_url = normalize_url(absolutize_url(href, page_url))
        if absolute_url in seen:
            continue
        seen.add(absolute_url)

        vtype = detect_video_type(absolute_url)
        if not vtype:
            continue

        videos.append(
            VideoItem(
                url=absolute_url,
                source_page=page_url,
                type=vtype,
                page_title=page_title,
                in_layout_container=False,
            )
        )
    return videos


def _extract_nested_video_sources(
    soup: BeautifulSoup,
    page_url: str,
    page_title: str,
) -> list[VideoItem]:
    """
    NestedVideoSourceExtractor — robustly extracts <source src> URLs from
    deeply nested <video> elements that use non-standard attributes (e.g.
    ``controls loop`` without a class) and are therefore skipped by the main
    ``<video>`` pass (which filters on layout containers aggressively).

    Specifically targets:
        <video controls loop>
            <source src="https://cdn.example.com/video.mp4" type="video/mp4">
        </video>

    This is a structural pattern; not tied to any specific domain.
    """
    videos: list[VideoItem] = []
    seen: set[str] = set()

    for video_tag in soup.find_all("video"):
        if not isinstance(video_tag, Tag):
            continue
        # Only target elements with both 'controls' and 'loop' (non-standard player)
        has_controls = video_tag.has_attr("controls")
        has_loop = video_tag.has_attr("loop")
        if not (has_controls and has_loop):
            continue

        if _is_in_layout_container(video_tag):
            continue

        for source in video_tag.find_all("source"):
            if not isinstance(source, Tag):
                continue
            src = _get_attr_str(source, "src").strip()
            if not src:
                continue
            absolute_url = normalize_url(absolutize_url(src, page_url))
            if absolute_url in seen:
                continue
            seen.add(absolute_url)
            vtype = detect_video_type(absolute_url)
            if not vtype:
                continue
            videos.append(
                VideoItem(
                    url=absolute_url,
                    source_page=page_url,
                    type=vtype,
                    page_title=page_title,
                    in_layout_container=False,
                )
            )
    return videos


def _extract_base64_iframe_videos(
    soup: BeautifulSoup,
    page_url: str,
    page_title: str,
) -> list[VideoItem]:
    """
    Base64IframeExtractor (inline) — decodes base64-encoded ``q`` parameters
    in embedded player iframes and extracts the hidden video source URL.

    Delegates to the ``Base64IframeExtractor`` plugin's ``extract_from_soup``
    method so extraction logic is maintained in a single place.
    """
    videos: list[VideoItem] = []
    try:
        from plugins.base64_iframe_extractor import Base64IframeExtractor
        result = Base64IframeExtractor().extract_from_soup(soup, page_url=page_url)
        for video_url in result.videos:
            absolute_url = normalize_url(absolutize_url(video_url, page_url))
            vtype = detect_video_type(absolute_url) or "direct"
            videos.append(
                VideoItem(
                    url=absolute_url,
                    source_page=page_url,
                    type=vtype,
                    page_title=page_title,
                    in_layout_container=False,
                )
            )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).debug("[_extract_base64_iframe_videos] Skipped: %s", exc)
    return videos


def _extract_video_objects_from_jsonld(
    soup: BeautifulSoup,
    page_url: str,
    page_title: str,
) -> list[VideoItem]:

    videos: list[VideoItem] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not isinstance(script, Tag):
            continue
        content = script.string or script.get_text(strip=True)
        if not content:
            continue
        try:
            payload = json.loads(content)
        except Exception:
            continue

        for item in _walk_json(payload):
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type")
            if not (
                item_type == "VideoObject"
                or (isinstance(item_type, list) and "VideoObject" in item_type)
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
        (re.compile(r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+"), "youtube"),
        (re.compile(r"https?://youtu\.be/[\w-]+"), "youtube"),
        (re.compile(r"https?://(?:www\.)?vimeo\.com/\d+"), "vimeo"),
        (DIRECT_VIDEO_PATTERN, "direct"),
        (HLS_PATTERN, "hls"),
        (DASH_PATTERN, "dash"),
    ]
    for tag in soup.find_all(["script", "p", "div", "span", "article", "section"]):
        if not isinstance(tag, Tag):
            continue
        text = tag.string or tag.get_text(" ", strip=True)
        if not text:
            continue
        for pattern, video_type in patterns:
            for match in pattern.findall(text):
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

    def __init__(
        self,
        domain_delays: dict[str, float] | None = None,
        proxy: str | None = None,
        proxy_list: str | None = None,
        captcha_provider: str | None = None,
        captcha_key: str | None = None,
        max_captcha_spend: float | None = None,
    ) -> None:
        self.http = HttpClient(domain_delays=domain_delays, proxy=proxy, proxy_list=proxy_list, captcha_provider=captcha_provider, captcha_key=captcha_key, max_captcha_spend=max_captcha_spend)
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
                if not isinstance(anchor, Tag):
                    continue
                href = self._extract_result_href(_get_attr_str(anchor, "href").strip())
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
            if not isinstance(form, Tag):
                continue
            action = _get_attr_str(form, "action")
            if "html" not in action.lower():
                continue
            params: dict[str, str] = {}
            for inp in form.find_all("input"):
                if not isinstance(inp, Tag):
                    continue
                name = _get_attr_str(inp, "name")
                val = _get_attr_str(inp, "value")
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
        if (parsed.netloc == "duckduckgo.com" or parsed.netloc.endswith(".duckduckgo.com")) and parsed.path.startswith("/l/"):
            return parse_qs(parsed.query).get("uddg", [""])[0]
        return href


def _is_in_layout_container(element: object) -> bool:
    if not isinstance(element, Tag):
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
        if not isinstance(parent, Tag):
            continue
        if parent.name in ("body", "html"):
            break
        if parent.name in ("footer", "header", "aside", "nav"):
            return True
        parent_class = parent.get("class")
        parent_id = _get_attr_str(parent, "id")

        tokens = set()
        if parent_id:
            tokens.update(re.split(r"[-_\s]+", parent_id.lower()))
        if parent_class:
            classes = parent_class if isinstance(parent_class, list) else [parent_class]
            for c in classes:
                c_str = c if isinstance(c, str) else str(c)
                tokens.update(re.split(r"[-_\s]+", c_str.lower()))

        if any(kw in tokens for kw in excluded_keywords):
            return True
    return False

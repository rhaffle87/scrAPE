from __future__ import annotations

import re
from urllib.parse import parse_qs, quote_plus, urlencode, urlparse
from typing import Any

from bs4 import BeautifulSoup, Tag

from config import (
    ALWAYS_BLOCK_DOMAINS,
    DISCOVERY_PATH_HINTS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
)
from core.filters import is_allowed_domain, is_allowed_path, is_http_url
from core.models import ImageItem, VideoItem
from core.parser import parse_html
from scraper.base import BaseSearchScraper
from scraper.video_scraper import extract_videos_from_html
from utils.http_client import HttpClient
from utils.logger import get_logger
from utils.robots import RobotsChecker

LOGGER = get_logger(__name__)


class SearchProviderScraper(BaseSearchScraper):
    # DuckDuckGo host variants that must bypass raw httpx and use browser stealth.
    _DDG_HOSTS = ("duckduckgo.com", "html.duckduckgo.com")

    def __init__(
        self, domain_delays: dict[str, float] | None = None, ignore_robots: bool = False
    ) -> None:
        self.http = HttpClient(domain_delays=domain_delays)
        self.robots = RobotsChecker(self.http, ignore_robots=ignore_robots)
        # Route all DuckDuckGo requests through browser stealth to avoid bot blocks.
        for ddg_host in self._DDG_HOSTS:
            HttpClient.register_stealth_required(ddg_host)

    def search_pages(
        self,
        keyword: str,
        max_results: int,
        allow_domains: list[str] | None = None,
        block_domains: list[str] | None = None,
    ) -> list[str]:
        allow_domains = allow_domains or []
        block_domains = block_domains or []
        # kp=-2 disables SafeSearch; browser stealth is already registered for DDG.
        search_url: str | None = (
            f"https://duckduckgo.com/html/?q={quote_plus(keyword)}&kp=-2"
        )
        links: list[str] = []
        visited: set[str] = set()

        while search_url and search_url not in visited:
            visited.add(search_url)
            LOGGER.info("Fetching search page: %s", search_url)
            try:
                response = self.http.get(search_url)
                soup = parse_html(response.text)
            except Exception as exc:
                LOGGER.warning("Search page fetch failed (%s): %s", search_url, exc)
                break

            anchors = soup.select("a.result__a") or soup.select("a[href]")
            page_count = 0
            for anchor in anchors:
                href = self._extract_result_href(anchor.get("href", "").strip())
                if not href or not is_http_url(href):
                    continue
                if not is_allowed_domain(href, allow_domains, block_domains):
                    continue
                if not is_allowed_path(href):
                    continue
                if href not in links:
                    links.append(href)
                    page_count += 1
                if max_results > 0 and len(links) >= max_results:
                    break

            LOGGER.info("Page yielded %d links (total: %d)", page_count, len(links))
            if max_results > 0 and len(links) >= max_results:
                break

            # Follow the next-page form (hidden inputs carry vqd/s/dc tokens).
            search_url = self._extract_next_page_url(soup)

        LOGGER.info("Search provider returned %s candidate pages total", len(links))
        return links

    def scrape_page(
        self,
        url: str,
        allow_domains: list[str] | None = None,
        block_domains: list[str] | None = None,
    ) -> tuple[list[ImageItem], list[VideoItem], str]:
        allow_domains = allow_domains or []
        block_domains = block_domains or []
        if not is_allowed_domain(url, allow_domains, block_domains):
            LOGGER.info("Skipping %s because it does not match domain rules", url)
            return [], [], "domain_blocked"
        if not is_allowed_path(url):
            LOGGER.info("Skipping %s because it is a structural path", url)
            return [], [], "structural_blocked"
        if not self.robots.is_allowed(url):
            LOGGER.info("Skipping %s because robots.txt disallows it", url)
            return [], [], "robots_blocked"

        try:
            response = self.http.get(url)
            content_type = response.headers.get("content-type", "").lower()
            if (
                "application/json" in content_type
                or url.endswith(".json")
                or "format=json" in url
            ):
                try:
                    data = response.json()
                    images, videos = self._extract_media_from_json(data, url)
                    return images, videos, "ok"
                except Exception as exc:
                    LOGGER.warning(
                        "Failed to parse JSON response from %s: %s", url, exc
                    )
                    return [], [], f"json_error:{type(exc).__name__}"

            soup = parse_html(response.text)
            page_title = self._extract_page_title(soup)
            images = self._extract_images(
                soup, url, page_title, allow_domains, block_domains
            )
            if not images:
                from core.semantic_selectors import extract_semantic_fallback_images

                images = extract_semantic_fallback_images(
                    soup, url, page_title, allow_domains, block_domains
                )
            videos = extract_videos_from_html(soup, url, page_title)
            return images, videos, "ok"
        except Exception as exc:
            exc_str = str(exc).lower()
            if "blacklisted" in exc_str or "cooldown" in exc_str:
                status_name = (
                    "fetch_error:blacklisted"
                    if "blacklisted" in exc_str
                    else "fetch_error:cooldown"
                )
                LOGGER.info(
                    "Skipping scrape of %s: domain is in blacklisted/cooldown state",
                    url,
                )
                return [], [], status_name

            LOGGER.warning("Failed to scrape %s: %s", url, exc)
            status_name = f"fetch_error:{type(exc).__name__}"
            if "429" in exc_str:
                status_name = "fetch_error:429"
            return [], [], status_name

    def _extract_page_links(self, soup: BeautifulSoup, page_url: str) -> list[str]:
        from core.filters import (
            absolutize_url,
            is_cdn_asset_domain,
            is_http_url,
            normalize_url,
            looks_like_media,
            is_allowed_path,
        )

        links: list[str] = []
        seen: set[str] = set()
        current_host = urlparse(page_url).netloc.lower()
        for element in soup.find_all(["a", "iframe", "embed", "link"]):
            href = element.get("href") or element.get("src") or element.get("data-href")
            if not href:
                continue
            absolute_url = normalize_url(absolutize_url(str(href).strip(), page_url))
            if not is_http_url(absolute_url):
                continue
            if not is_allowed_path(absolute_url):
                continue
            if looks_like_media(absolute_url):
                continue
            link_host = urlparse(absolute_url).netloc.lower()
            # Accept same-host links OR links to a known CDN domain that is associated
            # with the current seed domain (e.g. cdn.example.com when on example.com).
            if link_host != current_host and not is_cdn_asset_domain(absolute_url):
                continue
            if absolute_url in seen:
                continue
            seen.add(absolute_url)
            links.append(absolute_url)

        links.sort(key=self._link_priority)
        return links

    def discover_links(
        self,
        url: str,
        allow_domains: list[str] | None = None,
        block_domains: list[str] | None = None,
        keyword: str | None = None,
        entity_tokens: list[str] | None = None,
    ) -> list[str]:
        from core.filters import looks_like_media

        if looks_like_media(url):
            return []

        allow_domains = allow_domains or []
        block_domains = block_domains or []
        if not is_allowed_domain(url, allow_domains, block_domains):
            return []
        if not is_allowed_path(url):
            return []
        if not self.robots.is_allowed(url):
            return []

        try:
            response = self.http.get(url)
            if keyword:
                from core.filters import contains_subject_text

                if not contains_subject_text(response.text, keyword, entity_tokens):
                    LOGGER.info(
                        "Skipping link discovery on %s - no subject relevance", url
                    )
                    return []
            content_type = response.headers.get("content-type", "").lower()
            if (
                "application/json" in content_type
                or url.endswith(".json")
                or "format=json" in url
            ):
                try:
                    data = response.json()
                    links = []

                    from core.filters import absolutize_url, is_http_url, normalize_url

                    for val in self._walk_json(data):
                        if isinstance(val, str):
                            candidate = val.strip()
                            if (
                                is_http_url(candidate)
                                or candidate.startswith("/")
                                or candidate.startswith("./")
                                or candidate.startswith("../")
                            ):
                                try:
                                    absolute = normalize_url(
                                        absolutize_url(candidate, url)
                                    )
                                    if not absolute.lower().endswith(
                                        tuple(IMAGE_EXTENSIONS)
                                    ) and not absolute.lower().endswith(
                                        tuple(VIDEO_EXTENSIONS)
                                    ):
                                        links.append(absolute)
                                except Exception:
                                    pass
                    return [
                        link
                        for link in links
                        if is_allowed_domain(link, allow_domains, block_domains)
                        and is_allowed_path(link)
                    ]
                except Exception as exc:
                    LOGGER.warning(
                        "Failed to discover links from JSON in %s: %s", url, exc
                    )
                    return []

            soup = parse_html(response.text)
            links = self._extract_page_links(soup, url)
            return [
                link
                for link in links
                if is_allowed_domain(link, allow_domains, block_domains)
                and is_allowed_path(link)
            ]
        except Exception as exc:
            exc_str = str(exc).lower()
            if "blacklisted" in exc_str or "cooldown" in exc_str:
                LOGGER.info(
                    "Skipping link discovery on %s: domain is in blacklisted/cooldown state",
                    url,
                )
            else:
                LOGGER.warning("Failed to discover links from %s: %s", url, exc)
            return []

    def _extract_images(
        self,
        soup: Tag,
        page_url: str,
        page_title: str,
        allow_domains: list[str] | None = None,
        block_domains: list[str] | None = None,
    ) -> list[ImageItem]:
        from core.filters import (
            absolutize_url,
            clean_attr,
            extract_background_image,
            is_http_url,
            normalize_url,
        )

        images: list[ImageItem] = []
        allow_domains = allow_domains or []
        block_domains = block_domains or []

        for meta in soup.select("meta[property='og:image'], meta[name='og:image']"):
            content = meta.get("content", "").strip()
            if not content:
                continue
            absolute_url = normalize_url(absolutize_url(content, page_url))
            if not is_allowed_domain(
                absolute_url, allow_domains, [*block_domains, *ALWAYS_BLOCK_DOMAINS]
            ):
                continue
            images.append(
                ImageItem(
                    url=absolute_url,
                    source_page=page_url,
                    alt_text="",
                    page_title=page_title,
                )
            )

        for image in soup.find_all("img"):
            in_layout = self._is_in_layout_container(image)
            if in_layout:
                continue

            srcset_source = self._parse_srcset_highest_res(image.get("srcset", ""))
            source = (
                srcset_source
                or image.get("data-src")
                or image.get("data-original")
                or image.get("data-lazy-src")
                or image.get("src")
            )
            if not source:
                continue
            absolute_url = normalize_url(absolutize_url(source, page_url))
            if not is_http_url(absolute_url):
                continue
            if not is_allowed_domain(
                absolute_url, allow_domains, [*block_domains, *ALWAYS_BLOCK_DOMAINS]
            ):
                continue

            width = None
            height = None
            try:
                w_attr = image.get("width")
                if w_attr and str(w_attr).isdigit():
                    width = int(w_attr)
                h_attr = image.get("height")
                if h_attr and str(h_attr).isdigit():
                    height = int(h_attr)
            except Exception:
                pass

            parent_anchor = image.find_parent("a")
            parent_anchor_text = ""
            parent_anchor_href = ""
            if parent_anchor:
                parent_anchor_href = normalize_url(
                    absolutize_url(parent_anchor.get("href", "").strip(), page_url)
                )
                parent_anchor_text = clean_attr(
                    parent_anchor.get_text() or parent_anchor.get("title", "")
                )

            images.append(
                ImageItem(
                    url=absolute_url,
                    source_page=page_url,
                    alt_text=clean_attr(image.get("alt")),
                    page_title=page_title,
                    width=width,
                    height=height,
                    in_layout_container=in_layout,
                    parent_anchor_text=parent_anchor_text,
                    parent_anchor_href=parent_anchor_href,
                )
            )

        for element in soup.find_all(style=True):
            in_layout = self._is_in_layout_container(element)
            if in_layout:
                continue

            background_image = extract_background_image(element.get("style"))
            if not background_image:
                continue
            absolute_url = normalize_url(absolutize_url(background_image, page_url))
            if not is_http_url(absolute_url):
                continue
            if not is_allowed_domain(
                absolute_url, allow_domains, [*block_domains, *ALWAYS_BLOCK_DOMAINS]
            ):
                continue

            parent_anchor = element.find_parent("a")
            parent_anchor_text = ""
            parent_anchor_href = ""
            if parent_anchor:
                parent_anchor_href = normalize_url(
                    absolutize_url(parent_anchor.get("href", "").strip(), page_url)
                )
                parent_anchor_text = clean_attr(
                    parent_anchor.get_text() or parent_anchor.get("title", "")
                )

            images.append(
                ImageItem(
                    url=absolute_url,
                    source_page=page_url,
                    alt_text="",
                    page_title=page_title,
                    in_layout_container=in_layout,
                    parent_anchor_text=parent_anchor_text,
                    parent_anchor_href=parent_anchor_href,
                )
            )

        from core.filters import is_probable_image

        for anchor in soup.find_all("a"):
            href = anchor.get("href")
            if not href:
                continue
            absolute_url = normalize_url(absolutize_url(str(href).strip(), page_url))
            if not is_http_url(absolute_url):
                continue
            if is_probable_image(absolute_url):
                in_layout = self._is_in_layout_container(anchor)
                if in_layout:
                    continue
                if not is_allowed_domain(
                    absolute_url, allow_domains, [*block_domains, *ALWAYS_BLOCK_DOMAINS]
                ):
                    continue
                anchor_text = clean_attr(anchor.get_text() or anchor.get("title", ""))
                images.append(
                    ImageItem(
                        url=absolute_url,
                        source_page=page_url,
                        alt_text=anchor_text,
                        page_title=page_title,
                        in_layout_container=in_layout,
                    )
                )

        return images

    @staticmethod
    def _is_in_layout_container(element: Tag) -> bool:
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
                classes = (
                    parent_class if isinstance(parent_class, list) else [parent_class]
                )
                for c in classes:
                    tokens.update(re.split(r"[-_\s]+", str(c).lower()))

            if any(kw in tokens for kw in excluded_keywords):
                return True
        return False

    @staticmethod
    def _parse_srcset_highest_res(srcset: str) -> str | None:
        if not srcset:
            return None
        candidates = []
        for part in srcset.split(","):
            part = part.strip()
            if not part:
                continue
            parts = part.split()
            if not parts:
                continue
            url = parts[0]
            val = 1.0
            if len(parts) > 1:
                desc = parts[1].lower()
                if desc.endswith("w"):
                    try:
                        val = float(desc[:-1])
                    except ValueError:
                        pass
                elif desc.endswith("x"):
                    try:
                        val = float(desc[:-1]) * 1000.0
                    except ValueError:
                        pass
            candidates.append((url, val))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    @staticmethod
    def _walk_json(payload: Any) -> list[Any]:
        results = []
        todo = [payload]
        while todo:
            curr = todo.pop()
            if isinstance(curr, dict):
                todo.extend(curr.values())
            elif isinstance(curr, list):
                todo.extend(curr)
            else:
                results.append(curr)
        return results

    def _extract_media_from_json(
        self, data: Any, page_url: str
    ) -> tuple[list[ImageItem], list[VideoItem]]:
        from core.filters import (
            absolutize_url,
            is_http_url,
            is_probable_image,
            is_probable_video,
            normalize_url,
            is_thumbnail_url,
        )
        from scraper.video_scraper import detect_video_type

        images: list[ImageItem] = []
        videos: list[VideoItem] = []

        for value in self._walk_json(data):
            if isinstance(value, str):
                candidate = value.strip()
                if (
                    is_http_url(candidate)
                    or candidate.startswith("/")
                    or candidate.startswith("./")
                    or candidate.startswith("../")
                ):
                    try:
                        absolute = normalize_url(absolutize_url(candidate, page_url))
                        if is_probable_image(absolute) and not is_thumbnail_url(
                            absolute
                        ):
                            images.append(
                                ImageItem(
                                    url=absolute,
                                    source_page=page_url,
                                    alt_text="API Resource",
                                    page_title="JSON API Data",
                                )
                            )
                        elif is_probable_video(absolute):
                            videos.append(
                                VideoItem(
                                    url=absolute,
                                    source_page=page_url,
                                    type=detect_video_type(absolute) or "direct",
                                    page_title="JSON API Data",
                                )
                            )
                    except Exception:
                        pass
        return images, videos

    @staticmethod
    def _extract_page_title(soup: BeautifulSoup) -> str:
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        for meta in soup.select(
            "meta[property='og:title'], meta[name='title'], meta[name='twitter:title']"
        ):
            content = meta.get("content", "").strip()
            if content:
                return content
        return ""

    @staticmethod
    def _extract_next_page_url(soup: BeautifulSoup) -> str | None:
        """Parse the DuckDuckGo next-page form and return the next search URL.

        DDG's HTML endpoint includes a ``<form action="/html/">`` at the bottom
        of each results page with hidden fields (``q``, ``s``, ``vqd``, etc.).
        Extracting those inputs and building a GET URL lets us paginate without
        sessions or POST requests, and picks up any new token fields automatically.
        """
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
            # Only follow if real pagination params are present.
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

    @staticmethod
    def _link_priority(url: str) -> tuple[int, int, str]:
        lowered = url.lower()
        hint_score = 0 if any(hint in lowered for hint in DISCOVERY_PATH_HINTS) else 1
        return (hint_score, len(lowered), lowered)

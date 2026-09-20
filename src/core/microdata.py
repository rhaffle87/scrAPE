"""
microdata.py — JSON-LD structured data media extraction and smart pagination detection.
"""

from __future__ import annotations

import json
import re
from typing import Any, List, Tuple
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup

from core.models import ImageItem, VideoItem
from monitoring.logger import get_logger

LOGGER = get_logger(__name__)


def _safe_json_loads(text: str) -> Any:
    """Parse JSON safely, returning None on parse errors."""
    try:
        return json.loads(text)
    except Exception:
        # Handle unescaped characters or common malformed JSON
        try:
            cleaned = text.strip().replace("\r\n", " ").replace("\n", " ")
            return json.loads(cleaned)
        except Exception:
            return None


def extract_jsonld_media(
    html_or_soup: str | BeautifulSoup, base_url: str
) -> Tuple[List[ImageItem], List[VideoItem]]:
    """Extract ImageItem and VideoItem models from schema.org JSON-LD microdata scripts.

    Supported schemas: ImageObject, VideoObject, Product, Article, NewsArticle,
    Recipe, CreativeWork, and @graph collections.
    """
    if isinstance(html_or_soup, str):
        if "<script" not in html_or_soup:
            return [], []
        soup = BeautifulSoup(html_or_soup, "html.parser")
    else:
        soup = html_or_soup

    images: List[ImageItem] = []
    videos: List[VideoItem] = []
    seen_urls: set[str] = set()

    def _add_image(
        img_url: str,
        caption: str = "",
        width: int | None = None,
        height: int | None = None,
        candidates: list[dict[str, Any]] | None = None,
        fallbacks: list[str] | None = None,
    ):
        if not img_url:
            return
        abs_url = urljoin(base_url, img_url.strip())
        if not abs_url.startswith("http") or abs_url in seen_urls:
            return
        seen_urls.add(abs_url)
        cleaned_fallbacks = [
            urljoin(base_url, f.strip())
            for f in (fallbacks or [])
            if f and urljoin(base_url, f.strip()).startswith("http")
        ]
        images.append(
            ImageItem(
                url=abs_url,
                source_page=base_url,
                alt_text=caption or "",
                page_title=caption or "",
                width=width,
                height=height,
                fallback_urls=cleaned_fallbacks,
                candidates=candidates or [],
                extraction_source="json-ld",
            )
        )

    def _add_video(
        vid_url: str,
        title: str = "",
        thumb_url: str = "",
        fallbacks: list[str] | None = None,
    ):
        if not vid_url:
            return
        abs_url = urljoin(base_url, vid_url.strip())
        if not abs_url.startswith("http") or abs_url in seen_urls:
            return
        seen_urls.add(abs_url)
        cleaned_fallbacks = [
            urljoin(base_url, f.strip())
            for f in (fallbacks or [])
            if f and urljoin(base_url, f.strip()).startswith("http")
        ]
        if thumb_url and urljoin(base_url, thumb_url.strip()).startswith("http"):
            cleaned_fallbacks.append(urljoin(base_url, thumb_url.strip()))
        videos.append(
            VideoItem(
                url=abs_url,
                source_page=base_url,
                type="direct",
                page_title=title or "",
                fallback_urls=cleaned_fallbacks,
                extraction_source="json-ld",
            )
        )


    def _process_item(item: Any):
        if not isinstance(item, dict):
            return

        # Check @graph arrays
        if "@graph" in item and isinstance(item["@graph"], list):
            for child in item["@graph"]:
                _process_item(child)

        item_type = item.get("@type", "")
        if isinstance(item_type, list):
            item_type = item_type[0] if item_type else ""

        # 1. Direct ImageObject
        if item_type == "ImageObject":
            primary_url = item.get("contentUrl") or item.get("url")
            caption = item.get("caption") or item.get("name") or item.get("description") or ""
            w = item.get("width")
            h = item.get("height")
            w_val = int(w) if isinstance(w, (int, str)) and str(w).isdigit() else None
            h_val = int(h) if isinstance(h, (int, str)) and str(h).isdigit() else None
            _add_image(primary_url, caption=str(caption), width=w_val, height=h_val)

        # 2. Direct VideoObject
        elif item_type == "VideoObject":
            primary_url = item.get("contentUrl") or item.get("embedUrl") or item.get("url")
            title = item.get("name") or item.get("description") or ""
            thumb = item.get("thumbnailUrl")
            if isinstance(thumb, list) and thumb:
                thumb = thumb[0]
            _add_video(primary_url, title=str(title), thumb_url=str(thumb or ""))

        # 3. Items containing an 'image' field (Product, Article, etc.)
        if "image" in item:
            img_val = item["image"]
            if isinstance(img_val, str):
                _add_image(img_val, caption=str(item.get("name", "")))
            elif isinstance(img_val, list):
                first_url = None
                sub_fallbacks = []
                for sub in img_val:
                    if isinstance(sub, str):
                        u = sub
                    elif isinstance(sub, dict):
                        u = sub.get("contentUrl") or sub.get("url")
                    else:
                        u = None
                    if u:
                        if first_url is None:
                            first_url = u
                        else:
                            sub_fallbacks.append(u)
                if first_url:
                    _add_image(first_url, caption=str(item.get("name", "")), fallbacks=sub_fallbacks)
            elif isinstance(img_val, dict):
                _process_item(img_val)

        # 4. Items containing a 'video' field
        if "video" in item:
            vid_val = item["video"]
            if isinstance(vid_val, dict):
                _process_item(vid_val)
            elif isinstance(vid_val, list):
                for sub_v in vid_val:
                    if isinstance(sub_v, dict):
                        _process_item(sub_v)

    scripts = soup.find_all("script", type=re.compile(r"application/ld\+json", re.I))
    for script in scripts:
        raw_content = script.string or script.text
        if not raw_content or not raw_content.strip():
            continue
        parsed = _safe_json_loads(raw_content)
        if parsed is None:
            continue
        if isinstance(parsed, list):
            for entry in parsed:
                _process_item(entry)
        elif isinstance(parsed, dict):
            _process_item(parsed)

    return images, videos


def detect_smart_pagination(
    html_or_soup: str | BeautifulSoup, current_url: str
) -> List[str]:
    """Detect and infer next pagination links from HTML markup and query structure.

    Checks:
    1. <link rel="next" href="...">
    2. <a rel="next" href="...">
    3. Anchor elements matching next / pagination aria-labels and classes
    4. Query parameter stepping (?page=N -> ?page=N+1, ?p=N -> ?p=N+1, ?offset=N)
    """
    discovered: List[str] = []
    seen: set[str] = set()

    parsed_curr = urlparse(current_url)
    current_host = parsed_curr.netloc.lower()

    if isinstance(html_or_soup, str):
        soup = BeautifulSoup(html_or_soup, "html.parser")
    else:
        soup = html_or_soup

    def _try_add(candidate_url: str | None):
        if not candidate_url:
            return
        abs_url = urljoin(current_url, candidate_url.strip())
        parsed_cand = urlparse(abs_url)
        if parsed_cand.netloc.lower() != current_host:
            return
        if not abs_url.startswith("http"):
            return
        clean_url = abs_url.split("#")[0]
        if clean_url != current_url and clean_url not in seen:
            seen.add(clean_url)
            discovered.append(clean_url)

    # 1. <link rel="next"> in head
    for link_tag in soup.find_all("link", rel=lambda r: r and "next" in r):
        _try_add(link_tag.get("href"))

    # 2. <a rel="next">
    for a_tag in soup.find_all("a", rel=lambda r: r and "next" in r):
        _try_add(a_tag.get("href"))

    # 3. Anchor tags with pagination / next markers
    next_selectors = [
        "a.next",
        "a.pagination-next",
        "a.page-next",
        "a[aria-label*='Next']",
        "a[aria-label*='next']",
        "a[title*='Next']",
    ]
    for sel in next_selectors:
        for a_tag in soup.select(sel):
            _try_add(a_tag.get("href"))

    # 4. Infer numeric query parameter increment if no explicit markup next was found
    if not discovered:
        query_dict = parse_qs(parsed_curr.query)
        for param in ("page", "p", "paged", "pg"):
            if param in query_dict:
                try:
                    val = int(query_dict[param][0])
                    next_params = dict(query_dict)
                    next_params[param] = [str(val + 1)]
                    new_query = urlencode(next_params, doseq=True)
                    next_url = urlunparse(parsed_curr._replace(query=new_query))
                    _try_add(next_url)
                    break
                except (ValueError, IndexError):
                    pass

        # Check path pattern /page/N or /p/N
        match = re.search(r"/(page|p)/(\d+)", parsed_curr.path)
        if match:
            prefix, page_num = match.group(1), int(match.group(2))
            new_path = parsed_curr.path[: match.start()] + f"/{prefix}/{page_num + 1}" + parsed_curr.path[match.end() :]
            next_url = urlunparse(parsed_curr._replace(path=new_path))
            _try_add(next_url)

    return discovered

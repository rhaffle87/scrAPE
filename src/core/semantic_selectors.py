from __future__ import annotations

from bs4 import BeautifulSoup
from core.models import ImageItem, VideoItem
from core.filters import (
    absolutize_url,
    clean_attr,
    is_allowed_domain,
    is_http_url,
    normalize_url,
    is_probable_image,
    is_probable_video,
)
from utils.logger import get_logger

LOGGER = get_logger(__name__)

# List of semantic keywords often associated with main/gallery content
SEMANTIC_TARGET_KEYWORDS = {
    "gallery", "item", "media", "attachment", "detail", "content", "post", 
    "entry", "album", "photo", "pic", "player", "embed", "source", "main", 
    "wrapper", "container", "display", "viewer", "carousel", "slide"
}

def extract_semantic_fallback_images(
    soup: BeautifulSoup,
    page_url: str,
    page_title: str,
    allow_domains: list[str] | None = None,
    block_domains: list[str] | None = None,
) -> list[ImageItem]:
    """
    Scans the DOM for potential images using class/id/attributes with semantic fallback logic.
    Used when primary extraction yields zero or very few results.
    """
    allow_domains = allow_domains or []
    block_domains = block_domains or []
    extracted: list[ImageItem] = []
    seen_urls: set[str] = set()

    # Search every element for custom image attributes or href links
    for el in soup.find_all(True):
        # Calculate semantic score based on classes and IDs
        score = 0
        el_classes = el.get("class", [])
        if isinstance(el_classes, str):
            el_classes = [el_classes]
        el_id = el.get("id", "")
        
        # Check attributes and tag content
        text_to_check = " ".join([str(c) for c in el_classes] + [str(el_id), el.name])
        for kw in SEMANTIC_TARGET_KEYWORDS:
            if kw in text_to_check.lower():
                score += 10

        # Scan all attributes for image URLs, ignoring textual/structural attributes.
        # NOTE: 'title' MUST be excluded – sites like e-hentai use title="Page N: _N.jpg"
        # on div thumbnails; that value would otherwise be mistaken for a .jpg URL.
        for attr, val in el.attrs.items():
            if attr.lower() in {
                "alt",
                "title",
                "class",
                "id",
                "style",
                "width",
                "height",
                "onclick",
                "onload",
                "sizes",
                "rel",
                "target",
                "type",
                "media",
                "aria-label",
                "data-title",
                "data-alt",
            }:
                continue
            if not isinstance(val, str):
                continue
            val_stripped = val.strip()
            if not val_stripped:
                continue

            # If it's a HTTP URL or relative URL looking like an image
            if is_probable_image(val_stripped) or (len(val_stripped) > 4 and val_stripped.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))):
                try:
                    absolute_url = normalize_url(absolutize_url(val_stripped, page_url))
                    if not is_http_url(absolute_url):
                        continue
                    if not is_allowed_domain(absolute_url, allow_domains, block_domains):
                        continue
                    if absolute_url in seen_urls:
                        continue
                    
                    seen_urls.add(absolute_url)
                    parent_anchor = el.find_parent("a")
                    parent_anchor_href = ""
                    parent_anchor_text = ""
                    if parent_anchor:
                        parent_anchor_href = normalize_url(absolutize_url(parent_anchor.get("href", "").strip(), page_url))
                        parent_anchor_text = clean_attr(parent_anchor.get_text() or parent_anchor.get("title", ""))

                    extracted.append(
                        ImageItem(
                            url=absolute_url,
                            source_page=page_url,
                            alt_text=clean_attr(el.get("alt") or el.get("title") or ""),
                            page_title=page_title,
                            in_layout_container=False,
                            parent_anchor_text=parent_anchor_text,
                            parent_anchor_href=parent_anchor_href,
                        )
                    )
                except Exception:
                    pass

    return extracted

def extract_semantic_fallback_videos(
    soup: BeautifulSoup,
    page_url: str,
    page_title: str,
) -> list[VideoItem]:
    """
    Scans the DOM for potential videos using semantic classes/attributes when primary parsing yields zero results.
    """
    extracted: list[VideoItem] = []
    seen_urls: set[str] = set()

    # Search every element for custom video attributes or urls
    for el in soup.find_all(True):
        # Calculate semantic score based on classes and IDs
        score = 0
        el_classes = el.get("class", [])
        if isinstance(el_classes, str):
            el_classes = [el_classes]
        el_id = el.get("id", "")
        
        text_to_check = " ".join([str(c) for c in el_classes] + [str(el_id), el.name])
        for kw in SEMANTIC_TARGET_KEYWORDS:
            if kw in text_to_check.lower():
                score += 10

        # Scan attributes, ignoring textual/structural attributes.
        # NOTE: 'title' MUST be excluded – same reason as extract_semantic_fallback_images.
        for attr, val in el.attrs.items():
            if attr.lower() in {
                "alt",
                "title",
                "class",
                "id",
                "style",
                "width",
                "height",
                "onclick",
                "onload",
                "sizes",
                "rel",
                "target",
                "type",
                "media",
                "aria-label",
                "data-title",
                "data-alt",
            }:
                continue
            if not isinstance(val, str):
                continue
            val_stripped = val.strip()
            if not val_stripped:
                continue

            if is_probable_video(val_stripped) or (len(val_stripped) > 4 and val_stripped.lower().endswith((".mp4", ".webm", ".m3u8", ".mpd"))):
                try:
                    absolute_url = normalize_url(absolutize_url(val_stripped, page_url))
                    if not is_http_url(absolute_url):
                        continue
                    if absolute_url in seen_urls:
                        continue

                    seen_urls.add(absolute_url)
                    parent_anchor = el if el.name == "a" else el.find_parent("a")
                    parent_anchor_href = ""
                    parent_anchor_text = ""
                    if parent_anchor:
                        parent_anchor_href = normalize_url(absolutize_url(parent_anchor.get("href", "").strip(), page_url))
                        parent_anchor_text = clean_attr(parent_anchor.get_text() or parent_anchor.get("title", ""))

                    from scraper.video_scraper import detect_video_type
                    extracted.append(
                        VideoItem(
                            url=absolute_url,
                            source_page=page_url,
                            type=detect_video_type(absolute_url) or "direct",
                            page_title=page_title,
                            in_layout_container=False,
                            parent_anchor_text=parent_anchor_text,
                            parent_anchor_href=parent_anchor_href,
                        )
                    )
                except Exception:
                    pass

    return extracted

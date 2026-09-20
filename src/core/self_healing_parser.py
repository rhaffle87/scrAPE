"""Autonomous Multi-Tier Self-Healing DOM Parser for resilient media extraction across changing or obfuscated SPAs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import threading
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from core.models import ImageItem

LOGGER = logging.getLogger(__name__)


class SelfHealingDOMParser:
    """
    Multi-tier autonomous extraction parser:
      Tier 1: Cached previously repaired selectors from persistent SQLite store.
      Tier 2: Structural tree landmarks, container density clustering, and Schema.org / JSON-LD / OpenGraph microdata.
      Tier 3: Pluggable LLM-assisted selector synthesizer with validation and SQLite caching.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        enable_llm: bool = False,
        llm_provider: str = "ollama",
    ):
        self.db_path = Path(db_path or "output/cache/repaired_selectors.db")
        self.enable_llm = enable_llm or bool(os.getenv("ENABLE_LLM_HEALING", "0") in ("1", "true"))
        self.llm_provider = llm_provider
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS repaired_selectors (
                        domain TEXT PRIMARY KEY,
                        selector TEXT NOT NULL,
                        attr TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        updated_at TEXT NOT NULL,
                        hit_count INTEGER DEFAULT 1
                    )
                    """
                )
                conn.commit()

    def _get_domain(self, url: str) -> str:
        netloc = urlparse(url).netloc.lower()
        if ":" in netloc:
            netloc = netloc.split(":")[0]
        return netloc.lstrip("www.")

    def extract(
        self,
        soup: BeautifulSoup,
        page_url: str,
        page_title: str = "",
    ) -> list[ImageItem]:
        """
        Execute multi-tier self-healing extraction cascade.
        Returns list of extracted ImageItem assets.
        """
        domain = self._get_domain(page_url)
        items: list[ImageItem] = []

        # Tier 1: Cached Repaired Selector
        items = self._try_cached_selector(soup, domain, page_url, page_title)
        if items:
            LOGGER.info("Tier 1 self-healing cache hit for domain '%s' (%d items)", domain, len(items))
            return items

        # Tier 2: Structural & Microdata Heuristics
        items, candidate_sel, candidate_attr = self._extract_heuristics_and_microdata(soup, page_url, page_title)
        if items:
            LOGGER.info("Tier 2 structural/microdata recovery succeeded for '%s' (%d items)", domain, len(items))
            if candidate_sel:
                self.save_repaired_selector(domain, candidate_sel, candidate_attr, confidence=0.85)
            return items

        # Tier 3: Pluggable LLM Synthesizer (if enabled or available)
        if self.enable_llm:
            items = self._synthesize_with_llm(soup, domain, page_url, page_title)
            if items:
                LOGGER.info("Tier 3 LLM selector synthesis succeeded for '%s' (%d items)", domain, len(items))
                return items

        return []

    def _try_cached_selector(
        self, soup: BeautifulSoup, domain: str, page_url: str, page_title: str
    ) -> list[ImageItem]:
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT selector, attr, hit_count FROM repaired_selectors WHERE domain = ?",
                    (domain,),
                )
                row = cursor.fetchone()

        if not row:
            return []

        selector, attr, hits = row
        items: list[ImageItem] = []
        try:
            matched_tags = soup.select(selector)
            for tag in matched_tags:
                val = tag.get(attr) if isinstance(tag, Tag) else None
                if isinstance(val, str) and val.strip():
                    img_url = urljoin(page_url, val.strip())
                    items.append(
                        ImageItem(
                            url=img_url,
                            source_page=page_url,
                            page_title=page_title,
                            extraction_source=f"self_healing_cached:{selector}",
                        )
                    )

            if items:
                with self._lock:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute(
                            "UPDATE repaired_selectors SET hit_count = hit_count + 1, updated_at = ? WHERE domain = ?",
                            (datetime.now(timezone.utc).isoformat(), domain),
                        )
                        conn.commit()
        except Exception as e:
            LOGGER.warning("Failed evaluating cached selector '%s' for %s: %s", selector, domain, e)

        return items

    def _extract_heuristics_and_microdata(
        self, soup: BeautifulSoup, page_url: str, page_title: str
    ) -> tuple[list[ImageItem], str | None, str]:
        items: list[ImageItem] = []
        candidate_selector: str | None = None
        candidate_attr = "src"

        # A. Schema.org JSON-LD scripts
        for script in soup.find_all("script", type=lambda t: t and "ld+json" in t.lower()):
            try:
                data = json.loads(script.string or "{}")
                extracted_urls = self._parse_jsonld_for_images(data)
                for u in extracted_urls:
                    abs_url = urljoin(page_url, u)
                    items.append(
                        ImageItem(
                            url=abs_url,
                            source_page=page_url,
                            page_title=page_title,
                            extraction_source="self_healing_jsonld",
                        )
                    )
            except Exception:
                continue

        if items:
            return items, None, "src"

        # B. OpenGraph and Twitter Meta Tags
        for meta in soup.find_all("meta"):
            prop = meta.get("property", "").lower() or meta.get("name", "").lower()
            if prop in ("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"):
                content = meta.get("content")
                if content:
                    abs_url = urljoin(page_url, content.strip())
                    items.append(
                        ImageItem(
                            url=abs_url,
                            source_page=page_url,
                            page_title=page_title,
                            extraction_source="self_healing_meta",
                        )
                    )

        if items:
            return items, None, "content"

        # C. Structural Containers (<main>, <article>, <figure>, [role="feed"])
        container_selectors = [
            "main img",
            "article img",
            "figure img",
            "[role='feed'] img",
            "[role='main'] img",
            ".gallery img",
            ".media-container img",
        ]
        for sel in container_selectors:
            matched = soup.select(sel)
            if len(matched) >= 2:  # Found a repeating image layout
                for img in matched:
                    src = img.get("src") or img.get("data-src") or img.get("data-original")
                    if src and isinstance(src, str):
                        abs_url = urljoin(page_url, src.strip())
                        items.append(
                            ImageItem(
                                url=abs_url,
                                source_page=page_url,
                                page_title=page_title,
                                extraction_source=f"self_healing_structural:{sel}",
                            )
                        )
                if items:
                    candidate_selector = sel
                    candidate_attr = "src" if any(img.get("src") for img in matched) else "data-src"
                    return items, candidate_selector, candidate_attr

        return items, None, "src"

    def _parse_jsonld_for_images(self, data: Any) -> list[str]:
        urls = []
        if isinstance(data, dict):
            if data.get("@type") in ("ImageObject", "MediaObject") and "contentUrl" in data:
                urls.append(str(data["contentUrl"]))
            if "image" in data:
                val = data["image"]
                if isinstance(val, str):
                    urls.append(val)
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, str):
                            urls.append(item)
                        elif isinstance(item, dict) and "url" in item:
                            urls.append(str(item["url"]))
            for v in data.values():
                urls.extend(self._parse_jsonld_for_images(v))
        elif isinstance(data, list):
            for elem in data:
                urls.extend(self._parse_jsonld_for_images(elem))
        return urls

    def _synthesize_with_llm(
        self, soup: BeautifulSoup, domain: str, page_url: str, page_title: str
    ) -> list[ImageItem]:
        """Synthesize selector using compact DOM snippet and LLM inference."""
        # Sanitize DOM snippet
        clone = BeautifulSoup(str(soup), "html.parser")
        for tag in clone(["script", "style", "svg", "noscript", "iframe"]):
            tag.decompose()

        dom_sample = str(clone.body or clone)[:3500]
        prompt = (
            f"Given the following HTML DOM snippet from {domain}, identify the CSS selector "
            "and attribute that targets the primary content images. Return strictly JSON in this format: "
            '{"selector": "...", "attribute": "src"}\n\n'
            f"HTML Snippet:\n{dom_sample}"
        )

        try:
            response_text = self._call_llm(prompt)
            match = re.search(r"\{.*?\}", response_text, re.DOTALL)
            if match:
                payload = json.loads(match.group(0))
                selector = payload.get("selector")
                attr = payload.get("attribute", "src")
                if selector:
                    matched = soup.select(selector)
                    items = []
                    for t in matched:
                        v = t.get(attr) if isinstance(t, Tag) else None
                        if v and isinstance(v, str):
                            items.append(
                                ImageItem(
                                    url=urljoin(page_url, v.strip()),
                                    source_page=page_url,
                                    page_title=page_title,
                                    extraction_source=f"self_healing_llm:{selector}",
                                )
                            )
                    if items:
                        self.save_repaired_selector(domain, selector, attr, confidence=0.9)
                        return items
        except Exception as e:
            LOGGER.warning("LLM synthesis failed for %s: %s", domain, e)

        return []

    def _call_llm(self, prompt: str) -> str:
        """Call configured LLM with automatic tiered fallback (Ollama -> Gemini -> OpenAI/Compatible)."""
        import httpx

        # 1. Try Ollama (local, private, zero-cost)
        if self.llm_provider in ("ollama", "auto"):
            try:
                url = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/generate"
                res = httpx.post(url, json={"model": os.getenv("OLLAMA_MODEL", "llama3"), "prompt": prompt, "stream": False}, timeout=10.0)
                if res.status_code == 200:
                    return res.json().get("response", "")
            except Exception as e:
                LOGGER.debug("Ollama provider failed or offline: %s", e)
                if self.llm_provider == "ollama":
                    raise

        # 2. Try Google Gemini Flash
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        if gemini_key and self.llm_provider in ("gemini", "auto"):
            try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                body = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 200},
                }
                res = httpx.post(endpoint, json=body, timeout=8.0)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
            except Exception as e:
                LOGGER.debug("Gemini provider failed: %s", e)
                if self.llm_provider == "gemini":
                    raise

        # 3. Try OpenAI or OpenAI-compatible endpoint (LM Studio, vLLM, LocalAI)
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        if (openai_key or "localhost" in base_url or "127.0.0.1" in base_url) and self.llm_provider in ("openai", "auto"):
            try:
                headers = {"Authorization": f"Bearer {openai_key or 'sk-no-key'}"}
                payload = {
                    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 200,
                }
                res = httpx.post(f"{base_url}/chat/completions", json=payload, headers=headers, timeout=8.0)
                if res.status_code == 200:
                    choices = res.json().get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
            except Exception as e:
                LOGGER.debug("OpenAI/compatible provider failed: %s", e)
                if self.llm_provider == "openai":
                    raise

        raise RuntimeError(f"All configured LLM providers failed or are unreachable (provider={self.llm_provider})")

    def save_repaired_selector(
        self, domain: str, selector: str, attr: str = "src", confidence: float = 1.0
    ) -> None:
        """Persist newly validated repair rule into SQLite."""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO repaired_selectors (domain, selector, attr, confidence, updated_at, hit_count)
                    VALUES (?, ?, ?, ?, ?, 1)
                    ON CONFLICT(domain) DO UPDATE SET
                        selector = excluded.selector,
                        attr = excluded.attr,
                        confidence = excluded.confidence,
                        updated_at = excluded.updated_at,
                        hit_count = repaired_selectors.hit_count + 1
                    """,
                    (domain, selector, attr, confidence, datetime.now(timezone.utc).isoformat()),
                )
                conn.commit()
            LOGGER.info("Saved repaired rule for domain '%s' -> %s[%s]", domain, selector, attr)

from __future__ import annotations

from abc import ABC, abstractmethod

from core.models import ImageItem, VideoItem

class BaseSearchScraper(ABC):
    @abstractmethod
    def search_pages(
        self,
        keyword: str,
        max_results: int,
        allow_domains: list[str] | None = None,
        block_domains: list[str] | None = None,
    ) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def scrape_page(
        self,
        url: str,
        allow_domains: list[str] | None = None,
        block_domains: list[str] | None = None,
    ) -> tuple[list[ImageItem], list[VideoItem], str]:
        raise NotImplementedError
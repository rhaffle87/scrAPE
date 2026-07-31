from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional
from plugins.base import ExtractorPlugin, SpecializedResult, PluginRegistry

if TYPE_CHECKING:
    from network.http_client import HttpClient

LOGGER = logging.getLogger(__name__)

__all__ = ["SpecializedResult", "SpecializedExtractor"]


class SpecializedExtractor:
    """Handles deep extraction for platforms that block or complicate traditional DOM scraping.
    Delegates all plugin management, priority ordering, and caching to PluginRegistry.
    """

    @classmethod
    def is_supported(cls, url: str) -> bool:
        return PluginRegistry.get_instance().is_supported(url)

    @classmethod
    def extract(cls, url: str, http_client: Optional['HttpClient'] = None) -> SpecializedResult:
        return PluginRegistry.get_instance().extract(url, http_client)

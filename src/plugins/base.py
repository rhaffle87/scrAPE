from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

@dataclass
class SpecializedResult:
    images: List[str]
    videos: List[str]

class ExtractorPlugin(ABC):
    """Base interface for specialized media extractors."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this plugin can extract media from the given URL."""
        pass

    @abstractmethod
    def extract(self, url: str) -> SpecializedResult:
        """Extract media from the given URL."""
        pass

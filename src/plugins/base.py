from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
import importlib
import inspect
import logging
import pkgutil
import threading
from urllib.parse import urlparse

LOGGER = logging.getLogger(__name__)


@dataclass
class SpecializedResult:
    images: List[str]
    videos: List[str]


class ExtractorPlugin(ABC):
    """Base interface for specialized media extractors."""

    priority: int = 100
    name: str = ""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this plugin can extract media from the given URL."""
        pass

    @abstractmethod
    def extract(self, url: str) -> SpecializedResult:
        """Extract media from the given URL."""
        pass


class PluginRegistry:
    """Thread-safe registry managing priority-ordered ExtractorPlugin instances."""

    _instance: Optional[PluginRegistry] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._plugins: List[ExtractorPlugin] = []
        self._domain_cache: Dict[str, Optional[ExtractorPlugin]] = {}
        self._registry_lock = threading.Lock()
        self._loaded = False

    @classmethod
    def get_instance(cls) -> PluginRegistry:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                cls._instance.discover_plugins()
            return cls._instance

    def discover_plugins(self) -> None:
        with self._registry_lock:
            if self._loaded:
                return

            import plugins

            discovered = []
            for _, name, _ in pkgutil.iter_modules(plugins.__path__, plugins.__name__ + "."):
                try:
                    module = importlib.import_module(name)
                    for item_name, item in inspect.getmembers(module, inspect.isclass):
                        if issubclass(item, ExtractorPlugin) and item is not ExtractorPlugin:
                            instance = item()
                            if not instance.name:
                                instance.name = item_name
                            discovered.append(instance)
                except Exception as e:
                    LOGGER.error("Failed to load plugin module %s: %s", name, e)

            # Sort by priority ascending (lower priority number = higher precedence)
            discovered.sort(key=lambda p: getattr(p, "priority", 100))
            self._plugins = discovered
            self._domain_cache.clear()
            self._loaded = True

    def register(self, plugin: ExtractorPlugin) -> None:
        with self._registry_lock:
            if not plugin.name:
                plugin.name = plugin.__class__.__name__
            self._plugins = [p for p in self._plugins if p.name != plugin.name]
            self._plugins.append(plugin)
            self._plugins.sort(key=lambda p: getattr(p, "priority", 100))
            self._domain_cache.clear()

    def unregister(self, plugin_name: str) -> None:
        with self._registry_lock:
            self._plugins = [p for p in self._plugins if p.name != plugin_name]
            self._domain_cache.clear()

    def get_plugin_for_url(self, url: str) -> Optional[ExtractorPlugin]:
        host = urlparse(url).netloc.lower()
        with self._registry_lock:
            if host in self._domain_cache:
                cached = self._domain_cache[host]
                if cached is not None and cached.can_handle(url):
                    return cached

            for plugin in self._plugins:
                if plugin.can_handle(url):
                    if host:
                        self._domain_cache[host] = plugin
                    return plugin

            if host:
                self._domain_cache[host] = None
            return None

    def is_supported(self, url: str) -> bool:
        return self.get_plugin_for_url(url) is not None

    def extract(self, url: str) -> SpecializedResult:
        plugin = self.get_plugin_for_url(url)
        if plugin is None:
            return SpecializedResult([], [])

        try:
            return plugin.extract(url)
        except Exception as e:
            LOGGER.warning("Plugin '%s' failed during extraction for %s: %s", plugin.name, url, e)
            return SpecializedResult([], [])

import importlib
import inspect
import logging
import pkgutil
from plugins.base import ExtractorPlugin, SpecializedResult
import plugins

LOGGER = logging.getLogger(__name__)

# Keep for backwards compatibility if anyone imports it directly from here
__all__ = ["SpecializedResult", "SpecializedExtractor"]

class SpecializedExtractor:
    """Handles deep extraction for platforms that block or complicate traditional DOM scraping.
    Now uses a dynamic plugin architecture.
    """

    _plugins = []
    _loaded = False

    @classmethod
    def _load_plugins(cls):
        if cls._loaded:
            return
        
        cls._plugins = []
        for _, name, is_pkg in pkgutil.iter_modules(plugins.__path__, plugins.__name__ + "."):
            try:
                module = importlib.import_module(name)
                for item_name, item in inspect.getmembers(module, inspect.isclass):
                    if issubclass(item, ExtractorPlugin) and item is not ExtractorPlugin:
                        cls._plugins.append(item())
            except Exception as e:
                LOGGER.error("Failed to load plugin module %s: %s", name, e)
        cls._loaded = True

    @classmethod
    def is_supported(cls, url: str) -> bool:
        cls._load_plugins()
        for plugin in cls._plugins:
            if plugin.can_handle(url):
                return True
        return False

    @classmethod
    def extract(cls, url: str) -> SpecializedResult:
        cls._load_plugins()
        for plugin in cls._plugins:
            if plugin.can_handle(url):
                return plugin.extract(url)
        return SpecializedResult([], [])

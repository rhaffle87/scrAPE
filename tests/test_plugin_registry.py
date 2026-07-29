from __future__ import annotations

import pytest
from plugins.base import ExtractorPlugin, PluginRegistry, SpecializedResult
from scraper.specialized import SpecializedExtractor


class HighPriorityPlugin(ExtractorPlugin):
    priority = 10
    name = "high_priority_test"

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        netloc = urlparse(url).netloc
        return netloc == "testdomain.org" or netloc.endswith(".testdomain.org")

    def extract(self, url: str) -> SpecializedResult:
        return SpecializedResult(images=["https://testdomain.org/high.jpg"], videos=[])


class LowPriorityPlugin(ExtractorPlugin):
    priority = 100
    name = "low_priority_test"

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        netloc = urlparse(url).netloc
        return netloc == "testdomain.org" or netloc.endswith(".testdomain.org")

    def extract(self, url: str) -> SpecializedResult:
        return SpecializedResult(images=["https://testdomain.org/low.jpg"], videos=[])


class FailingPlugin(ExtractorPlugin):
    priority = 5
    name = "failing_test"

    def can_handle(self, url: str) -> bool:
        from urllib.parse import urlparse
        netloc = urlparse(url).netloc
        return netloc == "faildomain.org" or netloc.endswith(".faildomain.org")

    def extract(self, url: str) -> SpecializedResult:
        raise RuntimeError("Simulated plugin extraction crash")


def test_plugin_registry_priority_sorting_and_dynamic_registration():
    registry = PluginRegistry.get_instance()

    high_p = HighPriorityPlugin()
    low_p = LowPriorityPlugin()

    registry.register(low_p)
    registry.register(high_p)

    selected = registry.get_plugin_for_url("https://testdomain.org/post/1")
    assert selected is not None
    assert selected.name == "high_priority_test"

    res = registry.extract("https://testdomain.org/post/1")
    assert res.images == ["https://testdomain.org/high.jpg"]

    # Clean up test plugins
    registry.unregister("high_priority_test")
    registry.unregister("low_priority_test")


def test_plugin_registry_graceful_error_isolation():
    registry = PluginRegistry.get_instance()
    fail_p = FailingPlugin()
    registry.register(fail_p)

    assert registry.is_supported("https://faildomain.org/post/1") is True
    res = registry.extract("https://faildomain.org/post/1")
    assert res.images == []
    assert res.videos == []

    registry.unregister("failing_test")


def test_specialized_extractor_proxy_compatibility():
    # Verify backward compatible calls via SpecializedExtractor
    assert isinstance(SpecializedExtractor.is_supported("https://youtube.com/watch?v=123"), bool)
    res = SpecializedExtractor.extract("https://nonexistent-site-12345.com/post")
    assert res.images == []
    assert res.videos == []

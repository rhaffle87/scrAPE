from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
import pytest

from core.managers import DomainRulesManager
from core.engine import ScrapingEngine
from bs4 import BeautifulSoup


def test_domain_rules_manager_caching_and_mtime_reload(tmp_path):
    config_file = tmp_path / "domain_config.json"
    profile_file = tmp_path / "subject_profiles.json"

    initial_config = {
        "deep_scrape": ["example.com"],
        "domain_handlers": {
            "example.com": {"link_pattern": "/article/"}
        }
    }
    initial_profiles = {
        "test_profile": {"block_image_only_domains": ["blocked.com"]}
    }

    config_file.write_text(json.dumps(initial_config), encoding="utf-8")
    profile_file.write_text(json.dumps(initial_profiles), encoding="utf-8")

    mgr = DomainRulesManager(config_path=str(config_file), profile_path=str(profile_file))

    # Initial load
    assert mgr.should_deep_scrape("example.com") is True
    assert mgr.should_deep_scrape("other.com") is False
    assert mgr.filter_domains_by_profile(["allowed.com", "blocked.com"], "test_profile") == ["allowed.com"]

    soup = BeautifulSoup('<a href="/article/123">link</a><a href="/other/456">other</a>', "html.parser")
    links = mgr.handle_domain_links(soup, "example.com")
    assert links == ["/article/123"]

    # Verify cache mtimes are set
    assert mgr._config_mtime is not None
    assert mgr._profile_mtime is not None

    # Wait briefly to ensure mtime changes on disk
    time.sleep(0.05)

    # Mutate files on disk
    updated_config = {
        "deep_scrape": ["example.com", "newdeep.com"],
        "domain_handlers": {
            "example.com": {"link_pattern": "/post/"}
        }
    }
    updated_profiles = {
        "test_profile": {"block_image_only_domains": ["newblocked.com"]}
    }

    config_file.write_text(json.dumps(updated_config), encoding="utf-8")
    profile_file.write_text(json.dumps(updated_profiles), encoding="utf-8")

    # Access methods again — should auto-reload because mtime changed
    assert mgr.should_deep_scrape("newdeep.com") is True
    assert mgr.filter_domains_by_profile(["allowed.com", "newblocked.com"], "test_profile") == ["allowed.com"]

    soup_post = BeautifulSoup('<a href="/post/789">post link</a>', "html.parser")
    links_post = mgr.handle_domain_links(soup_post, "example.com")
    assert links_post == ["/post/789"]


def test_domain_rules_manager_thread_safety(tmp_path):
    config_file = tmp_path / "domain_config.json"
    profile_file = tmp_path / "subject_profiles.json"

    config_file.write_text(json.dumps({"deep_scrape": ["threadtest.com"]}), encoding="utf-8")
    profile_file.write_text(json.dumps({"p1": {"block_image_only_domains": ["bad.com"]}}), encoding="utf-8")

    mgr = DomainRulesManager(config_path=str(config_file), profile_path=str(profile_file))

    def worker():
        for _ in range(100):
            res1 = mgr.should_deep_scrape("threadtest.com")
            res2 = mgr.filter_domains_by_profile(["good.com", "bad.com"], "p1")
            assert res1 is True
            assert res2 == ["good.com"]

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker) for _ in range(8)]
        for f in futures:
            f.result()


def test_scraping_engine_proxy_delegation():
    engine = ScrapingEngine()
    assert hasattr(engine, "rules_manager")
    assert isinstance(engine.rules_manager, DomainRulesManager)

    # Verify delegation works cleanly
    res_deep = engine.should_deep_scrape("nonexistent-domain-12345.com")
    assert isinstance(res_deep, bool)

    res_filter = engine.filter_domains_by_profile(["domain1.com"], "nonexistent_profile")
    assert res_filter == ["domain1.com"]

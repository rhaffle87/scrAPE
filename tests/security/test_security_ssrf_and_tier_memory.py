"""
Unit tests for SSRF redirect hop validation, DNS rebinding defenses, credential scrubbing,
3-step path resolution, and DomainTierMemory caching.
"""

import httpx
import pytest
from common.security import (
    is_safe_target_url,
    sanitize_url_credentials,
    validate_safe_path,
    sanitize_filename,
)
from network.http_client import HttpClient, ScraperBypassError


def test_ssrf_validation_comprehensive(monkeypatch):
    monkeypatch.delenv("SCRAPE_ALLOW_LOCAL_TARGETS", raising=False)
    # Direct loopback and private IPs
    assert not is_safe_target_url("http://127.0.0.1:8000/test")
    assert not is_safe_target_url("http://localhost:3000/")
    assert not is_safe_target_url("http://169.254.169.254/latest/meta-data")
    assert not is_safe_target_url("http://10.0.0.5/api")
    assert not is_safe_target_url("http://192.168.1.100/")
    assert not is_safe_target_url("http://172.16.0.1/")
    assert not is_safe_target_url("http://0.0.0.0/")
    assert not is_safe_target_url("http://metadata.google.internal/")
    assert not is_safe_target_url("http://instance-data/")

    # Decimal-encoded IP (2130706433 == 127.0.0.1)
    assert not is_safe_target_url("http://2130706433/")

    # Non-http schemes
    assert not is_safe_target_url("file:///etc/passwd")
    assert not is_safe_target_url("gopher://127.0.0.1:70")
    assert not is_safe_target_url("ftp://internal.server/")

    # Valid public targets
    assert is_safe_target_url("https://example.com/page")
    assert is_safe_target_url("https://news.ycombinator.com/")


def test_credential_sanitization():
    raw_redis = "redis://:supersecretpassword@10.0.0.5:6379/0"
    clean_redis = sanitize_url_credentials(raw_redis)
    assert "supersecretpassword" not in clean_redis
    assert ":***@" in clean_redis

    raw_userpass = "redis://admin:mypassword@cache.cluster.internal:6379/1"
    clean_userpass = sanitize_url_credentials(raw_userpass)
    assert "mypassword" not in clean_userpass
    assert "admin:***@" in clean_userpass


def test_validate_safe_path_and_filename(tmp_path):
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    # Valid child path
    child = base_dir / "subdir" / "file.txt"
    resolved = validate_safe_path(base_dir, child)
    assert str(resolved).startswith(str(base_dir))

    # Path traversal outside base_dir
    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_safe_path(base_dir, base_dir / ".." / "evil.txt")

    # Filename sanitization
    assert sanitize_filename("../../etc/passwd") == "etc_passwd"
    assert sanitize_filename("my-photo_01.jpg") == "my-photo_01.jpg"


def test_ssrf_redirect_hop_validation():
    # Mock redirect response with unsafe Location header
    req = httpx.Request("GET", "https://public-site.com/redirect")
    resp = httpx.Response(
        status_code=302,
        headers={"Location": "http://169.254.169.254/latest/meta-data"},
        request=req,
    )

    with pytest.raises(ScraperBypassError, match="SSRF blocked redirect hop"):
        HttpClient._validate_redirect_hook(resp)

    # Relative safe redirect should pass
    safe_resp = httpx.Response(
        status_code=301,
        headers={"Location": "/next-page"},
        request=req,
    )
    # Should not raise
    HttpClient._validate_redirect_hook(safe_resp)


def test_domain_tier_memory_lifecycle():
    domain = "protected-waf-target.org"
    # Ensure clean slate
    HttpClient.evict_domain_tier(domain)
    assert HttpClient.get_domain_tier(domain) is None

    # Record successful tier
    HttpClient.record_domain_tier(domain, "curl_cffi")
    assert HttpClient.get_domain_tier(domain) == "curl_cffi"

    # Verify domain is automatically registered in stealth hosts
    assert domain in HttpClient._stealth_required_hosts
    assert HttpClient._preferred_engine_by_host.get(domain) == "curl_cffi"

    # Evict on failure
    HttpClient.evict_domain_tier(domain)
    assert HttpClient.get_domain_tier(domain) is None

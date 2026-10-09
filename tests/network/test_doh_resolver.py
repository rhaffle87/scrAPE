"""
test_doh_resolver.py — Unit tests for DoHResolver transparent DNS-over-HTTPS anti-poisoning.
"""

import socket
from unittest.mock import MagicMock, patch

from network.doh_resolver import KNOWN_CENSORSHIP_IPS, DoHResolver


def test_doh_resolver_singleton():
    r1 = DoHResolver.get_instance()
    r2 = DoHResolver.get_instance()
    assert r1 is r2
    assert DoHResolver.get_doh_url() == "https://1.1.1.1/dns-query"


def test_is_poisoned_ip():
    assert DoHResolver.is_poisoned_ip("202.3.218.139") is True
    assert DoHResolver.is_poisoned_ip("118.98.115.11") is True
    assert DoHResolver.is_poisoned_ip("127.0.0.1") is True
    assert DoHResolver.is_poisoned_ip("::1") is True
    assert DoHResolver.is_poisoned_ip("104.21.71.8") is False
    assert DoHResolver.is_poisoned_ip("1.1.1.1") is False


def test_query_doh_caching_and_resolution():
    resolver = DoHResolver()

    # Mock urllib response for DoH
    mock_payload = b'{"Status": 0, "Answer": [{"name": "example.com", "type": 1, "data": "93.184.216.34"}]}'
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = mock_payload
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        ips = resolver.query_doh("example.com")
        assert ips == ["93.184.216.34"]

        # Cache hit test: urlopen should not be called again
        with patch("urllib.request.urlopen") as mock_fail:
            cached_ips = resolver.query_doh("example.com")
            assert cached_ips == ["93.184.216.34"]
            mock_fail.assert_not_called()


def test_smart_getaddrinfo_intercepts_poisoned_dns():
    resolver = DoHResolver()

    # Simulate system DNS returning Telkom censorship IP
    orig_gai = MagicMock(
        return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("202.3.218.139", 443))
        ]
    )
    resolver._orig_getaddrinfo = orig_gai

    with patch.object(resolver, "query_doh", return_value=["104.21.71.8"]):
        res = resolver.smart_getaddrinfo("rule34.world", 443)
        assert len(res) == 1
        assert res[0][4] == ("104.21.71.8", 443)


def test_smart_getaddrinfo_passes_unpoisoned_clean_dns():
    resolver = DoHResolver()

    orig_gai = MagicMock(
        return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]
    )
    resolver._orig_getaddrinfo = orig_gai

    with patch.object(resolver, "query_doh") as mock_doh:
        res = resolver.smart_getaddrinfo("example.com", 443)
        assert len(res) == 1
        assert res[0][4] == ("93.184.216.34", 443)
        mock_doh.assert_not_called()


def test_install_and_uninstall_lifecycle():
    resolver = DoHResolver()
    orig = socket.getaddrinfo

    resolver.install()
    assert socket.getaddrinfo == resolver.smart_getaddrinfo
    assert resolver._installed is True

    resolver.uninstall()
    assert socket.getaddrinfo == orig
    assert resolver._installed is False

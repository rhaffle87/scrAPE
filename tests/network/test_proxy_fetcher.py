import pytest
from unittest.mock import patch, MagicMock

from network.proxy_fetcher import ProxyFetcher


@pytest.fixture
def mock_httpx_get():
    with patch("httpx.AsyncClient.get") as mock_get:
        yield mock_get


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_fetch_proxyscrape(mock_httpx_get):
    mock_resp = MagicMock()
    mock_resp.text = "http://1.2.3.4:80\nsocks5://5.6.7.8:1080\ninvalid_line"
    mock_httpx_get.return_value = mock_resp

    fetcher = ProxyFetcher()
    proxies = await fetcher.fetch_proxyscrape()
    assert "http://1.2.3.4:80" in proxies
    assert "socks5://5.6.7.8:1080" in proxies
    assert len(proxies) == 2


@pytest.mark.anyio
async def test_fetch_geonode(mock_httpx_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": [
            {"ip": "8.8.8.8", "port": "80", "protocols": ["http"]},
            {"ip": "9.9.9.9", "port": "1080", "protocols": ["socks5", "http"]},
        ]
    }
    mock_httpx_get.return_value = mock_resp

    fetcher = ProxyFetcher()
    proxies = await fetcher.fetch_geonode()
    assert "http://8.8.8.8:80" in proxies
    assert "socks5://9.9.9.9:1080" in proxies
    assert len(proxies) == 2


@pytest.mark.anyio
async def test_get_real_ip(mock_httpx_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"ip": "1.2.3.4"}
    mock_httpx_get.return_value = mock_resp

    fetcher = ProxyFetcher()
    ip = await fetcher._get_real_ip()
    assert ip == "1.2.3.4"
    assert fetcher.real_ip == "1.2.3.4"

    # Should use cached IP on second call
    mock_httpx_get.reset_mock()
    ip2 = await fetcher._get_real_ip()
    assert ip2 == "1.2.3.4"
    mock_httpx_get.assert_not_called()


@pytest.mark.anyio
async def test_validate_proxy_success(mock_httpx_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"ip": "9.9.9.9"}
    mock_httpx_get.return_value = mock_resp

    fetcher = ProxyFetcher()
    fetcher.real_ip = "1.2.3.4"  # Mock real IP

    # The proxy returns an IP (9.9.9.9) that is NOT our real IP (1.2.3.4), so it's valid
    valid_proxy = await fetcher._validate_proxy("http://proxy.com:80")
    assert valid_proxy == "http://proxy.com:80"


@pytest.mark.anyio
async def test_validate_proxy_transparent(mock_httpx_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"ip": "1.2.3.4"}
    mock_httpx_get.return_value = mock_resp

    fetcher = ProxyFetcher()
    fetcher.real_ip = "1.2.3.4"

    # The proxy returns our real IP, indicating it's transparent/leaking
    valid_proxy = await fetcher._validate_proxy("http://proxy.com:80")
    assert valid_proxy is None


@pytest.mark.anyio
async def test_validate_proxy_socks4_skipped():
    fetcher = ProxyFetcher()
    # socks4 should be skipped immediately without httpx call
    valid_proxy = await fetcher._validate_proxy("socks4://proxy.com:80")
    assert valid_proxy is None

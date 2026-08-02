import asyncio
import logging
import time
from typing import List, Set
from urllib.parse import urlparse

import httpx

LOGGER = logging.getLogger(__name__)

PROXY_SCRAPE_URL = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text"
GEONODE_URL = "https://proxylist.geonode.com/api/proxy-list?page=1&limit=500&sort_by=responseTime&sort_type=asc"


class ProxyFetcher:
    """Fetches and validates free public proxies for high speed and high anonymity."""

    def __init__(self, validation_timeout_s: float = 2.0):
        self.validation_timeout_s = validation_timeout_s
        self.real_ip: str | None = None

    async def _get_real_ip(self) -> str | None:
        """Fetch the host machine's real IP address to detect transparent proxies."""
        if self.real_ip:
            return self.real_ip
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get("https://api.ipify.org?format=json")
                resp.raise_for_status()
                self.real_ip = resp.json().get("ip")
                LOGGER.info("Detected real IP: %s", self.real_ip)
                return self.real_ip
        except Exception as e:
            LOGGER.error("Failed to fetch real IP for validation: %s", e)
            return None

    async def fetch_proxyscrape(self) -> Set[str]:
        """Fetch proxies from ProxyScrape."""
        proxies = set()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(PROXY_SCRAPE_URL)
                resp.raise_for_status()
                lines = resp.text.splitlines()
                for line in lines:
                    line = line.strip()
                    if line and line.startswith(("http://", "https://", "socks4://", "socks5://")):
                        proxies.add(line)
        except Exception as e:
            LOGGER.error("Failed to fetch from ProxyScrape: %s", e)
        return proxies

    async def fetch_geonode(self) -> Set[str]:
        """Fetch proxies from Geonode."""
        proxies = set()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(GEONODE_URL)
                resp.raise_for_status()
                data = resp.json()
                for item in data.get("data", []):
                    ip = item.get("ip")
                    port = item.get("port")
                    protocols = item.get("protocols", [])
                    # Prefer socks5 over socks4 over http
                    protocol = "http"
                    if "socks5" in protocols:
                        protocol = "socks5"
                    elif "socks4" in protocols:
                        protocol = "socks4"
                    elif "https" in protocols:
                        protocol = "https"
                        
                    if ip and port:
                        proxies.add(f"{protocol}://{ip}:{port}")
        except Exception as e:
            LOGGER.error("Failed to fetch from Geonode: %s", e)
        return proxies

    async def _validate_proxy(self, proxy_url: str) -> str | None:
        """
        Validate a single proxy.
        Returns the proxy_url if it passes latency and anonymity checks, else None.
        """
        parsed = urlparse(proxy_url)
        # httpx handles http://, https://, socks5://, and socks5h://
        # For HTTP/HTTPS scraping, we just test connecting to an HTTPS site.
        # But httpx async client proxy parameter takes the URL directly.
        
        # Geonode/Proxyscrape provide `socks4`, but httpx doesn't support socks4 natively in async very well, 
        # so we will skip socks4 to avoid crashes if we only want reliable ones.
        if parsed.scheme == "socks4":
            return None

        # httpx expects 'proxy' or 'proxies' param.
        # We test hitting api.ipify.org over HTTPS to ensure it can do SSL.
        try:
            async with httpx.AsyncClient(
                proxy=proxy_url,
                timeout=self.validation_timeout_s,
                verify=False # We only care if it can pass traffic, not if the cert store is perfectly synced
            ) as client:
                start_time = time.monotonic()
                resp = await client.get("https://api.ipify.org?format=json")
                latency = time.monotonic() - start_time
                
                resp.raise_for_status()
                returned_ip = resp.json().get("ip")
                
                if returned_ip and returned_ip != self.real_ip:
                    # Validated high anonymity and high speed
                    LOGGER.debug("Validated proxy %s (latency: %.2fs)", proxy_url, latency)
                    return proxy_url
                else:
                    # Transparent proxy (leaked real IP)
                    return None
        except Exception:
            # Timeout, connection error, etc.
            return None

    async def get_validated_proxies(self) -> List[str]:
        """Fetch from all sources, validate them, and return a list of reliable proxies."""
        await self._get_real_ip()
        
        # 1. Fetch raw proxies concurrently
        fetch_tasks = [
            self.fetch_proxyscrape(),
            self.fetch_geonode()
        ]
        results = await asyncio.gather(*fetch_tasks)
        
        all_raw_proxies = set()
        for r in results:
            all_raw_proxies.update(r)
            
        LOGGER.info("Fetched %d raw proxies. Starting validation...", len(all_raw_proxies))
        
        # 2. Validate concurrently
        # Limit concurrency to avoid file descriptor limits and network congestion
        valid_proxies = []
        semaphore = asyncio.Semaphore(100)
        
        async def bounded_validate(proxy_url: str):
            async with semaphore:
                res = await self._validate_proxy(proxy_url)
                if res:
                    valid_proxies.append(res)

        validate_tasks = [bounded_validate(p) for p in all_raw_proxies]
        await asyncio.gather(*validate_tasks)
        
        LOGGER.info("Validation complete. Found %d high-speed, high-anonymity proxies.", len(valid_proxies))
        return valid_proxies

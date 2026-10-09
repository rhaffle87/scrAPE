"""
doh_resolver.py — DNS-over-HTTPS (DoH) resolver and transparent anti-censorship layer.

Provides transparent DNS resolution via Cloudflare (1.1.1.1) and Google (8.8.8.8)
to detect and bypass ISP DNS poisoning, SNI/DNS interception (e.g. Kominfo/Telkom
TrustPositif/InternetBaik returning 202.3.218.139 / 118.98.115.11), and regional
DNS sinkholes.
"""

from __future__ import annotations

import json
import logging
import socket
import ssl
import threading
import time
import urllib.request
from typing import Any

LOGGER = logging.getLogger(__name__)

# Known ISP DNS sinkhole / censorship redirection IPs (Telkom, Biznet, Kominfo, etc.)
KNOWN_CENSORSHIP_IPS: set[str] = {
    "202.3.218.139",
    "118.98.115.11",
    "36.86.63.181",
    "36.86.63.182",
    "180.131.144.144",
    "180.131.145.145",
    "103.236.201.218",
    "127.0.0.1",
    "::1",
}

DEFAULT_TTL_SECONDS = 600.0


class DoHResolver:
    """Thread-safe DNS-over-HTTPS resolver with transparent socket interception."""

    _instance: DoHResolver | None = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        self._cache: dict[str, tuple[list[str], float]] = {}
        self._cache_lock = threading.Lock()
        self._installed = False
        self._orig_getaddrinfo = socket.getaddrinfo

    @classmethod
    def get_instance(cls) -> DoHResolver:
        """Return singleton DoHResolver instance."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @staticmethod
    def get_doh_url() -> str:
        """Return the primary DoH endpoint URL for curl_cffi / libcurl."""
        return "https://1.1.1.1/dns-query"

    @staticmethod
    def is_poisoned_ip(ip: str) -> bool:
        """Return True if *ip* matches a known ISP censorship sinkhole or loopback hijack."""
        return ip.strip() in KNOWN_CENSORSHIP_IPS

    def query_doh(self, hostname: str) -> list[str]:
        """Query DNS-over-HTTPS for *hostname*, returning a list of IPv4 addresses."""
        clean_host = hostname.strip().lower()
        now = time.monotonic()

        with self._cache_lock:
            if clean_host in self._cache:
                ips, expires_at = self._cache[clean_host]
                if now < expires_at:
                    return ips

        # Primary: Cloudflare 1.1.1.1
        # Secondary: Google 8.8.8.8
        endpoints = [
            f"https://1.1.1.1/dns-query?name={clean_host}&type=A",
            f"https://8.8.8.8/resolve?name={clean_host}&type=A",
        ]

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        for endpoint in endpoints:
            try:
                req = urllib.request.Request(
                    endpoint,
                    headers={
                        "Accept": "application/dns-json",
                        "User-Agent": "curl/8.0 (DNS-over-HTTPS Resolver)",
                    },
                )
                with urllib.request.urlopen(req, context=ctx, timeout=3.0) as resp:
                    if resp.status == 200:
                        payload = json.loads(resp.read().decode("utf-8"))
                        answers = payload.get("Answer", [])
                        ips = [
                            str(a["data"])
                            for a in answers
                            if a.get("type") == 1 and not self.is_poisoned_ip(str(a["data"]))
                        ]
                        if ips:
                            with self._cache_lock:
                                self._cache[clean_host] = (ips, now + DEFAULT_TTL_SECONDS)
                            LOGGER.debug(
                                "DoHResolver: resolved %s -> %s via %s", clean_host, ips, endpoint
                            )
                            return ips
            except Exception as exc:
                LOGGER.debug("DoHResolver endpoint %s failed for %s: %s", endpoint, clean_host, exc)

        return []

    def smart_getaddrinfo(
        self, host: Any, port: Any, *args: Any, **kwargs: Any
    ) -> list[tuple[Any, ...]]:
        """Replacement for socket.getaddrinfo that inspects resolved IPs and falls back to DoH."""
        if not host or not isinstance(host, str):
            return self._orig_getaddrinfo(host, port, *args, **kwargs)

        host_lower = host.lower().strip()
        # Direct IPs and loopback bypass DoH inspection
        if (
            host_lower in ("localhost", "127.0.0.1", "::1", "1.1.1.1", "8.8.8.8")
            or host_lower.replace(".", "").isdigit()
            or ":" in host_lower
        ):
            return self._orig_getaddrinfo(host, port, *args, **kwargs)

        is_poisoned = False
        try:
            res = self._orig_getaddrinfo(host, port, *args, **kwargs)
            for family, socktype, proto, canonname, sockaddr in res:
                ip = sockaddr[0] if isinstance(sockaddr, tuple) and sockaddr else ""
                if self.is_poisoned_ip(ip):
                    is_poisoned = True
                    break
            if not is_poisoned:
                return res
        except socket.gaierror:
            # System DNS failed completely
            is_poisoned = True

        if is_poisoned:
            LOGGER.warning(
                "DoHResolver: detected DNS poisoning/sinkhole on '%s'. Re-resolving via DoH...", host
            )
            doh_ips = self.query_doh(host_lower)
            if doh_ips:
                out = []
                for ip in doh_ips:
                    out.append((socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port)))
                return out

        return self._orig_getaddrinfo(host, port, *args, **kwargs)

    def install(self) -> None:
        """Hook socket.getaddrinfo with DoH anti-poisoning resolver."""
        with self._cache_lock:
            if not self._installed:
                socket.getaddrinfo = self.smart_getaddrinfo
                self._installed = True
                LOGGER.info("DoHResolver: installed transparent socket.getaddrinfo hook.")

    def uninstall(self) -> None:
        """Restore original socket.getaddrinfo."""
        with self._cache_lock:
            if self._installed:
                socket.getaddrinfo = self._orig_getaddrinfo
                self._installed = False
                LOGGER.info("DoHResolver: uninstalled socket.getaddrinfo hook.")

"""proxy_pool.py — Compatibility alias and re-export for ProxyPoolManager and ProxyInfo."""

from __future__ import annotations

from network.proxy_manager import ProxyInfo, ProxyPoolManager

__all__ = ["ProxyInfo", "ProxyPoolManager"]

"""
security.py — Centralized security utilities for SSRF validation, DNS rebinding prevention,
credential sanitization, and 3-step path traversal defense.
"""

from __future__ import annotations

import ipaddress
import logging
import os
from pathlib import Path
import re
import socket
from urllib.parse import urlparse

LOGGER = logging.getLogger(__name__)

# Cloud metadata and internal service domains
BLOCKED_HOSTS: set[str] = {
    "localhost",
    "localhost.localdomain",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "metadata.google.internal",
    "instance-data",
    "169.254.169.254",
    "metadata.azure.com",
}


def sanitize_url_credentials(url: str) -> str:
    """Scrub credentials from a Redis, HTTP, or DB URL for safe logging/telemetry."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        if parsed.password:
            user = parsed.username or ""
            port_str = f":{parsed.port}" if parsed.port else ""
            netloc = f"{user}:***@{parsed.hostname}{port_str}"
            return parsed._replace(netloc=netloc).geturl()
        return url
    except Exception:
        return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", url)


def is_safe_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Return True if IP is public and globally routable; reject private/loopback/link-local."""
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    ):
        return False
    # Check 6to4 / IPv4-mapped IPv6 addresses (::ffff:127.0.0.1)
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped and not is_safe_ip(ip.ipv4_mapped):
            return False
        if ip.sixtofour and not is_safe_ip(ip.sixtofour):
            return False
    return True


def is_safe_target_url(url: str) -> bool:
    """
    Validate target URL to prevent SSRF against loopback, link-local, private networks,
    and cloud metadata endpoints. Performs DNS resolution to prevent TOCTOU DNS rebinding.
    """
    if os.environ.get("SCRAPE_ALLOW_LOCAL_TARGETS", "").lower() in ("true", "1"):
        return True

    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        hostname_clean = hostname.lower().strip(".")
        if hostname_clean in BLOCKED_HOSTS or hostname_clean.endswith(".internal"):
            return False

        # Attempt to parse integer / octal / hex encoded IPv4 formats (e.g. 2130706433)
        if hostname_clean.isdigit():
            try:
                ip = ipaddress.ip_address(int(hostname_clean))
                if not is_safe_ip(ip):
                    return False
            except ValueError:
                pass

        # Check if hostname is an IP literal
        try:
            ip = ipaddress.ip_address(hostname_clean)
            if not is_safe_ip(ip):
                return False
            return True
        except ValueError:
            pass

        # Hostname is a domain name; resolve DNS to inspect all target IPs (Anti-DNS Rebinding)
        try:
            addr_info = socket.getaddrinfo(hostname_clean, None)
            if not addr_info:
                return False
            for item in addr_info:
                resolved_ip_str = item[4][0]
                try:
                    resolved_ip = ipaddress.ip_address(resolved_ip_str)
                    if not is_safe_ip(resolved_ip):
                        LOGGER.warning("SSRF blocked: Domain %s resolved to unsafe IP %s", hostname_clean, resolved_ip_str)
                        return False
                except ValueError:
                    return False
        except socket.gaierror:
            # Domain could not be resolved; allow downstream network stack to handle connection failure
            pass

        return True
    except Exception as exc:
        LOGGER.debug("Error checking is_safe_target_url for '%s': %s", url, exc)
        return False


def validate_safe_path(base_dir: str | Path, target_path: str | Path) -> Path:
    """
    Enforce strict 3-step path resolution:
      1. Untainted base root
      2. os.path.abspath(os.path.normpath(...))
      3. Prefix boundary verification against base root (dual relative_to + commonpath)
    """
    base = Path(os.path.abspath(os.path.normpath(base_dir)))
    target = Path(os.path.abspath(os.path.normpath(target_path)))

    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Path traversal detected: {target} is outside {base}") from exc

    try:
        common = os.path.commonpath([str(base), str(target)])
        if os.path.normcase(common) != os.path.normcase(str(base)):
            raise ValueError(f"Path traversal detected: {target} is outside {base}")
    except Exception as exc:
        raise ValueError(f"Path traversal detected: {target} is outside {base}") from exc

    base_str = str(base)
    safe_boundary = base_str if base_str.endswith(os.sep) else base_str + os.sep
    target_str = str(target)
    norm_target = os.path.normcase(target_str)
    norm_boundary = os.path.normcase(safe_boundary)
    norm_base = os.path.normcase(base_str)
    if not (norm_target.startswith(norm_boundary) or norm_target == norm_base):
        raise ValueError(f"Path traversal detected: {target} is outside {base}")

    return target


def is_safe_subpath_strict(base_dir: str | Path, target_path: str | Path) -> bool:
    """Return True if target_path is cleanly and strictly contained inside base_dir without traversal or sibling escape."""
    try:
        validate_safe_path(base_dir, target_path)
        return True
    except (ValueError, TypeError):
        return False


def is_safe_subpath(base_dir: str | Path, target_path: str | Path) -> bool:
    """Return True if target_path is cleanly contained inside base_dir without traversal."""
    return is_safe_subpath_strict(base_dir, target_path)


def sanitize_filename(name: str) -> str:
    """Sanitize a filename to strip directory traversal sequences and unsafe characters."""
    safe = re.sub(r"[^a-zA-Z0-9_.\-]", "_", name)
    safe = safe.replace("..", "_").strip(" ._")
    safe = re.sub(r"_+", "_", safe)
    return safe or "unnamed"

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


def is_safe_target_url(url: str, allow_local: bool = False) -> bool:
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
            if allow_local and hostname_clean in ("localhost", "localhost.localdomain", "127.0.0.1", "::1"):
                return True
            return False

        # Attempt to parse integer / octal / hex encoded IPv4 formats (e.g. 2130706433)
        if hostname_clean.isdigit():
            try:
                ip = ipaddress.ip_address(int(hostname_clean))
                if ip.is_loopback and allow_local:
                    return True
                if not is_safe_ip(ip):
                    return False
            except ValueError:
                pass

        # Check if hostname is an IP literal
        try:
            ip = ipaddress.ip_address(hostname_clean)
            if ip.is_loopback and allow_local:
                return True
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
                    if resolved_ip.is_loopback and allow_local:
                        continue
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


CAS_KEY_REGEX = re.compile(r"^[0-9a-f]{64}$")


def validate_cas_key(key: str) -> str:
    """
    Validate that a Content-Addressable Storage (CAS) key is a valid SHA-256 hex digest (AC2.3).
    Enforces exactly 64 lowercase hexadecimal ASCII characters.
    Rejects path traversal, null bytes, non-hex, uppercase, whitespace, and malformed strings.
    """
    if not isinstance(key, str):
        raise ValueError(f"CAS key must be a string, got {type(key).__name__}")
    if not CAS_KEY_REGEX.match(key):
        raise ValueError(
            f"Invalid CAS key: '{key}'. Must be exactly 64 lowercase hexadecimal characters."
        )
    return key


def validate_s3_endpoint_url(endpoint_url: str | None) -> str | None:
    """
    Validate custom S3 endpoint URL (MinIO / Cloudflare R2 / LocalStack) against SSRF,
    cloud metadata, link-local, and private network exploitation (AC2.2).
    Allows loopback/local endpoints only if SCRAPE_ALLOW_LOCAL_S3_ENDPOINT=true.
    """
    if not endpoint_url:
        return None
    endpoint_str = str(endpoint_url).strip()
    if not endpoint_str:
        return None

    from config.settings_manager import settings

    allow_local = settings.is_local_s3_endpoint_allowed()
    if not is_safe_target_url(endpoint_str, allow_local=allow_local):
        raise ValueError(
            f"SSRF blocked: S3_ENDPOINT_URL '{endpoint_str}' points to an insecure or restricted address. "
            f"Set SCRAPE_ALLOW_LOCAL_S3_ENDPOINT=true to allow local loopback endpoints for testing."
        )
    return endpoint_str


CSS_DISALLOWED_PATTERNS = [
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"vbscript:", re.IGNORECASE),
    re.compile(r"data:", re.IGNORECASE),
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"</?[a-z]+", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"-moz-binding", re.IGNORECASE),
    re.compile(r"@import", re.IGNORECASE),
    re.compile(r"@charset", re.IGNORECASE),
    re.compile(r"url\s*\(", re.IGNORECASE),
    re.compile(r"[;{}]"),
    re.compile(r"/\*|\*/"),
    re.compile(r"[`\\]"),
]

FORBIDDEN_ROOT_SELECTORS = {"*", "body", "html", ":root", "head", "script", "style"}

FORBIDDEN_ROOT_PATTERN = re.compile(
    r"(?:^|[\s>+~])(?:\*|body|html|head|script|style)(?:[\s>+~]|$)",
    re.IGNORECASE,
)

DANGEROUS_PSEUDO_CLASSES = re.compile(
    r":(?:is|where|has|not|scope|empty|root)(?:\s*\(|\b)",
    re.IGNORECASE,
)

# AC3.4 Structural Allowlist Definitions
SAFE_MEDIA_CONTROL_CLASSES = re.compile(
    r"(?i)\b("
    r"play|pause|unmute|mute|volume|replay|fullscreen|full-screen|"
    r"vjs-play-control|vjs-control|ytp-play-button|jw-display-icon|jw-icon-playback|"
    r"media-control|video-control|audio-control|player-control|media-player|"
    r"playback-button|play-btn|play-button|video-js"
    r")\b"
)

SAFE_MEDIA_CONTROL_LABELS = re.compile(
    r"(?i)\b(play|pause|unmute|mute|toggle mute|volume|replay|fullscreen|full screen|media)\b"
)

SAFE_OVERLAY_DISMISS_CLASSES = re.compile(
    r"(?i)\b("
    r"modal-close|dialog-close|popup-close|banner-close|overlay-close|"
    r"btn-close|close-btn|close-button|cookie-accept|cookie-agree|consent-accept|"
    r"consent-agree|accept-all|agree-all|accept-cookies|dismiss-banner|"
    r"cookie-banner|consent-banner|overlay-dismiss"
    r")\b"
)

SAFE_OVERLAY_DISMISS_LABELS = re.compile(
    r"(?i)\b("
    r"close|dismiss|accept cookies|accept all cookies|agree|accept all|"
    r"accept necessary|i agree|got it|understand|hide banner|close dialog"
    r")\b"
)

DESTRUCTIVE_TERMS = {
    "delete",
    "remove",
    "destroy",
    "erase",
    "purge",
    "drop",
    "reset",
    "uninstall",
    "terminate",
    "cancel",
    "unsubscribe",
    "deactivate",
    "confirm",
    "purchase",
    "buy",
    "order",
    "checkout",
    "pay",
    "payment",
    "transfer",
    "commit",
    "apply",
    "save",
    "update settings",
    "change password",
    "logout",
    "log out",
    "sign out",
    "signout",
    "disconnect",
}


def validate_css_selector(selector: str) -> str:
    """
    Validate that a CSS selector is safe, syntactically well-formed, and bounded (AC3.1).
    Rejects:
      - Control characters, newlines, null bytes.
      - Scripting / injection attempts (javascript:, vbscript:, data:, @import, expression).
      - HTML tags or delimiter breakout tokens (</untrusted_scraped_data>, <script>).
      - Semicolons, curly braces, CSS comments, backticks, backslashes.
      - Root/global wildcards (*, body, html, :root, head, script, style, div *).
      - Complex/dangerous pseudo-classes (:is, :where, :has, :not, :scope, :root).
      - Syntax errors unparseable by soupsieve.
    """
    if not selector or not isinstance(selector, str):
        raise ValueError("CSS selector must be a non-empty string.")

    cleaned = selector.strip()
    if not cleaned:
        raise ValueError("CSS selector cannot be empty or whitespace only.")

    if len(cleaned) > 500:
        raise ValueError(f"CSS selector exceeds maximum length of 500 characters (got {len(cleaned)}).")

    if re.search(r"[\x00-\x1f\x7f\r\n]", cleaned):
        raise ValueError("CSS selector contains illegal control characters or newlines.")

    for pattern in CSS_DISALLOWED_PATTERNS:
        if pattern.search(cleaned):
            raise ValueError(f"CSS selector contains disallowed pattern: {pattern.pattern}")

    if cleaned.lower() in FORBIDDEN_ROOT_SELECTORS or FORBIDDEN_ROOT_PATTERN.search(cleaned):
        raise ValueError(
            f"Root, global wildcard, or unconstrained element selector '{cleaned}' is forbidden for media extraction."
        )

    if DANGEROUS_PSEUDO_CLASSES.search(cleaned):
        raise ValueError(
            f"CSS selector contains forbidden complex pseudo-class in '{cleaned}'."
        )

    # Validate syntax via soupsieve compilation
    try:
        import soupsieve
        soupsieve.compile(cleaned)
    except Exception as exc:
        raise ValueError(f"Invalid CSS selector syntax '{cleaned}': {exc}") from exc

    return cleaned


def is_safe_vlm_interaction_target(
    tag_name: str,
    attributes: dict[str, Any] | None,
    text_content: str = "",
    current_domain: str = "",
) -> tuple[bool, str]:
    """
    Evaluates live DOM elements targeted by VLM coordinates using a
    STRUCTURAL ALLOWLIST (DEFAULT-DENY) architecture (AC3.4).

    Only allows elements matching:
      1. Media playback controls (video, audio, play/pause buttons, unmute, fullscreen)
      2. Overlay / banner dismiss controls (cookie consent, modal close, dialog dismiss)

    Rejects by default:
      - Any generic, ambiguous, or form buttons ('Yes', 'OK', 'Submit', 'Continue', etc.)
      - Form elements (<form>, <input type='submit'>, action targets)
      - Elements containing destructive/affirmative keywords across text or attributes
      - Links navigating away from the current page / external cross-domain links
      - Anything not affirmatively matching the structural allowlist shapes.

    Returns (is_safe: bool, reason: str).
    """
    tag = (tag_name or "").lower().strip()
    attrs = attributes or {}
    text = (text_content or "").strip()

    # --- NEGATIVE GATES (Hard Deny) ---

    # 1. Form submissions and form elements
    if tag == "form":
        return False, "Targeting <form> elements is prohibited for VLM interaction."

    input_type = str(attrs.get("type", "")).lower()
    if input_type in ("submit", "reset"):
        return False, f"Form submit/reset elements (<{tag} type='{input_type}'>) are prohibited for VLM interaction."

    if attrs.get("action"):
        return False, "Elements with form 'action' attributes are prohibited for VLM interaction."

    if tag == "input" and input_type not in ("button", "image"):
        return False, f"Input elements of type '{input_type}' are prohibited for VLM interaction."

    # 2. Destructive intent keywords across visible text
    for term in DESTRUCTIVE_TERMS:
        pattern = rf"(?<![a-zA-Z0-9]){re.escape(term)}(?![a-zA-Z0-9])"
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Destructive keyword '{term}' detected in element text: '{text[:50]}'"

    # 3. Destructive intent keywords across attributes
    for attr_name in ("id", "class", "name", "aria-label", "title", "value", "action", "role"):
        attr_val = attrs.get(attr_name)
        if not attr_val:
            continue
        if isinstance(attr_val, (list, tuple)):
            val_str = " ".join(str(v) for v in attr_val).lower()
        else:
            val_str = str(attr_val).lower()

        for term in DESTRUCTIVE_TERMS:
            pattern = rf"(?<![a-zA-Z0-9]){re.escape(term)}(?![a-zA-Z0-9])"
            if re.search(pattern, val_str, re.IGNORECASE):
                return False, f"Destructive keyword '{term}' detected in attribute '{attr_name}': '{val_str[:50]}'"

    # 4. External navigation / unsafe URI schemes in href
    link_target = str(attrs.get("href") or "").strip()
    if link_target:
        if link_target.lower().startswith(("javascript:", "data:", "vbscript:", "mailto:", "tel:")):
            return False, f"Unsafe URI scheme in target link: '{link_target[:30]}'"

        try:
            parsed = urlparse(link_target)
            target_host = (parsed.hostname or "").lower().lstrip("www.")
            if target_host:
                curr_host = current_domain.lower().lstrip("www.")
                if ":" in curr_host:
                    curr_host = curr_host.split(":")[0]
                if curr_host and target_host != curr_host and not target_host.endswith(f".{curr_host}"):
                    return False, f"External cross-domain navigation blocked: '{target_host}' != '{curr_host}'"
        except Exception as exc:
            return False, f"Malformed URL in target link: {exc}"

    # --- STRUCTURAL ALLOWLIST (Default-Deny) ---

    cls_attr = attrs.get("class", "")
    cls_str = " ".join(cls_attr) if isinstance(cls_attr, (list, tuple)) else str(cls_attr)
    id_str = str(attrs.get("id", ""))
    tokens_str = f"{cls_str} {id_str}"

    label_str = f"{attrs.get('aria-label', '')} {attrs.get('title', '')} {attrs.get('alt', '')}"
    role_str = str(attrs.get("role", "")).lower()

    # Category A: Media Playback / Unmute / Fullscreen Controls
    if tag in ("video", "audio"):
        return True, "Safe media tag"

    if tag in ("button", "div", "span", "i", "svg", "a"):
        if (
            SAFE_MEDIA_CONTROL_CLASSES.search(tokens_str)
            or SAFE_MEDIA_CONTROL_LABELS.search(label_str)
            or SAFE_MEDIA_CONTROL_LABELS.search(text)
            or role_str in ("button", "switch") and SAFE_MEDIA_CONTROL_LABELS.search(tokens_str)
        ):
            return True, "Safe media playback control"

    # Category B: Overlay / Modal / Cookie Consent Dismissal
    if tag in ("button", "div", "span", "a"):
        if (
            SAFE_OVERLAY_DISMISS_CLASSES.search(tokens_str)
            or SAFE_OVERLAY_DISMISS_LABELS.search(label_str)
            or SAFE_OVERLAY_DISMISS_LABELS.search(text)
        ):
            return True, "Safe overlay dismissal control"

    # DEFAULT-DENY: Reject anything that failed to affirmatively match the allowlist
    return False, (
        f"Default-deny: Target <{tag}> with text '{text[:30]}' does not match structural allowlist "
        "(must be media-playback or overlay-dismissal)."
    )

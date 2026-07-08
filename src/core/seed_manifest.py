"""
seed_manifest.py — Parse annotated seed files into structured domain profiles.

The seed file format uses comment lines immediately above each URL block to
annotate that domain's expected media type, crawl strategy, CDN hosts, and
other notes. This module converts those annotations into dataclasses consumed
by the engine, filter layer, and logger.

Annotation syntax recognised inside comment blocks:
    # type: video | image | mixed
    # crawl: direct | index → detail  (also parses "direct" from same line)
    # [CDN] hostname                   (one host per line, multiple allowed)
    # Subject : Name / AltName / ...   (header block, first occurrence used)
    # depth: N                         (optional per-domain crawl depth cap)
    # skip-link-discovery              (flag domains unsuitable for crawling)

A single comment line may contain multiple annotations separated by pipes,
e.g.  # type: image  |  crawl: direct
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

@dataclass
class DomainProfile:
    """Parsed profile for a single seed domain."""

    domain: str
    """Bare hostname, e.g. 'erothots1.com'."""

    seed_urls: list[str] = field(default_factory=list)
    """Bare URLs that belong to this domain (in order)."""

    media_type: str = "mixed"
    """Expected primary media kind: 'video', 'image', or 'mixed'."""

    crawl_strategy: str = "index→detail"
    """
    'direct'       — page itself holds final assets; skip link discovery.
    'index→detail' — index page discovers detail-page links to follow.
    """

    crawl_depth: int | None = None
    """
    Optional depth override. None means use the engine's default
    (0 for direct, 1 for index→detail).
    """

    cdn_hosts: list[str] = field(default_factory=list)
    """Cross-origin CDN hostnames referenced from this domain's pages."""

    skip_link_discovery: bool = False
    """True for domains where link discovery is known to be useless/risky."""

    rate_limit: float | None = None
    """Optional rate-limit override in requests per second (req/s)."""

    username: str | None = None
    """Optional username credential parsed from manifest."""

    email: str | None = None
    """Optional email credential parsed from manifest."""

    password: str | None = None
    """Optional password credential parsed from manifest."""

    notes: list[str] = field(default_factory=list)
    """Remaining human-readable comment lines for this domain block."""

    @property
    def effective_crawl_depth(self) -> int:
        """Resolved crawl depth, applying strategy defaults when not overridden."""
        if self.crawl_depth is not None:
            return self.crawl_depth
        return 0 if self.crawl_strategy == "direct" else 1


@dataclass
class SeedManifest:
    """Top-level parsed representation of a seed file."""

    source_file: Path
    """Path to the seed file that was parsed."""

    subject_name: str = ""
    """Human-readable subject name from the '# Subject :' header line."""

    entity_tokens: list[str] = field(default_factory=list)
    """
    Tokens extracted from the subject name line, normalised for scoring.
    E.g. 'Example Subject / Alias Beta' -> ['example subject', 'alias beta',
    'example', 'alias', 'beta'].
    """

    domains: list[DomainProfile] = field(default_factory=list)
    """All domain profiles, in file order."""

    @property
    def domain_map(self) -> dict[str, DomainProfile]:
        """Return {hostname: DomainProfile} for O(1) lookup."""
        return {p.domain: p for p in self.domains}

    @property
    def all_seed_urls(self) -> list[str]:
        """Flat list of every seed URL across all domains, in file order."""
        urls: list[str] = []
        for profile in self.domains:
            urls.extend(profile.seed_urls)
        return urls

    @property
    def all_allowed_hosts(self) -> list[str]:
        """
        Every domain + CDN host that should be admitted by the allow-list.
        Deduplicated, order-preserving.
        """
        seen: set[str] = set()
        out: list[str] = []
        for profile in self.domains:
            for host in [profile.domain, *profile.cdn_hosts]:
                if host not in seen:
                    seen.add(host)
                    out.append(host)
        return out

    @classmethod
    def from_file(cls, path: "Path | str") -> "SeedManifest":
        """Parse *path* and return a populated ``SeedManifest``."""
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        return _parse(path, text)


# ---------------------------------------------------------------------------
# Internal parser helpers
# ---------------------------------------------------------------------------

_SUBJECT_RE = re.compile(r"#\s*Subject\s*:\s*(.+)", re.IGNORECASE)
# These regexes search the whole comment line (no leading-# anchor) so they
# also match lines like  "# type: image  |  crawl: direct"
_TYPE_RE = re.compile(r"\btype\s*:\s*(video|image|mixed)\b", re.IGNORECASE)
_CRAWL_RE = re.compile(r"\bcrawl\s*:\s*(direct|index.+?detail)\b", re.IGNORECASE)
_CDN_RE = re.compile(r"#\s*\[CDN\]\s*(\S+)", re.IGNORECASE)
_DEPTH_RE = re.compile(r"#\s*depth\s*:\s*(\d+)", re.IGNORECASE)
_SKIP_RE = re.compile(r"#\s*(skip[-_]link[-_]discovery|skip link discovery)", re.IGNORECASE)
_RATE_LIMIT_RE = re.compile(r"\bRate-limit\s*:\s*(\d+(?:\.\d+)?)\s*req/s", re.IGNORECASE)
_USERNAME_RE = re.compile(r"\bUsername\s*:\s*(\S+)", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\bEmail\s*:\s*(\S+)", re.IGNORECASE)
_PASSWORD_RE = re.compile(r"\bPassword\s*:\s*(\S+)", re.IGNORECASE)
_URL_RE = re.compile(r"^https?://\S+$")
_SUBJECT_SPLIT_RE = re.compile(r"[/|,]")


def _normalise_cdn_host(raw: str) -> str:
    """
    Normalise CDN host patterns to the real matchable hostname or parent domain.
    e.g. 's{NNN}.erome.com' -> 'erome.com'
         'cdn.erocdn.co'    -> 'cdn.erocdn.co'  (already concrete)
    """
    raw = raw.lower().strip()
    # Strip wildcard / template prefixes like 's{NNN}.', 's*.', '*.', etc.
    cleaned = re.sub(r"^[a-z0-9*{}\[\]]+\.", "", raw)
    if "." in cleaned and cleaned != raw:
        return cleaned
    return raw


def _host(url: str) -> str:
    return urlparse(url).netloc.lower()


def _extract_entity_tokens(subject_name: str) -> list[str]:
    """
    Split 'Subject / AltName' into individual normalised tokens.
    Also adds sub-word tokens for multi-word names.
    """
    tokens: list[str] = []
    seen: set[str] = set()
    for part in _SUBJECT_SPLIT_RE.split(subject_name):
        clean = part.strip().lower()
        if clean and clean not in seen:
            seen.add(clean)
            tokens.append(clean)
            for word in clean.split():
                if word and word not in seen:
                    seen.add(word)
                    tokens.append(word)
    return tokens


# ---------------------------------------------------------------------------
# Core parser — two-pass: buffer comment blocks, commit on first URL seen
# ---------------------------------------------------------------------------


def _parse(source: Path, text: str) -> SeedManifest:  # noqa: PLR0912
    """
    Two-pass strategy:
    1. Accumulate comment lines into a 'pending' buffer.
    2. When a URL line is seen, look up / create a DomainProfile.
       If the domain is *new*, commit the pending buffer as its annotations
       and reset the buffer for the next block.
       If the domain already exists, just append the URL.
    """
    manifest = SeedManifest(source_file=source)

    # Pending annotation buffer — built up from comments before a URL block
    pend_media: str = "mixed"
    pend_crawl: str = "index\u2192detail"
    pend_cdns: list[str] = []
    pend_depth: int | None = None
    pend_skip: bool = False
    pend_rate_limit: float | None = None
    pend_username: str | None = None
    pend_email: str | None = None
    pend_password: str | None = None
    pend_notes: list[str] = []

    def reset_pending() -> None:
        nonlocal pend_media, pend_crawl, pend_cdns, pend_depth, pend_skip, pend_notes
        nonlocal pend_rate_limit, pend_username, pend_email, pend_password
        pend_media = "mixed"
        pend_crawl = "index\u2192detail"
        pend_cdns = []
        pend_depth = None
        pend_skip = False
        pend_rate_limit = None
        pend_username = None
        pend_email = None
        pend_password = None
        pend_notes = []

    def commit_new_profile(domain: str) -> DomainProfile:
        profile = DomainProfile(
            domain=domain,
            media_type=pend_media,
            crawl_strategy=pend_crawl,
            cdn_hosts=list(pend_cdns),
            crawl_depth=pend_depth,
            skip_link_discovery=pend_skip,
            rate_limit=pend_rate_limit,
            username=pend_username,
            email=pend_email,
            password=pend_password,
            notes=list(pend_notes),
        )
        manifest.domains.append(profile)
        return profile

    known_domains: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue  # blank lines — no action; pending survives

        if line.startswith("#"):
            # Global subject header (first match only)
            m = _SUBJECT_RE.match(line)
            if m and not manifest.subject_name:
                manifest.subject_name = m.group(1).strip()
                manifest.entity_tokens = _extract_entity_tokens(manifest.subject_name)
                continue

            # Annotation: type
            m = _TYPE_RE.search(line)
            if m:
                pend_media = m.group(1).lower()

            # Annotation: crawl strategy — "direct" wins if present
            m = _CRAWL_RE.search(line)
            if m:
                raw = m.group(1).lower()
                pend_crawl = "direct" if "direct" in raw else "index\u2192detail"

            # Annotation: CDN host
            m = _CDN_RE.search(line)
            if m:
                cdn = _normalise_cdn_host(m.group(1))
                if cdn not in pend_cdns:
                    pend_cdns.append(cdn)

            # Annotation: depth override
            m = _DEPTH_RE.search(line)
            if m:
                pend_depth = int(m.group(1))

            # Flag: skip link discovery
            if _SKIP_RE.search(line):
                pend_skip = True

            # Annotation: Rate-limit
            m = _RATE_LIMIT_RE.search(line)
            if m:
                pend_rate_limit = float(m.group(1))

            # Annotation: Username
            m = _USERNAME_RE.search(line)
            if m:
                pend_username = m.group(1).strip()

            # Annotation: Email
            m = _EMAIL_RE.search(line)
            if m:
                pend_email = m.group(1).strip()

            # Annotation: Password
            m = _PASSWORD_RE.search(line)
            if m:
                pend_password = m.group(1).strip()

            pend_notes.append(line)
            continue

        # URL line
        if _URL_RE.match(line):
            domain = _host(line)
            if not domain:
                continue

            # New domain encountered — pending buffer belongs to it
            if domain not in known_domains:
                known_domains.add(domain)
                # pending annotations were built from the comment block above
                profile = commit_new_profile(domain)
                reset_pending()
            else:
                # Already have a profile — just find it
                profile = next(p for p in manifest.domains if p.domain == domain)

            if line not in profile.seed_urls:
                profile.seed_urls.append(line)
            continue

        # Non-URL, non-comment, non-blank — ignore

    return manifest

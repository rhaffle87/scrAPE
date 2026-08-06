from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse
from monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class SeedLinter:
    """Validates and lints .txt seed manifest files for syntax errors and unknown annotations."""

    VALID_ANNOTATION_PREFIXES = [
        "type:",
        "crawl:",
        "[cdn]",
        "subject",
        "depth:",
        "skip-link-discovery",
        "requires_referer",
        "thumbnail_prefix:",
        "google-fallback:",
        "min_image_size:",
        "rate-limit:",
        "cloudflare:",
        "max_pages:",
    ]

    def lint_manifest_text(self, content: str) -> dict[str, Any]:
        lines = content.splitlines()
        errors: list[str] = []
        warnings: list[str] = []
        domains_seen: set[str] = set()

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("#"):
                comment_body = stripped.lstrip("#").strip().lower()
                if comment_body and not any(comment_body.startswith(p) for p in self.VALID_ANNOTATION_PREFIXES):
                    # Check if it's a structural comment or unknown annotation
                    if ":" in comment_body and not comment_body.startswith("subject"):
                        warnings.append(f"Line {idx}: Unrecognized annotation syntax '{stripped}'")
            elif "://" in stripped:
                domain = urlparse(stripped).netloc.lower()
                if domain:
                    if domain in domains_seen:
                        warnings.append(f"Line {idx}: Duplicate domain '{domain}' found in seed list")
                    else:
                        domains_seen.add(domain)
            else:
                errors.append(f"Line {idx}: Invalid URL or malformed line '{stripped}'")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "domains_count": len(domains_seen),
        }


class PatternGenerator:
    """Generates paginated and template seed URLs from base patterns."""

    def generate_paginated_urls(self, base_url: str, start_page: int = 1, end_page: int = 5) -> list[str]:
        urls = []
        for page in range(start_page, end_page + 1):
            if "{page}" in base_url:
                urls.append(base_url.replace("{page}", str(page)))
            elif base_url.endswith("/"):
                urls.append(f"{base_url}page/{page}/")
            else:
                urls.append(f"{base_url}?page={page}")
        return urls


class SeedDiscoverer:
    """Discovers gallery seed candidate domains from a subject keyword."""

    def discover_seeds_for_subject(self, subject: str) -> str:
        clean_subj = subject.strip()
        slug = re.sub(r"\s+", "-", clean_subj.lower())

        manifest_lines = [
            f"# Subject: {clean_subj}",
            "#",
            "# type: image | crawl: index→detail | max_pages: 50",
            f"https://example.com/gallery/{slug}/",
            "",
            "# type: video | crawl: direct | max_pages: 20",
            f"https://example-videos.com/tag/{slug}/",
        ]
        return "\n".join(manifest_lines)

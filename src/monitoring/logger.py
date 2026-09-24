from __future__ import annotations

import logging
import sys
from pathlib import Path

import re

# Root logger name used when no specific name is requested
_ROOT = "scraper"

# Default log directory (relative to the project root where main.py lives)
_DEFAULT_LOG_DIR = Path("logs")
_DEFAULT_LOG_FILE = "logs.txt"

# Regex patterns for scrubbing secrets from all log output
AWS_KEY_PATTERN = re.compile(r"(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}")
AWS_SECRET_PATTERN = re.compile(
    r"(?i)(aws_secret_access_key|secret_access_key|secret_key|secret|password|sig)[\s:=]+['\"]?([0-9a-zA-Z/+=_-]{16,64})['\"]?"
)
AMZ_SIG_PATTERN = re.compile(r"X-Amz-Signature=[0-9a-fA-F]+")
URL_CRED_PATTERN = re.compile(r"([a-zA-Z0-9+.-]+://)([^:\s/@]+):([^@\s/]+)@")


def scrub_credentials(text: str) -> str:
    """Scrub sensitive AWS keys, signatures, and URL embedded credentials."""
    if not isinstance(text, str) or not text:
        return text
    text = AWS_KEY_PATTERN.sub("[REDACTED_AWS_KEY]", text)
    text = AMZ_SIG_PATTERN.sub("X-Amz-Signature=[REDACTED_SIGNATURE]", text)
    text = AWS_SECRET_PATTERN.sub(r"\1=[REDACTED_SECRET]", text)
    text = URL_CRED_PATTERN.sub(r"\1***:***@", text)
    return text


class CredentialScrubbingFilter(logging.Filter):
    """Logging filter that scrubs sensitive AWS credentials and signatures before emission."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = scrub_credentials(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: scrub_credentials(v) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, (tuple, list)):
                record.args = tuple(scrub_credentials(v) if isinstance(v, str) else v for v in record.args)
        return True


def configure_logging(
    level: int = logging.DEBUG,
    log_dir: Path | None = None,
    log_file: str = _DEFAULT_LOG_FILE,
) -> Path:
    """Configure the root logger with both console and rotating file handlers."""
    log_dir = (log_dir or _DEFAULT_LOG_DIR).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    root = logging.getLogger()
    root.setLevel(level)

    # Attach CredentialScrubbingFilter to root logger
    if not any(isinstance(f, CredentialScrubbingFilter) for f in root.filters):
        root.addFilter(CredentialScrubbingFilter())

    # Suppress verbose third-party logs
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("s3transfer").setLevel(logging.WARNING)

    _fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console handler (INFO and above to keep stdout readable) ──────────
    if not any(
        isinstance(h, logging.StreamHandler) and h.stream is sys.stderr
        for h in root.handlers
    ):
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(logging.INFO)
        console.setFormatter(_fmt)
        root.addHandler(console)

    # ── File handler (DEBUG and above — full trace for analysis) ──────────
    if not any(
        isinstance(h, logging.FileHandler) and Path(h.baseFilename) == log_path
        for h in root.handlers
    ):
        file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(_fmt)
        root.addHandler(file_handler)

    return log_path


def get_logger(name: str) -> logging.Logger:
    """Return a named child logger under the root hierarchy."""
    return logging.getLogger(name)


def log_run_start(
    logger: logging.Logger, keyword: str, seed_count: int, extra: dict | None = None
) -> None:
    """Emit a structured banner at the beginning of a scrape run."""
    sep = "=" * 72
    logger.info(sep)
    logger.info("RUN START  | keyword=%r  seeds=%d", keyword, seed_count)
    if extra:
        for key, value in extra.items():
            logger.info("  %-20s %s", f"{key}:", value)
    logger.info(sep)


def log_run_end(
    logger: logging.Logger,
    keyword: str,
    images: int,
    videos: int,
    output_dir: Path | str,
) -> None:
    """Emit a structured banner at the end of a scrape run."""
    sep = "=" * 72
    logger.info(sep)
    logger.info(
        "RUN END    | keyword=%r  images=%d  videos=%d  output=%s",
        keyword,
        images,
        videos,
        output_dir,
    )
    logger.info(sep)


def log_domain_profile_summary(logger: logging.Logger, manifest: object) -> None:
    """
    Emit a formatted DOMAIN PROFILES table derived from a ``SeedManifest``.

    Called once after the manifest is parsed so every log session has a
    clear header showing exactly which domains the run is scoped to, their
    expected media types, crawl strategies, and CDN hosts.
    """
    sep = "-" * 72
    logger.info(sep)
    logger.info("DOMAIN PROFILES  (%d domains)", len(getattr(manifest, "domains", [])))
    logger.info(
        "  %-30s  %-6s  %-12s  %-5s  %-6s  %s",
        "domain",
        "type",
        "crawl",
        "depth",
        "rps",
        "cdn",
    )
    logger.info("  " + "-" * 68)
    for profile in getattr(manifest, "domains", []):
        strat = profile.crawl_strategy.replace("\u2192", "->")
        cdn_str = ", ".join(profile.cdn_hosts) if profile.cdn_hosts else "-"
        rps_val = getattr(profile, "rate_limit", None)
        rps_str = f"{rps_val:.2f}" if rps_val is not None else "-"
        logger.info(
            "  %-30s  %-6s  %-12s  %-5s  %-6s  %s",
            profile.domain,
            profile.media_type,
            strat,
            str(profile.effective_crawl_depth),
            rps_str,
            cdn_str,
        )
    logger.info(sep)

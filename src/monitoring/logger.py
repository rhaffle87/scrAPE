from __future__ import annotations

import logging
import sys
from pathlib import Path

# Root logger name used when no specific name is requested
_ROOT = "scraper"

# Default log directory (relative to the project root where main.py lives)
_DEFAULT_LOG_DIR = Path("logs")
_DEFAULT_LOG_FILE = "logs.txt"


def configure_logging(
    level: int = logging.DEBUG,
    log_dir: Path | None = None,
    log_file: str = _DEFAULT_LOG_FILE,
) -> Path:
    """Configure the root logger with both console and rotating file handlers.

    Parameters
    ----------
    level:
        Minimum log level captured by *both* handlers.
    log_dir:
        Directory in which to create ``log_file``.  Defaults to ``logs/``
        relative to the current working directory.
    log_file:
        Filename for the persistent log.  Defaults to ``logs.txt``.

    Returns
    -------
    Path
        Absolute path to the log file being written.
    """
    log_dir = (log_dir or _DEFAULT_LOG_DIR).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    root = logging.getLogger()
    root.setLevel(level)

    # Suppress verbose third-party logs
    logging.getLogger("httpcore").setLevel(logging.WARNING)

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

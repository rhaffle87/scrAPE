from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

# Add src to python path to resolve modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    CACHE_DIR,
    CONCURRENT_DOWNLOADS,
    CONCURRENT_PAGES_PER_BATCH,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_MAX_RESULTS,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_RUNS_SUBDIR,
    MAX_CRAWL_DEPTH,
    MAX_PAGE_FETCHES,
    OUTPUT_DIR,
)
from core.engine import ScrapingEngine
from storage.csv_writer import write_csv
from storage.json_writer import write_json
from utils.logger import (
    configure_logging,
    get_logger,
    log_run_start,
    log_run_end,
    log_domain_profile_summary,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="scrAPE — Collect public image and video URLs for a keyword query."
    )
    parser.add_argument("--keyword", default="", help="Keyword query to search for.")
    parser.add_argument(
        "--login", type=str, metavar="DOMAIN", help="Interactive headful login for the specified domain to save session cookies."
    )
    parser.add_argument(
        "--inject-cookies", type=Path, metavar="FILE", help="Import a JSON or Netscape cookies.txt file."
    )
    parser.add_argument(
        "--domain", type=str, help="Domain to associate with the injected cookies (required if using --inject-cookies)."
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=DEFAULT_MAX_RESULTS,
        help="Maximum number of media items per type to keep. Use 0 for unlimited.",
    )
    parser.add_argument(
        "--output",
        choices=["json", "csv", "both"],
        default=DEFAULT_OUTPUT_FORMAT,
        help="Output format.",
    )
    parser.add_argument(
        "--download-media",
        action="store_true",
        help="Download discovered media into the output directory.",
    )
    parser.add_argument(
        "--seed-url",
        action="append",
        default=[],
        help="Seed page URL to scrape directly. Repeat for multiple URLs.",
    )
    parser.add_argument(
        "--seed-file",
        type=Path,
        help="Text file containing one seed URL per line.",
    )
    parser.add_argument(
        "--seed-domain",
        action="append",
        default=[],
        help="Additional domain roots to treat as in-scope for strict-domain mode.",
    )
    parser.add_argument(
        "--allow-domain",
        action="append",
        default=[],
        help="Restrict scraping to these domains. Repeat for multiple domains.",
    )
    parser.add_argument(
        "--block-domain",
        action="append",
        default=[],
        help="Skip these domains. Repeat for multiple domains.",
    )
    parser.add_argument(
        "--entity-token",
        action="append",
        default=[],
        help="Extra name/entity token to boost relevance scoring. Repeat as needed.",
    )
    parser.add_argument(
        "--skip-search",
        action="store_true",
        help="Disable keyword search and only scrape provided seed URLs.",
    )
    parser.add_argument(
        "--page-limit",
        type=int,
        default=MAX_PAGE_FETCHES,
        help="Maximum number of pages to visit during the crawl. Use 0 for unlimited.",
    )
    parser.add_argument(
        "--crawl-depth",
        type=int,
        default=MAX_CRAWL_DEPTH,
        help="Maximum depth for recursive link traversal. Use 0 for unlimited.",
    )
    parser.add_argument(
        "--strict-domain",
        action="store_true",
        help="Keep crawl candidates inside the seed domain set.",
    )
    parser.add_argument(
        "--site-tree-only",
        action="store_true",
        help="Keep discovered links within the same seed path subtree.",
    )
    parser.add_argument(
        "--domain-delay",
        action="append",
        default=[],
        metavar="DOMAIN=SECONDS",
        help=(
            "Override the per-domain request rate. Format: domain=seconds_per_request. "
            "Example: --domain-delay example.com=3.0. Repeat for multiple domains."
        ),
    )
    parser.add_argument(
        "--proxy",
        type=str,
        help="A single HTTP/SOCKS proxy URL to use for all requests.",
    )
    parser.add_argument(
        "--proxy-list",
        type=Path,
        help="A text file containing one proxy URL per line. The system will rotate through them on failures.",
    )
    parser.add_argument(
        "--capsolver-key",
        type=str,
        help="API key for CapSolver to automatically solve captchas.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=CONCURRENT_PAGES_PER_BATCH,
        metavar="N",
        help=f"Number of pages to fetch concurrently (default: {CONCURRENT_PAGES_PER_BATCH}).",
    )
    parser.add_argument(
        "--dl-workers",
        type=int,
        default=CONCURRENT_DOWNLOADS,
        metavar="N",
        help=f"Number of media files to download concurrently (default: {CONCURRENT_DOWNLOADS}).",
    )
    parser.add_argument(
        "--force-search",
        action="store_true",
        help=(
            "Force DuckDuckGo keyword search even when a seed file is present. "
            "By default, search is disabled automatically when seeds are loaded "
            "to keep the crawl narrowly focused on the listed domains."
        ),
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Wipe the entire cache directory before starting the crawl.",
    )
    parser.add_argument(
        "--ignore-robots",
        action="store_true",
        help="Bypass robots.txt rules and fetch all URLs.",
    )
    parser.add_argument(
        "--use-state-cache",
        action="store_true",
        help="Use a persistent SQLite state cache to prevent re-crawling URLs across runs.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Force the browser to run in headless mode (overrides platform defaults).",
    )
    parser.add_argument(
        "--stealth-headful",
        action="store_true",
        help="Run stealth browser fallbacks (DrissionPage, Helium, Crawl4AI) in headful mode (visible browser).",
    )
    parser.add_argument(
        "--validate-seed",
        type=Path,
        metavar="FILE",
        help="Validate the syntax and annotations of the specified seed file, then exit.",
    )
    return parser


def load_seed_urls(seed_file: Path | None, seed_urls: list[str]) -> list[str]:
    collected = [url.strip() for url in seed_urls if url.strip()]
    if seed_file is None:
        return collected
    file_urls = [
        line.strip()
        for line in seed_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return [*collected, *file_urls]


def dispose_unnecessary_cache(cache_dir: Path, ttl_seconds: float, logger) -> None:
    """Scan CACHE_DIR and remove expired or invalid cache files."""
    if not cache_dir.exists():
        return
    import time

    now = time.time()
    deleted_count = 0
    error_count = 0
    for path in cache_dir.iterdir():
        if path.is_file() and path.suffix == ".cache":
            try:
                if now - path.stat().st_mtime > ttl_seconds:
                    path.unlink()
                    deleted_count += 1
            except Exception:
                error_count += 1
    if deleted_count > 0:
        logger.info(
            "Automatically disposed %d expired cache files from %s.",
            deleted_count,
            cache_dir,
        )
    if error_count > 0:
        logger.warning(
            "Failed to delete %d cache files due to permission or system errors.",
            error_count,
        )


def main() -> None:
    from datetime import datetime, timezone

    # Generate run_id early so we can use it for the log file
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    log_file = f"run_{run_id}.log"
    log_path = configure_logging(log_dir=Path("logs"), log_file=log_file)
    logger = get_logger(__name__)
    logger.info("Logging to file: %s", log_path)

    args = build_parser().parse_args()

    if args.headless:
        import utils.http_client
        utils.http_client.FORCE_HEADLESS = True

    if args.stealth_headful:
        import utils.http_client
        utils.http_client.STEALTH_HEADFUL = True

    if args.validate_seed:
        from core.seed_manifest import SeedManifest
        warnings = SeedManifest.validate(args.validate_seed)
        if warnings:
            logger.error("Validation failed for seed file '%s':", args.validate_seed)
            for w in warnings:
                logger.error("  - %s", w)
            sys.exit(1)
        else:
            logger.info("Seed file '%s' is valid!", args.validate_seed)
            sys.exit(0)

    if args.login:
        from cli.auth import perform_interactive_login
        perform_interactive_login(args.login)
        return

    if args.inject_cookies:
        if not args.domain:
            logger.error("--domain is required when using --inject-cookies")
            sys.exit(1)
        from cli.auth import import_cookies
        import_cookies(args.domain, args.inject_cookies)
        return
        
    if not args.keyword and not args.seed_file and not args.seed_url:
        logger.error("--keyword, --seed-file, or --seed-url must be provided.")
        sys.exit(1)

    # Clear cache if requested, or automatically dispose expired cache
    if args.clear_cache:
        logger.info("Clearing entire cache directory: %s", CACHE_DIR)
        if CACHE_DIR.exists():
            import shutil

            try:
                shutil.rmtree(CACHE_DIR)
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                logger.info("Cache directory cleared successfully.")
            except Exception as exc:
                logger.warning("Failed to clear cache directory: %s", exc)
    else:
        dispose_unnecessary_cache(CACHE_DIR, DEFAULT_CACHE_TTL_SECONDS, logger)

    import re
    from urllib.parse import quote_plus

    keyword_slug = (
        re.sub(r"[^a-zA-Z0-9]+", "_", args.keyword.strip().lower()).strip("_")
        or "query"
    )
    seeds_folder = Path("seeds")
    dedicated_seed_file = seeds_folder / f"{keyword_slug}.txt"

    active_seed_file = args.seed_file
    is_seed_context = (args.seed_file is not None) or args.skip_search

    if is_seed_context and active_seed_file is None:
        if dedicated_seed_file.exists():
            active_seed_file = dedicated_seed_file
            logger.info("Using dedicated seed file: %s", active_seed_file)
        else:
            root_template_file = Path("seed.txt")
            if root_template_file.exists():
                try:
                    template_content = root_template_file.read_text(
                        encoding="utf-8"
                    )
                    q_param = quote_plus(args.keyword)
                    path_param = re.sub(
                        r"[^a-zA-Z0-9]+", "-", args.keyword.strip().lower()
                    ).strip("-")
                    keyword_title = args.keyword.title()
    
                    lines = []
                    for line in template_content.splitlines():
                        if line.strip().startswith("#"):
                            updated = line.replace("Apple", keyword_title).replace(
                                "apple", args.keyword.lower()
                            )
                            lines.append(updated)
                        else:
                            if not line.strip():
                                lines.append(line)
                                continue
                            url = line.strip()
                            if "?" in url:
                                parts = url.split("?", 1)
                                path = (
                                    parts[0]
                                    .replace("apple", path_param)
                                    .replace("Apple", path_param)
                                )
                                query = (
                                    parts[1]
                                    .replace("apple", q_param)
                                    .replace("Apple", q_param)
                                )
                                url = f"{path}?{query}"
                            else:
                                url = url.replace("apple", path_param).replace(
                                    "Apple", path_param
                                )
                            lines.append(url)
    
                    seeds_folder.mkdir(parents=True, exist_ok=True)
                    dedicated_seed_file.write_text(
                        "\n".join(lines), encoding="utf-8"
                    )
                    logger.info(
                        "Created dedicated seed file: %s", dedicated_seed_file
                    )
                    active_seed_file = dedicated_seed_file
                except Exception as exc:
                    logger.warning(
                        "Could not auto-generate dedicated seed file: %s", exc
                    )
            else:
                logger.warning(
                    "Root template seed.txt not found. Skipping dedicated seed file creation."
                )
    seed_urls = load_seed_urls(active_seed_file, args.seed_url)

    # ── Manifest-driven focused-mode ─────────────────────────────────────
    # Parse the seed file annotations into structured domain profiles.
    # Then automatically enforce:
    #   1. skip-search (unless --force-search is passed)
    #   2. allow_domains locked to exactly the listed sites + their CDN hosts
    #   3. entity_tokens enriched from the manifest subject header
    manifest = None
    domain_profiles: dict = {}
    if active_seed_file is not None and active_seed_file.exists():
        try:
            from core.seed_manifest import SeedManifest

            # Perform non-blocking validation of the seed file at runtime
            seed_warnings = SeedManifest.validate(active_seed_file)
            if seed_warnings:
                logger.warning("Seed file '%s' has validation warnings:", active_seed_file)
                for w in seed_warnings:
                    logger.warning("  - %s", w)

            manifest = SeedManifest.from_file(active_seed_file)
            domain_profiles = manifest.domain_map
            log_domain_profile_summary(logger, manifest)

            # Filter out seed URLs belonging to disabled domains
            disabled_domains = {p.domain for p in manifest.domains if p.disabled}
            if disabled_domains:
                filtered_urls = []
                for u in seed_urls:
                    from urllib.parse import urlparse

                    host = urlparse(u).netloc.lower()
                    if host not in disabled_domains:
                        filtered_urls.append(u)
                    else:
                        logger.info(
                            "Skipping seed URL belonging to disabled domain: %s", u
                        )
                seed_urls = filtered_urls

            # 1. Auto-disable broad search for speed/focus
            if not getattr(args, "force_search", False) and manifest.domains:
                logger.info(
                    "Seed manifest loaded (%d domains) — disabling DuckDuckGo broad search. "
                    "Pass --force-search to override.",
                    len(manifest.domains),
                )
                args.skip_search = True

            # 2. Always lock allow_domains to manifest hosts (even with --force-search)
            #    unless the user explicitly provided --allow-domain flags.
            if manifest.domains and not args.allow_domain:
                args.allow_domain = manifest.all_allowed_hosts
                logger.info(
                    "Auto-locked allow_domains to %d hosts from seed manifest.",
                    len(args.allow_domain),
                )

            # 3. Auto-inject entity tokens from manifest subject header
            manifest_tokens = [
                t for t in manifest.entity_tokens if t not in args.entity_token
            ]
            if manifest_tokens:
                args.entity_token = [*manifest_tokens, *args.entity_token]
                logger.info(
                    "Auto-injected entity tokens from manifest: %s", manifest_tokens
                )

        except Exception as exc:
            logger.warning(
                "Could not parse seed manifest from %s: %s", active_seed_file, exc
            )
    # ─────────────────────────────────────────────────────────────────────

    domain_delays: dict[str, float] = {}
    for entry in args.domain_delay:
        if "=" not in entry:
            logger.warning(
                "Ignoring malformed --domain-delay value '%s' (expected DOMAIN=SECONDS)",
                entry,
            )
            continue
        domain, _, raw_seconds = entry.partition("=")
        try:
            domain_delays[domain.strip().lower()] = float(raw_seconds.strip())
        except ValueError:
            logger.warning(
                "Ignoring --domain-delay '%s': seconds value is not a valid float",
                entry,
            )

    if manifest:
        for profile in manifest.domains:
            if profile.rate_limit is not None and profile.domain not in domain_delays:
                domain_delays[profile.domain] = 1.0 / profile.rate_limit
                logger.info(
                    "Auto-set rate limit for %s to %.2f req/s (%.2f s delay) from manifest.",
                    profile.domain,
                    profile.rate_limit,
                    1.0 / profile.rate_limit,
                )
            # Register Cloudflare-blocked domains so HttpClient skips Crawl4AI fallback
            if getattr(profile, "cloudflare_blocked", False):
                from utils.http_client import HttpClient

                HttpClient.register_cloudflare_blocked(profile.domain)
                logger.info(
                    "Domain '%s' flagged cloudflare_blocked — Crawl4AI fallback disabled.",
                    profile.domain,
                )

    engine = ScrapingEngine(
        domain_delays=domain_delays or None,
        workers=args.workers,
        ignore_robots=args.ignore_robots,
        use_state_cache=args.use_state_cache,
        proxy=args.proxy,
        proxy_list=str(args.proxy_list) if args.proxy_list else None,
        capsolver_key=args.capsolver_key,
    )
    engine.downloader.workers = args.dl_workers

    log_run_start(
        logger,
        keyword=args.keyword,
        seed_count=len(seed_urls),
        extra={
            "seed_file": active_seed_file,
            "max_results": args.max_results or "unlimited",
            "page_limit": args.page_limit or "unlimited",
            "crawl_depth": args.crawl_depth or "unlimited",
            "workers": args.workers,
            "dl_workers": args.dl_workers,
            "download_media": args.download_media,
            "skip_search": args.skip_search,
            "strict_domain": args.strict_domain,
        },
    )

    _run_start = time.monotonic()
    result = engine.run(
        keyword=args.keyword,
        max_results=args.max_results,
        output_format=args.output,
        download_media=args.download_media,
        seed_urls=seed_urls,
        seed_domains=args.seed_domain,
        allow_domains=args.allow_domain,
        block_domains=args.block_domain,
        entity_tokens=args.entity_token,
        use_search=not args.skip_search,
        page_limit=args.page_limit,
        crawl_depth=args.crawl_depth,
        strict_domain=args.strict_domain,
        site_tree_only=args.site_tree_only,
        seed_manifest=manifest,
        domain_profiles=domain_profiles,
        run_id=run_id,
    )
    result.duration_seconds = int(time.monotonic() - _run_start)
    metadata_updates = {
        "seed_file": str(active_seed_file) if active_seed_file else None,
        "workers": args.workers,
        "dl_workers": args.dl_workers,
        "page_limit": args.page_limit,
        "crawl_depth": args.crawl_depth,
        "max_results": args.max_results,
        "entity_tokens": args.entity_token,
        "download_media": args.download_media,
    }
    result.run_metadata.update(metadata_updates)

    output_root = OUTPUT_DIR / result.keyword_slug / DEFAULT_RUNS_SUBDIR / result.run_id
    output_root.mkdir(parents=True, exist_ok=True)

    if args.output in {"json", "both"}:
        write_json(result, output_root / "results.json")
    if args.output in {"csv", "both"}:
        write_csv(result, output_root)

    import json

    with open(output_root / "domain_report.json", "w", encoding="utf-8") as f:
        json.dump(result.domain_stats, f, indent=2)

    # Generate post-run summary observability report and write run_summary.json
    from core.run_summary import generate_run_summary

    crawl_dur = result.run_metadata.get("crawl_duration_seconds", 0.0)
    download_dur = result.run_metadata.get("download_duration_seconds", 0.0)
    generate_run_summary(result, output_root, crawl_dur, download_dur)

    logger.info("Scraping completed. Results written to %s", output_root.resolve())
    log_run_end(
        logger,
        keyword=args.keyword,
        images=len(result.images),
        videos=len(result.videos),
        output_dir=output_root.resolve(),
    )


if __name__ == "__main__":
    main()

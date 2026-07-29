import sys
import time
import subprocess
import argparse
import os
import json
import signal
import threading
from datetime import datetime, timedelta
from pathlib import Path

shutdown_event = threading.Event()


def signal_handler(signum, frame):
    print(f"\n[{datetime.now().isoformat()}] Received shutdown signal. Exiting gracefully...")
    shutdown_event.set()


# Add src to python path to resolve modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_watchdog_config(config_path: str = "data/domain_config.json") -> dict:
    """Load watchdog default configuration from domain_config.json.

    Resolves the path relative to CWD first; falls back to project root inferred
    from this module's location so tests pass regardless of working directory.
    """
    p = Path(config_path)
    if not p.is_absolute() and not p.exists():
        _project_root = Path(__file__).resolve().parent.parent.parent
        p = _project_root / config_path
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data.get("watchdog", {})
        except Exception:
            pass
    return {}


class AdaptiveBackoffTracker:
    """Tracks per-subject harvest history and calculates adaptive next-run delay."""

    def __init__(
        self,
        min_interval_s: float = 60,
        max_interval_s: float = 86400,
        backoff_factor: float = 2.0,
    ):
        self.min_interval_s = min_interval_s
        self.max_interval_s = max_interval_s
        self.backoff_factor = backoff_factor
        self.subject_delays: dict[str, float] = {}

    def get_next_delay(self, subject: str, harvest_yield: int) -> float:
        current = self.subject_delays.get(subject, self.min_interval_s)
        if harvest_yield > 0:
            next_delay = self.min_interval_s
        else:
            next_delay = min(self.max_interval_s, current * self.backoff_factor)
        self.subject_delays[subject] = next_delay
        return next_delay


def broadcast_watchdog_event(event_name: str, payload: dict) -> None:
    """Broadcast watchdog status/alert event over SSE if frontend broadcaster is available."""
    try:
        from frontend.app import broadcaster

        broadcaster.broadcast(event_name, payload)
    except Exception:
        pass


def discover_rotation_targets(seeds_dir: str) -> list[tuple[str, str]]:
    """Scan seeds_dir for .txt seed manifest files and return list of (keyword, seed_file_path)."""
    p = Path(seeds_dir)
    if not p.exists() or not p.is_dir():
        return []
    targets = []
    for f in sorted(p.glob("*.txt")):
        keyword = f.stem.replace("_", " ")
        targets.append((keyword, str(f)))
    return targets


def parse_latest_run_yield(keyword: str) -> tuple[int, int, int] | None:
    """Parse latest run results for subject to extract (images, videos, rejections)."""
    slug = keyword.replace(" ", "_").lower()
    sub_dir = Path("output") / slug / "runs"
    if not sub_dir.exists():
        return None
    run_folders = sorted([d for d in sub_dir.iterdir() if d.is_dir()])
    if not run_folders:
        return None
    latest_run = run_folders[-1]
    res_json = latest_run / "results.json"
    if res_json.exists():
        try:
            data = json.loads(res_json.read_text(encoding="utf-8"))
            imgs = len(data.get("images", []))
            vids = len(data.get("videos", []))
            rejs = len(data.get("rejected_items", []))
            return imgs, vids, rejs
        except Exception:
            pass
    return None


def run_scraper(
    keyword: str, seed_file: str | None, download_media: bool, extra_args: list[str]
) -> int:
    print(f"[{datetime.now().isoformat()}] Starting full scrAPE run for subject '{keyword}'...")
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "main.py"),
        "--keyword",
        keyword,
        "--use-state-cache",
    ]
    if seed_file:
        cmd.extend(["--seed-file", seed_file])
    if download_media:
        cmd.append("--download-media")
    if extra_args:
        cmd.extend(extra_args)

    return_code = -1
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )

        start_time = time.time()
        timeout = int(os.environ.get("SCRAPE_TIMEOUT", 1800))

        while True:
            if shutdown_event.is_set():
                print(
                    f"[{datetime.now().isoformat()}] Shutdown requested during active scrape. Terminating process gracefully..."
                )
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                process.wait()
                break

            if time.time() - start_time > timeout:
                print(
                    f"[{datetime.now().isoformat()}] ERROR: scrAPE timed out after {timeout} seconds. Terminating process..."
                )
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                process.wait()
                break

            if process.stdout is None:
                break
            line = process.stdout.readline()
            if not line:
                break
            sys.stdout.write(line)
            sys.stdout.flush()

        return_code = process.wait()
        if return_code == 0:
            print(f"[{datetime.now().isoformat()}] scrAPE run finished successfully.")
        else:
            print(
                f"[{datetime.now().isoformat()}] scrAPE run failed with exit code {return_code}."
            )

        print(f"[{datetime.now().isoformat()}] Scraping run complete.")

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Unexpected error during run: {e}")

    return return_code


def notify_telegram(message: str) -> None:
    """Send alert via TelegramBotNotifier and multi-channel NotificationPipeline."""
    try:
        from utils.telegram_bot import TelegramBotNotifier

        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        notifier = TelegramBotNotifier(token, chat_id)
        if notifier.is_configured():
            notifier.send_message(message)
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Telegram alert dispatch failed: {e}")

    try:
        from utils.notification_manager import NotificationPipeline, TelegramNotifier

        pipeline = NotificationPipeline()
        pipeline.providers = [p for p in pipeline.providers if not isinstance(p, TelegramNotifier)]
        pipeline.notify_watchdog_status(message)
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Multi-channel alert dispatch failed: {e}")


def notify_telegram_summary(
    keyword: str, cycle: int, code: int, yield_info: tuple[int, int, int] | None
) -> None:
    """Send structured summary digest card after a subject watchdog cycle."""
    if yield_info:
        imgs, vids, rejs = yield_info
        status = "✅ SUCCESS" if code == 0 else f"⚠️ FAILED ({code})"
        msg = (
            f"<b>📊 Watchdog Cycle #{cycle} Complete</b>\n"
            f"<b>Subject:</b> <code>{keyword}</code>\n"
            f"<b>Status:</b> {status}\n"
            f"<b>Images Harvested:</b> {imgs}\n"
            f"<b>Videos Harvested:</b> {vids}\n"
            f"<b>Rejections Filtered:</b> {rejs}"
        )
    else:
        msg = f"<b>📊 Watchdog Cycle #{cycle} Complete</b>\n<b>Subject:</b> <code>{keyword}</code>\n<b>Return Code:</b> {code}"
    notify_telegram(msg)


def main():
    wd_cfg = load_watchdog_config()

    parser = argparse.ArgumentParser(
        description="Sleep Monitoring Agent for scrAPE — run scrapes continuously at set intervals."
    )
    parser.add_argument(
        "--keyword",
        "-k",
        default=os.environ.get("SCRAPE_KEYWORD"),
        help="The keyword / subject name to scrape. Can also be set via SCRAPE_KEYWORD environment variable.",
    )
    parser.add_argument(
        "--seed-file",
        "-s",
        default=os.environ.get("SCRAPE_SEED_FILE"),
        help="Path to the matching seed manifest file. Can also be set via SCRAPE_SEED_FILE environment variable.",
    )
    parser.add_argument(
        "--seeds-dir",
        default=os.environ.get("SCRAPE_SEEDS_DIR"),
        help="Directory containing seed manifest files for automatic round-robin rotation across watch cycles.",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=int(os.environ.get("SCRAPE_INTERVAL", wd_cfg.get("min_interval_s", 60))),
        help="Check/run interval in seconds (default: 60).",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=int(os.environ.get("SCRAPE_TIMEOUT", 1800)),
        help="Maximum runtime per execution run in seconds (default: 1800).",
    )
    parser.add_argument(
        "--download-media",
        "-d",
        action="store_true",
        help="Enable downloading of discovered media.",
    )
    parser.add_argument(
        "--flush-cache",
        action="store_true",
        help="Flush the state cache database before starting the watchdog.",
    )
    parser.add_argument(
        "--auto-prune-cache",
        action="store_true",
        default=True,
        help="Enable periodic StateCache pruning and vacuuming across watch cycles (default: True).",
    )
    parser.add_argument(
        "--prune-interval-cycles",
        type=int,
        default=5,
        help="Number of watch cycles between automatic cache pruning (default: 5).",
    )
    parser.add_argument(
        "--ttl-days",
        type=int,
        default=int(wd_cfg.get("ttl_days", 7)),
        help="State cache URL retention TTL in days (default: 7).",
    )
    parser.add_argument(
        "--adaptive-backoff",
        action="store_true",
        default=True,
        help="Enable adaptive yield-based backoff delay per subject (default: True).",
    )

    args, extra_args = parser.parse_known_args()

    rotation_targets = []
    if args.seeds_dir:
        rotation_targets = discover_rotation_targets(args.seeds_dir)

    if not args.keyword and not rotation_targets:
        parser.print_help()
        print(
            "\nERROR: --keyword (or SCRAPE_KEYWORD env var) or a valid --seeds-dir is required to run the monitoring agent."
        )
        sys.exit(1)

    os.environ["SCRAPE_TIMEOUT"] = str(args.timeout)

    if args.flush_cache:
        from storage.state_cache import StateCache

        StateCache().flush()

    backoff_tracker = AdaptiveBackoffTracker(
        min_interval_s=args.interval,
        max_interval_s=wd_cfg.get("max_interval_s", 86400),
        backoff_factor=wd_cfg.get("backoff_factor", 2.0),
    )

    print(
        f"[{datetime.now().isoformat()}] Sleep Monitoring Agent (scrAPE) initialized."
    )
    if rotation_targets:
        print(f"Seed Rotation Active: {len(rotation_targets)} subjects discovered in '{args.seeds_dir}'.")
    else:
        print(f"Target Keyword: {args.keyword}")
        if args.seed_file:
            print(f"Seed File: {args.seed_file}")
    print(f"Interval: {args.interval}s | TTL: {args.ttl_days} days | Timeout: {args.timeout}s")
    if extra_args:
        print(f"Pass-through arguments: {extra_args}")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    cycle_count = 0

    try:
        while not shutdown_event.is_set():
            if rotation_targets:
                target_keyword, target_seed = rotation_targets[cycle_count % len(rotation_targets)]
            else:
                target_keyword = args.keyword
                target_seed = args.seed_file

            cycle_count += 1
            print(f"\n[{datetime.now().isoformat()}] --- WATCHDOG CYCLE #{cycle_count} [{target_keyword}] ---")

            # Periodic 7-day TTL cache maintenance
            if args.auto_prune_cache and (cycle_count % args.prune_interval_cycles == 0):
                try:
                    from storage.state_cache import StateCache

                    cache = StateCache()
                    pruned = cache.prune_expired(max_age_days=args.ttl_days)
                    db_size = cache.vacuum_db()
                    print(
                        f"[{datetime.now().isoformat()}] StateCache Maintenance (TTL={args.ttl_days}d): Pruned {pruned} stale URLs. DB size: {db_size} bytes."
                    )
                    broadcast_watchdog_event(
                        "watchdog", {"type": "prune", "pruned": pruned, "db_size": db_size}
                    )
                except Exception as c_err:
                    print(f"[{datetime.now().isoformat()}] StateCache Maintenance Error: {c_err}")

            broadcast_watchdog_event(
                "watchdog",
                {
                    "type": "cycle_start",
                    "cycle": cycle_count,
                    "keyword": target_keyword,
                    "seed_file": target_seed,
                },
            )

            code = run_scraper(target_keyword, target_seed, args.download_media, extra_args)
            yield_info = parse_latest_run_yield(target_keyword)

            if wd_cfg.get("telegram_digest", True):
                notify_telegram_summary(target_keyword, cycle_count, code, yield_info)

            broadcast_watchdog_event(
                "watchdog",
                {
                    "type": "cycle_complete",
                    "cycle": cycle_count,
                    "keyword": target_keyword,
                    "return_code": code,
                    "yield": yield_info,
                },
            )

            if shutdown_event.is_set():
                break

            total_harvest = (yield_info[0] + yield_info[1]) if yield_info else 0
            sleep_delay = backoff_tracker.get_next_delay(target_keyword, total_harvest) if args.adaptive_backoff else float(args.interval)

            next_run = datetime.now() + timedelta(seconds=sleep_delay)
            print(
                f"[{datetime.now().isoformat()}] Next cycle scheduled at {next_run.isoformat()}. Adaptive sleep for {sleep_delay:.0f}s..."
            )

            if shutdown_event.wait(sleep_delay):
                break

    except KeyboardInterrupt:
        print(
            f"\n[{datetime.now().isoformat()}] Sleep Monitoring Agent stopped by user request."
        )
        shutdown_event.set()


if __name__ == "__main__":
    main()

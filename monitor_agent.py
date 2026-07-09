import sys
import time
import subprocess
import argparse
import os
from datetime import datetime, timedelta


def run_scraper(
    keyword: str, seed_file: str | None, download_media: bool, extra_args: list[str]
) -> None:
    print(f"[{datetime.now().isoformat()}] Starting full scrAPE run...")
    cmd = [
        sys.executable,
        "main.py",
        "--keyword",
        keyword,
    ]
    if seed_file:
        cmd.extend(["--seed-file", seed_file])
    if download_media:
        cmd.append("--download-media")
    if extra_args:
        cmd.extend(extra_args)

    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )

        start_time = time.time()
        timeout = int(os.environ.get("SCRAPE_TIMEOUT", 1800))

        while True:
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

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Unexpected error during run: {e}")


def main():
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
        "--interval",
        "-i",
        type=int,
        default=int(os.environ.get("SCRAPE_INTERVAL", 60)),
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

    args, extra_args = parser.parse_known_args()

    if not args.keyword:
        parser.print_help()
        print(
            "\nERROR: --keyword (or SCRAPE_KEYWORD env var) is required to run the monitoring agent."
        )
        sys.exit(1)

    os.environ["SCRAPE_TIMEOUT"] = str(args.timeout)

    print(
        f"[{datetime.now().isoformat()}] Sleep Monitoring Agent (scrAPE) initialized."
    )
    print(f"Target Keyword: {args.keyword}")
    if args.seed_file:
        print(f"Seed File: {args.seed_file}")
    print(f"Interval: {args.interval} seconds | Timeout: {args.timeout} seconds")
    if extra_args:
        print(f"Pass-through arguments: {extra_args}")

    try:
        # Initial immediate run
        run_scraper(args.keyword, args.seed_file, args.download_media, extra_args)

        while True:
            next_run = datetime.now() + timedelta(seconds=args.interval)
            print(
                f"[{datetime.now().isoformat()}] Next run scheduled at {next_run.isoformat()}. Sleeping..."
            )

            # Sleep in small increments to allow responsive Ctrl+C
            sleep_elapsed = 0
            while sleep_elapsed < args.interval:
                time.sleep(5)
                sleep_elapsed += 5

            run_scraper(args.keyword, args.seed_file, args.download_media, extra_args)
    except KeyboardInterrupt:
        print(
            f"\n[{datetime.now().isoformat()}] Sleep Monitoring Agent stopped by user request."
        )


if __name__ == "__main__":
    main()

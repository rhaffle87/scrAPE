"""
worker.py — CLI entrypoint for running distributed worker daemons.

Usage:
  python -m src.cli.worker --broker redis://127.0.0.1:6379/0 --role all --group scraper_cluster
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import signal
import sys

# Bootstrap sys.path to resolve src and root modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.distributed_worker import DistributedWorkerNode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOGGER = logging.getLogger("worker_daemon")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="scrAPE Distributed Worker Node Daemon")
    parser.add_argument("--broker", default="redis://127.0.0.1:6379/0", help="Redis broker URL")
    parser.add_argument("--role", default="all", choices=["crawl", "download", "all"], help="Worker task role")
    parser.add_argument("--group", default="scraper_cluster", help="Consumer group name")
    parser.add_argument("--name", default=None, help="Custom consumer name")
    parser.add_argument("--lease-ttl", type=int, default=30, help="Task lease TTL in seconds")
    parser.add_argument("--max-tasks", type=int, default=None, help="Optional maximum tasks to process before exit")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate broker connectivity, assert/create stream consumer groups, log ready status, and exit 0",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    parsed = parse_args(args)
    LOGGER.info("Initializing DistributedWorkerNode (role=%s, group=%s)...", parsed.role, parsed.group)

    worker = DistributedWorkerNode(
        broker_url=parsed.broker,
        role=parsed.role,
        group_name=parsed.group,
        consumer_name=parsed.name,
        lease_ttl=parsed.lease_ttl,
    )

    if parsed.dry_run:
        LOGGER.info("Executing --dry-run: verifying broker connectivity and stream consumer groups...")
        client = getattr(worker.broker, "_client", None)
        if client is None:
            LOGGER.error("Dry-run failed: Unable to connect to Redis broker at %s", parsed.broker)
            return 1
        try:
            client.ping()
        except Exception as exc:
            LOGGER.error("Dry-run failed: Redis ping failed (%s)", exc)
            return 1

        for stream in worker.streams:
            if hasattr(worker.broker, "_ensure_group"):
                worker.broker._ensure_group(stream)
            LOGGER.info("Verified consumer group '%s' for stream '%s'", parsed.group, stream)

        LOGGER.info(
            "Dry-run SUCCESS: Worker '%s' is ready. Connected to %s, consumer group '%s' verified.",
            worker.worker_id,
            parsed.broker,
            parsed.group,
        )
        return 0

    def _signal_handler(sig, frame):
        LOGGER.info("Received termination signal (%s). Initiating graceful worker shutdown...", sig)
        worker.shutdown()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
    except Exception:
        pass

    try:
        worker.run(max_tasks=parsed.max_tasks)
    except KeyboardInterrupt:
        worker.shutdown()

    return 0


if __name__ == "__main__":
    sys.exit(main())

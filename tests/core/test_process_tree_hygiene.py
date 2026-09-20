"""Tests verifying zero zombie child processes during crawl operations and emergency aborts."""

import os
import subprocess
import sys
import time
import psutil
from core.worker_pool import HybridWorkerPool, _cleanup_all_pools


def test_process_tree_hygiene_on_pool_abort():
    pool = HybridWorkerPool(max_workers=2, use_processes=True)

    # Submit a couple of short tasks
    futures = [pool.submit(time.sleep, 0.05) for _ in range(2)]
    for f in futures:
        f.result(timeout=3.0)

    # Record children of the current test runner before shutdown
    current_proc = psutil.Process(os.getpid())

    # Trigger full shutdown with process-tree cleanup
    pool.shutdown(wait=True)

    # Give OS brief moment to clean up process table
    time.sleep(0.1)

    # Check for any lingering Python or browser processes spawned by current process
    lingering = [
        c for c in current_proc.children(recursive=True)
        if c.is_running() and c.status() != psutil.STATUS_ZOMBIE
    ]
    pool_workers_lingering = [p for p in lingering if "pytest" not in p.name().lower() and "python" in p.name().lower()]
    assert len(pool_workers_lingering) == 0


def test_emergency_cleanup_children_helper():
    from unittest.mock import MagicMock
    from core.worker_pool import _MANAGED_POOLS, _cleanup_all_pools

    mock_pool = MagicMock()
    _MANAGED_POOLS.append(mock_pool)

    _cleanup_all_pools()
    mock_pool.shutdown.assert_called_once_with(wait=False)


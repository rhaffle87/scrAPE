"""Unit tests for HybridWorkerPool verifying process lifecycle, task execution, and clean termination."""

import pytest
from core.worker_pool import HybridWorkerPool


def _square_task(x: int) -> int:
    return x * x


def test_hybrid_worker_pool_process_execution():
    pool = HybridWorkerPool(max_workers=2, use_processes=True)
    try:
        futures = [pool.submit(_square_task, i) for i in range(5)]
        results = [f.result(timeout=5.0) for f in futures]
        assert results == [0, 1, 4, 9, 16]

        mem_stats = pool.get_memory_usage()
        assert "total_rss_mb" in mem_stats
        assert "worker_count" in mem_stats
    finally:
        pool.shutdown(wait=True)


def test_hybrid_worker_pool_thread_mode():
    pool = HybridWorkerPool(max_workers=2, use_processes=False)
    try:
        futures = [pool.submit(_square_task, i) for i in range(4)]
        results = [f.result(timeout=5.0) for f in futures]
        assert results == [0, 1, 4, 9]
    finally:
        pool.shutdown(wait=True)


def test_hybrid_worker_pool_zero_zombie_shutdown():
    pool = HybridWorkerPool(max_workers=2, use_processes=True)
    f = pool.submit(_square_task, 42)
    assert f.result(timeout=5.0) == 1764

    # Shutdown and verify no remaining running processes
    pool.shutdown(wait=True)

    with pytest.raises(RuntimeError, match="Cannot submit to a shutdown"):
        pool.submit(_square_task, 10)

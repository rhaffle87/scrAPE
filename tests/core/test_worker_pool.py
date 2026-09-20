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


def test_in_memory_task_broker():
    from core.worker_pool import InMemoryTaskBroker, BaseTaskBroker

    broker = InMemoryTaskBroker()
    assert isinstance(broker, BaseTaskBroker)

    broker.push_task("crawl_jobs", {"url": "https://example.com/1", "depth": 0})
    broker.push_task("crawl_jobs", {"url": "https://example.com/2", "depth": 1})
    assert broker.get_queue_length("crawl_jobs") == 2

    task1 = broker.pop_task("crawl_jobs", timeout=0.1)
    assert task1 == {"url": "https://example.com/1", "depth": 0}
    assert broker.get_queue_length("crawl_jobs") == 1

    task2 = broker.pop_task("crawl_jobs", timeout=0.1)
    assert task2 == {"url": "https://example.com/2", "depth": 1}

    # Empty queue should return None after timeout
    empty = broker.pop_task("crawl_jobs", timeout=0.01)
    assert empty is None


def test_redis_task_broker_offline_fallback():
    from core.worker_pool import RedisTaskBroker, BaseTaskBroker

    # Connect to offline/dummy port - should log warning and transparently fallback to InMemoryTaskBroker
    broker = RedisTaskBroker(redis_url="redis://127.0.0.1:59999/0")
    assert isinstance(broker, BaseTaskBroker)

    broker.push_task("distributed_queue", {"action": "parse", "id": 101})
    assert broker.get_queue_length("distributed_queue") == 1

    item = broker.pop_task("distributed_queue", timeout=0.1)
    assert item == {"action": "parse", "id": 101}


def test_get_task_broker_factory(monkeypatch):
    from core.worker_pool import get_task_broker, InMemoryTaskBroker, RedisTaskBroker

    monkeypatch.delenv("SCRAPER_REDIS_URL", raising=False)
    b1 = get_task_broker()
    assert isinstance(b1, InMemoryTaskBroker)

    b2 = get_task_broker("redis://127.0.0.1:6379/1")
    assert isinstance(b2, RedisTaskBroker)


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
    assert task1 is not None
    assert task1["url"] == "https://example.com/1"
    assert task1["depth"] == 0
    assert "_task_id" in task1

    task2 = broker.pop_task("crawl_jobs", timeout=0.1)
    assert task2 is not None
    assert task2["url"] == "https://example.com/2"
    assert task2["depth"] == 1

    assert broker.pop_task("crawl_jobs", timeout=0.01) is None


def test_redis_task_broker_offline_fallback():
    from core.worker_pool import RedisTaskBroker, BaseTaskBroker

    # Connect to offline/dummy port - should log warning and transparently fallback to InMemoryTaskBroker
    broker = RedisTaskBroker(redis_url="redis://127.0.0.1:59999/0")
    assert isinstance(broker, BaseTaskBroker)

    broker.push_task("distributed_queue", {"action": "parse", "id": 101})
    assert broker.get_queue_length("distributed_queue") == 1

    item = broker.pop_task("distributed_queue", timeout=0.1)
    assert item is not None
    assert item["action"] == "parse"
    assert item["id"] == 101
    assert "_task_id" in item


def test_get_task_broker_factory(monkeypatch):
    from core.worker_pool import get_task_broker, InMemoryTaskBroker, RedisTaskBroker, RedisStreamTaskBroker

    monkeypatch.delenv("SCRAPER_REDIS_URL", raising=False)
    b1 = get_task_broker()
    assert isinstance(b1, InMemoryTaskBroker)

    b2 = get_task_broker("redis://127.0.0.1:6379/1")
    assert isinstance(b2, (RedisTaskBroker, RedisStreamTaskBroker))


def test_validate_broker_security_ac1_2(caplog):
    """AC1.2: Assert INSECURE warning on unauthenticated non-loopback Redis configurations."""
    import logging
    from core.worker_pool import RedisStreamTaskBroker

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        # 1. Non-loopback with no password -> MUST emit INSECURE warning
        RedisStreamTaskBroker.validate_broker_security("redis://192.168.1.100:6379/0")
        assert any("INSECURE" in record.message and "192.168.1.100" in record.message for record in caplog.records)

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        # 2. Non-loopback WITH password -> MUST NOT emit INSECURE warning
        RedisStreamTaskBroker.validate_broker_security("redis://:secret_pass@192.168.1.100:6379/0")
        assert not any("INSECURE" in record.message for record in caplog.records)

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        # 3. Loopback without password -> local dev allowed, NO INSECURE warning
        RedisStreamTaskBroker.validate_broker_security("redis://127.0.0.1:6379/0")
        assert not any("INSECURE" in record.message for record in caplog.records)


def test_worker_heartbeat_and_active_count_ac1_6():
    """AC1.6: Worker heartbeat key lifecycle and active node count tracking."""
    import fakeredis
    from core.worker_pool import RedisStreamTaskBroker
    from core.distributed_worker import DistributedWorkerNode

    fake_client = fakeredis.FakeRedis()
    broker = RedisStreamTaskBroker(redis_url="redis://127.0.0.1:6379/0")
    broker._client = fake_client

    assert broker.get_active_worker_count() == 0

    worker1 = DistributedWorkerNode(broker=broker, consumer_name="worker_test_1")
    worker1.publish_heartbeat()
    assert broker.get_active_worker_count() == 1

    worker2 = DistributedWorkerNode(broker=broker, consumer_name="worker_test_2")
    worker2.publish_heartbeat()
    assert broker.get_active_worker_count() == 2

    # Simulate worker 1 graceful shutdown (deletes heartbeat key)
    worker1.shutdown()
    assert broker.get_active_worker_count() == 1

    # Simulate worker 2 crash (heartbeat expires after TTL)
    fake_client.delete(f"scrape:workers:{worker2.worker_id}")
    assert broker.get_active_worker_count() == 0


def test_gc_stale_consumers_ac1_7():
    """AC1.7: Garbage collection of stale consumers in consumer group."""
    import fakeredis
    from core.worker_pool import RedisStreamTaskBroker

    fake_client = fakeredis.FakeRedis()
    broker = RedisStreamTaskBroker(redis_url="redis://127.0.0.1:6379/0")
    broker._client = fake_client

    stream_name = "scrape:crawl_stream"
    broker._ensure_group(stream_name)

    # Simulate 50 stale worker consumers created across cluster restarts
    for i in range(50):
        fake_client.xreadgroup("scraper_cluster", f"stale_worker_{i}", {stream_name: ">"}, count=1)

    consumers_before = fake_client.xinfo_consumers(stream_name, "scraper_cluster")
    assert len(consumers_before) == 50

    # Prune stale consumers: all 50 have 0 pending and no active heartbeat key
    pruned_count = broker.gc_stale_consumers(stream_name)
    assert pruned_count == 50

    consumers_after = fake_client.xinfo_consumers(stream_name, "scraper_cluster")
    assert len(consumers_after) == 0


def test_idempotency_lock_mutual_exclusion_ac1_1():
    """AC1.1: Atomic idempotency lock ensures only first worker wins and double-write is rejected."""
    import fakeredis
    from core.worker_pool import RedisStreamTaskBroker

    fake_client = fakeredis.FakeRedis()
    broker = RedisStreamTaskBroker(redis_url="redis://127.0.0.1:6379/0")
    broker._client = fake_client

    task_id = "task_uuid_9999"

    # Worker A acquires idempotency lock
    locked_a = broker.acquire_idempotency_lock(task_id, worker_id="worker_a", ttl_seconds=60)
    assert locked_a is True

    # Worker B tries to acquire idempotency lock for the same task -> MUST FAIL
    locked_b = broker.acquire_idempotency_lock(task_id, worker_id="worker_b", ttl_seconds=60)
    assert locked_b is False

    # Idempotency key in Redis belongs to worker_a
    assert fake_client.get(f"scrape:completed:{task_id}") == b"worker_a"


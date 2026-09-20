"""Unit tests for RedisStreamTaskBroker verifying stream queuing, consumer groups, and failover."""

from unittest.mock import MagicMock, patch

from core.worker_pool import (
    BaseTaskBroker,
    InMemoryTaskBroker,
    RedisStreamTaskBroker,
    get_task_broker,
)


def test_in_memory_task_broker_stream_contract():
    broker = InMemoryTaskBroker()
    assert isinstance(broker, BaseTaskBroker)

    broker.push_task("crawl_stream", {"url": "https://example.com/p1", "depth": 0})
    item = broker.pop_task("crawl_stream", timeout=0.1)
    assert item is not None
    assert item["url"] == "https://example.com/p1"
    assert "_task_id" in item

    # ack_task should succeed
    assert broker.ack_task("crawl_stream", item["_task_id"]) is True
    # autoclaim should return empty list
    assert broker.autoclaim_abandoned_tasks("crawl_stream") == []


def test_redis_stream_broker_offline_fallback():
    broker = RedisStreamTaskBroker(redis_url="redis://127.0.0.1:59998/0")
    assert isinstance(broker, BaseTaskBroker)

    broker.push_task("crawl_stream", {"url": "https://example.com/offline", "depth": 1})
    item = broker.pop_task("crawl_stream", timeout=0.1)
    assert item is not None
    assert item["url"] == "https://example.com/offline"
    assert broker.ack_task("crawl_stream", item["_task_id"]) is True


def test_redis_stream_broker_mocked_redis_operations():
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    mock_redis.xadd.return_value = b"1695200000000-0"
    mock_redis.xlen.return_value = 1
    mock_redis.xreadgroup.return_value = [
        (b"scrape:tasks", [(b"1695200000000-0", {b"payload": b'{"url": "https://example.com/stream", "target": "img"}'})])
    ]
    mock_redis.xack.return_value = 1
    mock_redis.xautoclaim.return_value = [
        b"0-0",
        [(b"1695200000001-0", {b"payload": b'{"url": "https://example.com/reclaimed"}'})],
    ]

    mock_redis_mod = MagicMock()
    mock_redis_mod.from_url.return_value = mock_redis

    with patch.dict("sys.modules", {"redis": mock_redis_mod}):
        broker = RedisStreamTaskBroker(redis_url="redis://127.0.0.1:6379/0", group_name="test_group")
        assert broker._client is not None


        # Test push_task
        assert broker.push_task("scrape:tasks", {"url": "https://example.com/stream"}) is True
        mock_redis.xadd.assert_called_once()

        # Test pop_task
        task = broker.pop_task("scrape:tasks", timeout=0.5)
        assert task is not None
        assert task["url"] == "https://example.com/stream"
        assert task["_task_id"] == "1695200000000-0"

        # Test ack_task
        assert broker.ack_task("scrape:tasks", task["_task_id"]) is True
        mock_redis.xack.assert_called_once_with("scrape:tasks", "test_group", "1695200000000-0")

        # Test autoclaim_abandoned_tasks
        reclaimed = broker.autoclaim_abandoned_tasks("scrape:tasks", min_idle_ms=30000)
        assert len(reclaimed) == 1
        assert reclaimed[0]["url"] == "https://example.com/reclaimed"
        assert reclaimed[0]["_task_id"] == "1695200000001-0"


def test_get_task_broker_factory_streams(monkeypatch):
    monkeypatch.setenv("SCRAPER_REDIS_URL", "redis://127.0.0.1:6379/0")
    b = get_task_broker()
    assert isinstance(b, RedisStreamTaskBroker)

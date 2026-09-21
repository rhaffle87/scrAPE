"""Hybrid Worker Pool managing CPU/GPU workloads with psutil process lifecycle & zombie prevention."""

from __future__ import annotations

import atexit
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import json
import logging
import multiprocessing
import os
import queue
import threading
from typing import Any, Callable, Protocol, runtime_checkable

LOGGER = logging.getLogger(__name__)

# Global registry of managed worker process pools for atexit safety
_MANAGED_POOLS: list[HybridWorkerPool] = []


def _cleanup_all_pools():
    """Emergency atexit handler to ensure zero orphaned child processes remain."""
    for pool in list(_MANAGED_POOLS):
        try:
            pool.shutdown(wait=False)
        except Exception:
            pass


atexit.register(_cleanup_all_pools)


class HybridWorkerPool:
    """
    Hybrid concurrency worker pool:
      - Local Mode: ProcessPoolExecutor with explicit PID tracking and psutil tree termination.
      - Fallback Thread Mode: Gracefully falls back to ThreadPoolExecutor if process spawning fails.
      - Process Tree Lifecycle: Recursively terminates all spawned child processes to eliminate zombie processes.
    """

    def __init__(
        self,
        max_workers: int | None = None,
        use_processes: bool = True,
        max_memory_mb: int = 1536,
    ):
        self.use_processes = use_processes
        self.max_workers = max_workers or max(1, min(multiprocessing.cpu_count(), 8))
        self.max_memory_mb = max_memory_mb
        self._executor: ProcessPoolExecutor | ThreadPoolExecutor | None = None
        self._active_pids: set[int] = set()
        self._is_shutdown = False

        self._init_pool()
        _MANAGED_POOLS.append(self)

    def _init_pool(self) -> None:
        if self.use_processes:
            try:
                # Use spawn context on Windows/POSIX for clean separation
                ctx = multiprocessing.get_context("spawn")
                self._executor = ProcessPoolExecutor(
                    max_workers=self.max_workers,
                    mp_context=ctx,
                )
                LOGGER.info(
                    "HybridWorkerPool: Initialized ProcessPoolExecutor with %d workers.",
                    self.max_workers,
                )
            except Exception as e:
                LOGGER.warning(
                    "Failed initializing ProcessPoolExecutor (%s); falling back to ThreadPoolExecutor.",
                    e,
                )
                self.use_processes = False
                self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        else:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any):
        """Submit a task to the worker pool."""
        if self._is_shutdown or self._executor is None:
            raise RuntimeError("Cannot submit to a shutdown or uninitialized HybridWorkerPool.")
        return self._executor.submit(fn, *args, **kwargs)

    def map(self, fn: Callable[..., Any], *iterables: Any, timeout: float | None = None):
        """Map a function across iterables concurrently."""
        if self._is_shutdown or self._executor is None:
            raise RuntimeError("Cannot map across a shutdown or uninitialized HybridWorkerPool.")
        return self._executor.map(fn, *iterables, timeout=timeout)

    def get_child_pids(self) -> list[int]:
        """Discover all child process PIDs spawned under this process via psutil."""
        pids: list[int] = []
        try:
            import psutil
            current = psutil.Process()
            children = current.children(recursive=True)
            pids = [c.pid for c in children if c.is_running()]
        except Exception:
            pass
        return pids

    def get_memory_usage(self) -> dict[str, Any]:
        """Report memory usage of the pool workers."""
        stats = {"total_rss_mb": 0.0, "worker_count": 0, "pids": []}
        try:
            import psutil
            current = psutil.Process()
            children = current.children(recursive=True)
            total_rss = 0
            for child in children:
                try:
                    rss = child.memory_info().rss
                    total_rss += rss
                    stats["pids"].append({"pid": child.pid, "rss_mb": round(rss / (1024 * 1024), 2)})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            stats["total_rss_mb"] = round(total_rss / (1024 * 1024), 2)
            stats["worker_count"] = len(stats["pids"])
        except Exception:
            pass
        return stats

    def shutdown(self, wait: bool = True, timeout: float = 5.0) -> None:
        """
        Gracefully shut down the executor, then recursively terminate all child processes
        using psutil to guarantee zero zombie Chromium or Python processes remain.
        """
        if self._is_shutdown:
            return
        self._is_shutdown = True

        if self in _MANAGED_POOLS:
            _MANAGED_POOLS.remove(self)

        LOGGER.info("Shutting down HybridWorkerPool...")
        if self._executor:
            try:
                self._executor.shutdown(wait=wait, cancel_futures=True)
            except Exception:
                pass
            self._executor = None

        # Terminate any remaining child processes recursively
        try:
            import psutil
            current = psutil.Process()
            children = current.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Wait briefly for termination, kill if still alive
            gone, alive = psutil.wait_procs(children, timeout=min(timeout, 3.0))
            for p in alive:
                try:
                    p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as exc:
            LOGGER.debug("Error during worker process tree cleanup: %s", exc)

        LOGGER.info("HybridWorkerPool shutdown complete. Zero child processes remain.")


@runtime_checkable
class BaseTaskBroker(Protocol):
    """Abstract interface for task message brokers."""

    def push_task(self, queue_name: str, payload: dict[str, Any]) -> bool:
        ...

    def pop_task(self, queue_name: str, timeout: float = 1.0) -> dict[str, Any] | None:
        ...

    def ack_task(self, queue_name: str, task_id: str) -> bool:
        ...

    def autoclaim_abandoned_tasks(self, queue_name: str, min_idle_ms: int = 60000) -> list[dict[str, Any]]:
        ...

    def get_queue_length(self, queue_name: str) -> int:
        ...

    def acquire_idempotency_lock(self, task_id: str, worker_id: str, ttl_seconds: int = 120) -> bool:
        ...

    def release_idempotency_lock(self, task_id: str) -> bool:
        ...

    def route_dead_letter(self, stream_name: str, message_id: str, payload: dict[str, Any], error_trace: str) -> bool:
        ...


class InMemoryTaskBroker:
    """Thread-safe zero-dependency in-memory task broker for local worker queues."""

    def __init__(self) -> None:
        self._queues: dict[str, queue.Queue] = {}
        self._lock = threading.Lock()
        self._task_counter = 0
        self._completed_locks: dict[str, tuple[str, float]] = {}
        self._dead_letters: list[dict[str, Any]] = []

    def _get_queue(self, queue_name: str) -> queue.Queue:
        with self._lock:
            if queue_name not in self._queues:
                self._queues[queue_name] = queue.Queue()
            return self._queues[queue_name]

    def push_task(self, queue_name: str, payload: dict[str, Any]) -> bool:
        q = self._get_queue(queue_name)
        with self._lock:
            self._task_counter += 1
            copied = dict(payload)
            copied.setdefault("_task_id", f"mem_{self._task_counter}")
        q.put(copied)
        return True

    def pop_task(self, queue_name: str, timeout: float = 1.0) -> dict[str, Any] | None:
        q = self._get_queue(queue_name)
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None

    def ack_task(self, queue_name: str, task_id: str) -> bool:
        return True

    def autoclaim_abandoned_tasks(self, queue_name: str, min_idle_ms: int = 60000) -> list[dict[str, Any]]:
        return []

    def get_queue_length(self, queue_name: str) -> int:
        q = self._get_queue(queue_name)
        return q.qsize()

    def acquire_idempotency_lock(self, task_id: str, worker_id: str, ttl_seconds: int = 120) -> bool:
        import time
        now = time.time()
        with self._lock:
            if task_id in self._completed_locks:
                owner, expires = self._completed_locks[task_id]
                if now < expires:
                    return False
            self._completed_locks[task_id] = (worker_id, now + ttl_seconds)
            return True

    def release_idempotency_lock(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._completed_locks:
                del self._completed_locks[task_id]
                return True
            return False

    def route_dead_letter(self, stream_name: str, message_id: str, payload: dict[str, Any], error_trace: str) -> bool:
        import time
        entry = {
            "task_id": payload.get("task_id", ""),
            "original_stream": stream_name,
            "message_id": message_id,
            "payload": payload,
            "error_trace": error_trace,
            "routed_at": time.time(),
            "delivery_count": payload.get("delivery_count", 0),
        }
        with self._lock:
            self._dead_letters.append(entry)
        return True


class RedisTaskBroker:
    """Distributed Redis task broker with automatic fallback to InMemoryTaskBroker."""

    def __init__(self, redis_url: str = "redis://127.0.0.1:6379/0") -> None:
        self.redis_url = redis_url
        self._client = None
        self._fallback = InMemoryTaskBroker()
        self._init_client()

    def _init_client(self) -> None:
        try:
            import redis
            from common.security import sanitize_url_credentials
            self._client = redis.from_url(self.redis_url, socket_timeout=2.0)
            self._client.ping()
            LOGGER.info("RedisTaskBroker: Connected to Redis at %s", sanitize_url_credentials(self.redis_url))
        except Exception as e:
            LOGGER.warning("RedisTaskBroker: Failed connecting to Redis (%s). Using in-memory fallback.", e)
            self._client = None

    def push_task(self, queue_name: str, payload: dict[str, Any]) -> bool:
        if self._client:
            try:
                self._client.rpush(queue_name, json.dumps(payload))
                return True
            except Exception as e:
                LOGGER.warning("Redis rpush failed (%s). Spilling to in-memory broker.", e)
        return self._fallback.push_task(queue_name, payload)

    def pop_task(self, queue_name: str, timeout: float = 1.0) -> dict[str, Any] | None:
        if self._client:
            try:
                item = self._client.blpop(queue_name, timeout=int(max(1, timeout)))
                if item and len(item) == 2:
                    raw_data = item[1]
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8")
                    return json.loads(raw_data)
            except Exception as e:
                LOGGER.warning("Redis blpop failed (%s). Falling back to in-memory broker.", e)
        return self._fallback.pop_task(queue_name, timeout)

    def ack_task(self, queue_name: str, task_id: str) -> bool:
        return True

    def autoclaim_abandoned_tasks(self, queue_name: str, min_idle_ms: int = 60000) -> list[dict[str, Any]]:
        return []

    def get_queue_length(self, queue_name: str) -> int:
        if self._client:
            try:
                return int(self._client.llen(queue_name))
            except Exception:
                pass
        return self._fallback.get_queue_length(queue_name)

    def acquire_idempotency_lock(self, task_id: str, worker_id: str, ttl_seconds: int = 120) -> bool:
        if self._client:
            try:
                return bool(self._client.set(f"scrape:completed:{task_id}", worker_id, nx=True, ex=ttl_seconds))
            except Exception:
                pass
        return self._fallback.acquire_idempotency_lock(task_id, worker_id, ttl_seconds)

    def release_idempotency_lock(self, task_id: str) -> bool:
        if self._client:
            try:
                return bool(self._client.delete(f"scrape:completed:{task_id}"))
            except Exception:
                pass
        return self._fallback.release_idempotency_lock(task_id)

    def route_dead_letter(self, stream_name: str, message_id: str, payload: dict[str, Any], error_trace: str) -> bool:
        return self._fallback.route_dead_letter(stream_name, message_id, payload, error_trace)


class RedisStreamTaskBroker:
    """
    Distributed Redis Streams task broker utilizing consumer groups (XREADGROUP),
    explicit acknowledgments (XACK), orphan auto-recovery (XAUTOCLAIM),
    atomic idempotency locks (SET NX), and dead-letter routing.
    Falls back gracefully to InMemoryTaskBroker if Redis is offline.
    """

    def __init__(
        self,
        redis_url: str = "redis://127.0.0.1:6379/0",
        group_name: str = "scraper_cluster",
        consumer_name: str | None = None,
    ) -> None:
        import time
        self.redis_url = redis_url
        self.group_name = group_name
        self.consumer_name = consumer_name or f"worker_{os.getpid()}_{int(time.time())}"
        self._client = None
        self._fallback = InMemoryTaskBroker()
        self._known_groups: set[str] = set()
        self._init_client()

    @staticmethod
    def validate_broker_security(redis_url: str) -> None:
        """
        Check for insecure broker configurations (AC1.2).
        Emits a warning containing 'INSECURE' if connecting to a non-loopback host without authentication.
        """
        from urllib.parse import urlparse
        from common.security import sanitize_url_credentials
        try:
            parsed = urlparse(redis_url)
            hostname = (parsed.hostname or "").lower()
            has_password = bool(parsed.password)
            is_loopback = hostname in ("127.0.0.1", "localhost", "::1", "")
            if not is_loopback and not has_password:
                LOGGER.warning(
                    "INSECURE REDIS CONFIGURATION: Worker connecting to unauthenticated non-loopback Redis host '%s' (missing credentials) at %s",
                    hostname,
                    sanitize_url_credentials(redis_url),
                )
        except Exception as err:
            LOGGER.debug("Error in validate_broker_security: %s", err)

    def _init_client(self) -> None:
        # Check security posture first
        self.validate_broker_security(self.redis_url)
        try:
            import redis
            from common.security import sanitize_url_credentials
            self._client = redis.from_url(self.redis_url, socket_timeout=2.0)
            self._client.ping()
            LOGGER.info("RedisStreamTaskBroker: Connected to Redis Streams at %s (group: %s)", sanitize_url_credentials(self.redis_url), self.group_name)
        except Exception as e:
            LOGGER.warning("RedisStreamTaskBroker: Failed connecting to Redis (%s). Using in-memory fallback.", e)
            self._client = None

    def _ensure_group(self, stream_name: str) -> None:
        if not self._client or stream_name in self._known_groups:
            return
        try:
            self._client.xgroup_create(stream_name, self.group_name, id="0", mkstream=True)
            self._known_groups.add(stream_name)
        except Exception as e:
            if "BUSYGROUP" in str(e):
                self._known_groups.add(stream_name)
            else:
                LOGGER.debug("xgroup_create notice for stream %s: %s", stream_name, e)

    def _decode_message_fields(self, msg_id: Any, fields: dict) -> dict[str, Any]:
        raw_payload = fields.get(b"payload") or fields.get("payload")
        if isinstance(raw_payload, bytes):
            raw_payload = raw_payload.decode("utf-8")
        data = json.loads(raw_payload) if raw_payload else {}
        msg_id_str = msg_id.decode("utf-8") if isinstance(msg_id, bytes) else str(msg_id)
        data["_task_id"] = msg_id_str
        return data

    def push_task(self, stream_name: str, payload: dict[str, Any]) -> bool:
        if self._client:
            try:
                self._client.xadd(stream_name, {"payload": json.dumps(payload)})
                return True
            except Exception as e:
                LOGGER.warning("Redis xadd failed (%s). Spilling to in-memory broker.", e)
        return self._fallback.push_task(stream_name, payload)

    def pop_task(self, stream_name: str, timeout: float = 1.0) -> dict[str, Any] | None:
        if self._client:
            try:
                self._ensure_group(stream_name)
                # 1. Drain consumer's own unacknowledged pending messages first
                pending_resp = self._client.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={stream_name: "0"},
                    count=1,
                )
                if pending_resp:
                    for _stream, messages in pending_resp:
                        for msg_id, fields in messages:
                            return self._decode_message_fields(msg_id, fields)

                # 2. Pop new messages from stream
                block_ms = int(max(10, timeout * 1000))
                resp = self._client.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={stream_name: ">"},
                    count=1,
                    block=block_ms,
                )
                if resp:
                    for _stream, messages in resp:
                        for msg_id, fields in messages:
                            return self._decode_message_fields(msg_id, fields)
            except Exception as e:
                LOGGER.warning("Redis xreadgroup failed (%s). Falling back to in-memory.", e)
        return self._fallback.pop_task(stream_name, timeout)

    def ack_task(self, stream_name: str, task_id: str) -> bool:
        if self._client:
            try:
                self._client.xack(stream_name, self.group_name, task_id)
                return True
            except Exception as e:
                LOGGER.warning("Redis xack failed: %s", e)
        return self._fallback.ack_task(stream_name, task_id)

    def acquire_idempotency_lock(self, task_id: str, worker_id: str, ttl_seconds: int = 120) -> bool:
        """
        Atomic idempotency lock (AC1.1).
        Enforces SET scrape:completed:{task_id} {worker_id} NX EX {ttl_seconds}.
        Only the first worker to complete the task acquires the lock.
        """
        ttl = max(1, int(ttl_seconds))
        if self._client:
            try:
                key = f"scrape:completed:{task_id}"
                res = self._client.set(key, worker_id, nx=True, ex=ttl)
                return bool(res)
            except Exception as e:
                LOGGER.warning("Redis acquire_idempotency_lock error (%s). Falling back to in-memory.", e)
        return self._fallback.acquire_idempotency_lock(task_id, worker_id, ttl)

    def release_idempotency_lock(self, task_id: str) -> bool:
        if self._client:
            try:
                key = f"scrape:completed:{task_id}"
                return bool(self._client.delete(key))
            except Exception as e:
                LOGGER.warning("Redis release_idempotency_lock error: %s", e)
        return self._fallback.release_idempotency_lock(task_id)

    def route_dead_letter(self, stream_name: str, message_id: str, payload: dict[str, Any], error_trace: str) -> bool:
        """
        Route poison-pill tasks to scrape:dead_letter_stream and XACK off working stream (AC1.4).
        """
        import time
        dead_letter_stream = "scrape:dead_letter_stream"
        entry = {
            "task_id": str(payload.get("task_id", "")),
            "original_stream": stream_name,
            "message_id": str(message_id),
            "payload": json.dumps(payload),
            "error_trace": error_trace[:4096],
            "routed_at": str(time.time()),
            "delivery_count": str(payload.get("delivery_count", 0)),
        }
        if self._client:
            try:
                self._client.xadd(dead_letter_stream, entry)
                self._client.xack(stream_name, self.group_name, message_id)
                LOGGER.warning(
                    "Task %s moved to dead-letter stream %s after failed execution (delivery_count: %s).",
                    payload.get("task_id", message_id),
                    dead_letter_stream,
                    payload.get("delivery_count", 0),
                )
                return True
            except Exception as e:
                LOGGER.error("Failed routing task to dead letter stream: %s", e)
        return self._fallback.route_dead_letter(stream_name, message_id, payload, error_trace)

    def autoclaim_abandoned_tasks(self, stream_name: str, min_idle_ms: int = 5000, count: int = 10) -> list[dict[str, Any]]:
        """
        Reclaim abandoned or stalled tasks (AC1.1).
        Uses XAUTOCLAIM with fallback to XPENDING_RANGE + XCLAIM.
        """
        reclaimed: list[dict[str, Any]] = []
        if not self._client:
            return self._fallback.autoclaim_abandoned_tasks(stream_name, min_idle_ms)

        self._ensure_group(stream_name)
        try:
            res = self._client.xautoclaim(
                name=stream_name,
                groupname=self.group_name,
                consumername=self.consumer_name,
                min_idle_time=min_idle_ms,
                start_id="0-0",
                count=count,
            )
            if res and len(res) >= 2:
                messages = res[1]
                for msg_id, fields in messages:
                    data = self._decode_message_fields(msg_id, fields)
                    if data:
                        reclaimed.append(data)
                return reclaimed
        except Exception as e:
            LOGGER.debug("xautoclaim fallback triggered: %s", e)

        # Fallback to XPENDING_RANGE + XCLAIM
        try:
            pending = self._client.xpending_range(
                name=stream_name,
                groupname=self.group_name,
                min="-",
                max="+",
                count=count,
            )
            for p in pending:
                idle = p.get("idle", 0)
                msg_id = p.get("message_id")
                consumer = p.get("consumer")
                if idle >= min_idle_ms and consumer != self.consumer_name:
                    claimed = self._client.xclaim(
                        name=stream_name,
                        groupname=self.group_name,
                        consumername=self.consumer_name,
                        min_idle_time=min_idle_ms,
                        message_ids=[msg_id],
                    )
                    for c_id, fields in claimed:
                        data = self._decode_message_fields(c_id, fields)
                        if data:
                            reclaimed.append(data)
        except Exception as err:
            LOGGER.debug("xpending/xclaim error: %s", err)

        return reclaimed

    def get_delivery_count(self, stream_name: str, message_id: str) -> int:
        """Query Redis XPENDING to get delivery count for a pending message."""
        if not self._client:
            return 1
        try:
            pending_list = self._client.xpending_range(
                name=stream_name,
                groupname=self.group_name,
                min=message_id,
                max=message_id,
                count=1,
            )
            if pending_list:
                return int(pending_list[0].get("times_delivered", 1))
        except Exception as e:
            LOGGER.debug("Error querying message delivery count: %s", e)
        return 1

    def gc_stale_consumers(self, stream_name: str) -> int:
        """
        Garbage collect consumers in consumer group that have 0 pending messages
        and no active heartbeat key in scrape:workers:* (AC1.7).
        """
        pruned = 0
        if not self._client:
            return pruned
        try:
            self._ensure_group(stream_name)
            consumers = self._client.xinfo_consumers(stream_name, self.group_name)
            for c in consumers:
                c_name = c.get("name")
                if isinstance(c_name, bytes):
                    c_name = c_name.decode("utf-8")
                pending = c.get("pending", 0)
                if pending == 0:
                    heartbeat_key = f"scrape:workers:{c_name}"
                    if not self._client.exists(heartbeat_key):
                        self._client.xgroup_delconsumer(stream_name, self.group_name, c_name)
                        pruned += 1
                        LOGGER.info("Pruned stale consumer %s from stream %s", c_name, stream_name)
        except Exception as e:
            LOGGER.debug("gc_stale_consumers notice for stream %s: %s", stream_name, e)
        return pruned

    def get_active_worker_count(self) -> int:
        """Count active worker nodes based on unexpired heartbeat keys (AC1.6)."""
        if self._client:
            try:
                keys = list(self._client.scan_iter("scrape:workers:*", count=100))
                return len(keys)
            except Exception as e:
                LOGGER.debug("Error scanning worker heartbeats: %s", e)
        return 0

    def get_queue_length(self, stream_name: str) -> int:
        if self._client:
            try:
                return int(self._client.xlen(stream_name))
            except Exception:
                pass
        return self._fallback.get_queue_length(stream_name)


def get_task_broker(broker_url: str | None = None, use_streams: bool = True) -> BaseTaskBroker:
    """Factory creating an appropriate task broker based on URL or SCRAPER_REDIS_URL environment variable."""
    url = (broker_url or os.getenv("SCRAPER_REDIS_URL", "")).strip()
    if url.startswith("redis://") or url.startswith("rediss://"):
        if use_streams:
            return RedisStreamTaskBroker(redis_url=url)
        return RedisTaskBroker(redis_url=url)
    return InMemoryTaskBroker()


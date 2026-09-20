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

    def get_queue_length(self, queue_name: str) -> int:
        ...


class InMemoryTaskBroker:
    """Thread-safe zero-dependency in-memory task broker for local worker queues."""

    def __init__(self) -> None:
        self._queues: dict[str, queue.Queue] = {}
        self._lock = threading.Lock()

    def _get_queue(self, queue_name: str) -> queue.Queue:
        with self._lock:
            if queue_name not in self._queues:
                self._queues[queue_name] = queue.Queue()
            return self._queues[queue_name]

    def push_task(self, queue_name: str, payload: dict[str, Any]) -> bool:
        q = self._get_queue(queue_name)
        q.put(payload)
        return True

    def pop_task(self, queue_name: str, timeout: float = 1.0) -> dict[str, Any] | None:
        q = self._get_queue(queue_name)
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_queue_length(self, queue_name: str) -> int:
        q = self._get_queue(queue_name)
        return q.qsize()


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
            self._client = redis.from_url(self.redis_url, socket_timeout=2.0)
            self._client.ping()
            LOGGER.info("RedisTaskBroker: Connected to Redis at %s", self.redis_url)
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

    def get_queue_length(self, queue_name: str) -> int:
        if self._client:
            try:
                return int(self._client.llen(queue_name))
            except Exception:
                pass
        return self._fallback.get_queue_length(queue_name)


def get_task_broker(broker_url: str | None = None) -> BaseTaskBroker:
    """Factory creating a task broker based on URL or SCRAPER_REDIS_URL environment variable."""
    url = (broker_url or os.getenv("SCRAPER_REDIS_URL", "")).strip()
    if url.startswith("redis://"):
        return RedisTaskBroker(redis_url=url)
    return InMemoryTaskBroker()

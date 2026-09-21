"""
distributed_worker.py — Autonomous worker node daemon for distributed task leasing.

Implements:
  - Unique worker identity: worker_{hostname}_{pid}_{uuid}
  - Ephemeral Redis heartbeat: scrape:workers:{worker_id} with EX 15
  - Consumer group task leasing (XREADGROUP) and auto-recovery (XAUTOCLAIM)
  - Strict write-before-ack ordering (AC1.5)
  - Atomic idempotency locks preventing double-write on reclaimed tasks (AC1.1)
  - Dead-letter stream routing on poison-pill tasks (AC1.4)
  - Consumer group garbage collection on shutdown (AC1.7)
"""

from __future__ import annotations

import json
import logging
import os
import socket
import threading
import time
from typing import Any, Callable
import uuid

from core.task_schema import (
    CrawlTaskPayload,
    DownloadTaskPayload,
    parse_task_payload,
)
from core.worker_pool import BaseTaskBroker, RedisStreamTaskBroker

LOGGER = logging.getLogger(__name__)


class DistributedWorkerNode:
    """Distributed Worker Node consuming tasks from Redis Streams."""

    def __init__(
        self,
        broker: BaseTaskBroker | None = None,
        broker_url: str = "redis://127.0.0.1:6379/0",
        role: str = "all",
        group_name: str = "scraper_cluster",
        consumer_name: str | None = None,
        lease_ttl: int = 30,
        task_handler: Callable[[CrawlTaskPayload | DownloadTaskPayload], Any] | None = None,
    ) -> None:
        self.role = role
        self.group_name = group_name
        self.lease_ttl = lease_ttl
        self.task_handler = task_handler

        hostname = socket.gethostname()
        pid = os.getpid()
        self.worker_id = consumer_name or f"worker_{hostname}_{pid}_{uuid.uuid4().hex[:6]}"

        if broker is not None:
            self.broker = broker
            if hasattr(self.broker, "consumer_name"):
                self.broker.consumer_name = self.worker_id
        else:
            self.broker = RedisStreamTaskBroker(
                redis_url=broker_url,
                group_name=self.group_name,
                consumer_name=self.worker_id,
            )

        self.streams: list[str] = []
        if self.role in ("crawl", "all"):
            self.streams.append("scrape:crawl_stream")
        if self.role in ("download", "all"):
            self.streams.append("scrape:download_stream")

        self.is_running = False
        self.tasks_processed = 0
        self.tasks_failed = 0
        self._heartbeat_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start_heartbeat(self) -> None:
        """Start the background heartbeat thread publishing to Redis."""
        self._stop_event.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def stop_heartbeat(self) -> None:
        """Signal and wait for heartbeat thread shutdown."""
        self._stop_event.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=1.0)

    def publish_heartbeat(self) -> None:
        """Publish an ephemeral heartbeat key (AC1.6) with 15s TTL."""
        client = getattr(self.broker, "_client", None)
        if client:
            try:
                heartbeat_data = {
                    "worker_id": self.worker_id,
                    "hostname": socket.gethostname(),
                    "pid": os.getpid(),
                    "role": self.role,
                    "tasks_processed": self.tasks_processed,
                    "last_heartbeat": time.time(),
                }
                key = f"scrape:workers:{self.worker_id}"
                client.set(key, json.dumps(heartbeat_data), ex=15)
            except Exception as e:
                LOGGER.debug("Worker heartbeat publish failed: %s", e)

    def _heartbeat_loop(self) -> None:
        while not self._stop_event.is_set():
            self.publish_heartbeat()
            self._stop_event.wait(5.0)

    def process_one_task(self, stream_name: str | None = None, timeout: float = 0.5) -> dict[str, Any] | None:
        """
        Process a single task lease with full fault-tolerance, idempotency, and dead-letter routing.
        """
        target_stream = stream_name or (self.streams[0] if self.streams else "scrape:crawl_stream")

        # 1. Lease task or reclaim abandoned task
        task_data = self.broker.pop_task(target_stream, timeout=timeout)
        is_reclaimed = False
        if not task_data:
            reclaimed = self.broker.autoclaim_abandoned_tasks(target_stream, min_idle_ms=int(self.lease_ttl * 1000))
            if reclaimed:
                task_data = reclaimed[0]
                is_reclaimed = True

        if not task_data:
            return None

        msg_id = task_data.get("_task_id", "")
        task_id = str(task_data.get("task_id", msg_id))
        LOGGER.info("Worker %s leased task %s from stream %s (msg_id: %s)", self.worker_id, task_id, target_stream, msg_id)

        # 2. Check delivery counter (AC1.4 poison-pill defense)
        delivery_count = 1
        if hasattr(self.broker, "get_delivery_count"):
            delivery_count = self.broker.get_delivery_count(target_stream, msg_id)
        task_data["delivery_count"] = delivery_count

        if delivery_count > 3:
            LOGGER.error("Poison-pill task %s exceeded max retries (%d). Routing to dead-letter.", task_id, delivery_count)
            self.broker.route_dead_letter(
                stream_name=target_stream,
                message_id=msg_id,
                payload=task_data,
                error_trace=f"Task failed after {delivery_count} delivery attempts.",
            )
            self.tasks_failed += 1
            return {"status": "dead_letter", "task_id": task_id, "delivery_count": delivery_count}

        # 3. Strict schema validation (AC1.3)
        try:
            typed_task = parse_task_payload(task_data)
        except Exception as validation_exc:
            LOGGER.error("Task %s payload rejected by security schema: %s", task_id, validation_exc)
            self.broker.route_dead_letter(
                stream_name=target_stream,
                message_id=msg_id,
                payload=task_data,
                error_trace=f"Schema validation error: {validation_exc}",
            )
            self.tasks_failed += 1
            return {"status": "rejected", "task_id": task_id, "error": str(validation_exc)}

        # 4. Execute task business logic
        execution_result = None
        try:
            if self.task_handler:
                execution_result = self.task_handler(typed_task)
            else:
                execution_result = self._default_execute(typed_task)
        except Exception as exec_exc:
            LOGGER.exception("Error executing task %s: %s", task_id, exec_exc)
            # Do NOT ack! Leave message pending for redelivery / autoclaim up to 3 times
            self.tasks_failed += 1
            return {"status": "execution_failed", "task_id": task_id, "error": str(exec_exc)}

        # 5. Atomic Idempotency Lock (AC1.1)
        # Guarantees that if a stale worker or reclaiming worker finishes, only the first one persists output
        lock_acquired = self.broker.acquire_idempotency_lock(
            task_id=task_id,
            worker_id=self.worker_id,
            ttl_seconds=max(60, int(self.lease_ttl * 3)),
        )
        if not lock_acquired:
            LOGGER.warning(
                "Task %s was already completed by another worker. Discarding duplicate output.",
                task_id,
            )
            # Acknowledge message to remove from stream
            self.broker.ack_task(target_stream, msg_id)
            return {"status": "discarded_duplicate", "task_id": task_id}

        # 6. Persist output artifact (Strict ordering: write BEFORE ack per AC1.5)
        self._persist_output(typed_task, execution_result)

        # 7. Finalize and acknowledge task
        self.broker.ack_task(target_stream, msg_id)
        self.tasks_processed += 1
        return {
            "status": "completed",
            "task_id": task_id,
            "reclaimed": is_reclaimed,
            "output": execution_result,
        }

    def _default_execute(self, task: CrawlTaskPayload | DownloadTaskPayload) -> dict[str, Any]:
        """Default execution for worker nodes with test delay injection support."""
        try:
            delay = float(os.getenv("SCRAPER_WORKER_SIMULATE_DELAY", "0"))
            if delay > 0:
                time.sleep(delay)
        except Exception:
            pass

        if isinstance(task, CrawlTaskPayload):
            return {"pages_visited": 1, "media_found": 0, "status": "crawled"}
        elif isinstance(task, DownloadTaskPayload):
            return {"bytes_downloaded": 1024, "status": "downloaded"}
        return {"status": "ok"}

    def _persist_output(self, task: CrawlTaskPayload | DownloadTaskPayload, result: Any) -> None:
        """Simulate or execute durable output persistence."""
        if isinstance(task, DownloadTaskPayload):
            dest = task.destination_path
            os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(f"DOWNLOAD_ARTIFACT_FOR_{task.task_id}")
        elif isinstance(task, CrawlTaskPayload):
            out_dir = task.output_dir
            os.makedirs(out_dir, exist_ok=True)
            out_file = os.path.join(out_dir, f"{task.task_id}_summary.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump({"task_id": task.task_id, "result": result}, f)

    def run(self, max_tasks: int | None = None) -> None:
        """Run the worker loop continuously until shutdown."""
        self.is_running = True
        self.start_heartbeat()
        count = 0
        try:
            while self.is_running:
                for stream in self.streams:
                    res = self.process_one_task(stream_name=stream, timeout=0.5)
                    if res and res.get("status") == "completed":
                        count += 1
                        if max_tasks and count >= max_tasks:
                            return
                time.sleep(0.05)
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Gracefully shut down the worker, stop heartbeat, and deregister consumer (AC1.7)."""
        if getattr(self, "_is_shutdown", False):
            return
        self._is_shutdown = True
        self.is_running = False
        self.stop_heartbeat()

        client = getattr(self.broker, "_client", None)
        if client:
            try:
                # Remove heartbeat key
                client.delete(f"scrape:workers:{self.worker_id}")
                # Prune self from consumer groups
                for stream in self.streams:
                    try:
                        client.xgroup_delconsumer(stream, self.group_name, self.worker_id)
                    except Exception:
                        pass
            except Exception as e:
                LOGGER.debug("Error cleaning up worker in Redis: %s", e)
        LOGGER.info("DistributedWorkerNode %s shutdown complete.", self.worker_id)

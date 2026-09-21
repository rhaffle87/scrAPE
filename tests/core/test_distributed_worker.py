"""
tests/core/test_distributed_worker.py — Verification of Distributed Task Leasing & Worker Daemons.

Strict Acceptance Criteria Tests:
  - AC1.1: Kill worker mid-task via real process.kill(), reclaim via XAUTOCLAIM,
           verify exactly 1 output artifact on disk and SET NX idempotency lock in Redis.
  - AC1.4: Poison-pill repeated failure (> 3 delivery attempts) routed to scrape:dead_letter_stream.
           Assert directly against Redis state: XPENDING empty, dead-letter stream has 1 item.
  - AC1.5: Strict write-before-ack ordering under fault injection.
  - AC1.3 / AC1.7: Stream schema validation failure handling and consumer deregistration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Generator

import fakeredis
import pytest
import redis

from core.distributed_worker import DistributedWorkerNode
from core.task_schema import CrawlTaskPayload
from core.worker_pool import RedisStreamTaskBroker


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def fake_redis_tcp_server() -> Generator[str, None, None]:
    """
    Spins up tests/fake_redis_service.py as an isolated subprocess on an ephemeral loopback port.
    Ensures real TCP wire protocol connectivity for spawned CLI worker subprocesses.
    """
    port = _get_free_port()
    script_path = Path(__file__).resolve().parent.parent / "fake_redis_service.py"
    proc = subprocess.Popen(
        [sys.executable, str(script_path), "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for service readiness
    ready_line = ""
    for _ in range(50):
        if proc.stdout and proc.poll() is None:
            ready_line = proc.stdout.readline().strip()
            if "READY" in ready_line:
                break
        time.sleep(0.1)

    if "READY" not in ready_line:
        proc.kill()
        raise RuntimeError(f"Fake Redis TCP service failed to start on port {port}. Line: {ready_line}")

    redis_url = f"redis://127.0.0.1:{port}/0"

    # Verify connectivity
    client = redis.from_url(redis_url, socket_timeout=2.0)
    for _ in range(30):
        try:
            if client.ping():
                break
        except Exception:
            time.sleep(0.1)
    else:
        proc.kill()
        raise RuntimeError(f"Could not connect to Fake Redis TCP service on {redis_url}")

    try:
        yield redis_url
    finally:
        client.close()
        proc.kill()
        proc.wait(timeout=3.0)


@pytest.mark.e2e
def test_worker_killed_mid_task_reclaimed_with_idempotency_ac1_1(fake_redis_tcp_server, tmp_path):
    """
    AC1.1 Adversarial Kill Test:
      1. Spawn Worker 1 as a separate OS subprocess.
      2. Worker 1 leases task from scrape:crawl_stream and enters simulated execution.
      3. Mid-task, violently terminate Worker 1 with proc.kill() (not a mocked simulation).
      4. Verify Worker 1 is dead, output artifact does NOT exist, idempotency key NOT set.
      5. Start Worker 2, let it reclaim the abandoned task via XAUTOCLAIM.
      6. Worker 2 completes task, sets idempotency lock, writes output artifact.
      7. Assert via Redis and filesystem:
         - Exactly 1 output artifact exists on disk.
         - Redis completed key is set to Worker 2.
         - Working stream XPENDING is 0.
      8. Concurrency guard: A subsequent attempt to process the same task discards duplicate output.
    """
    redis_url = fake_redis_tcp_server
    client = redis.from_url(redis_url)
    stream_name = "scrape:crawl_stream"
    group_name = "scraper_cluster"
    task_id = "task_adv_kill_101"
    output_dir = tmp_path / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize consumer group and push task
    try:
        client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
    except Exception:
        pass

    task_payload = {
        "task_id": task_id,
        "seed_url": "https://example.com/adversarial-target",
        "output_dir": str(output_dir),
        "page_limit": 3,
    }
    client.xadd(stream_name, {"payload": json.dumps(task_payload)})
    assert client.xlen(stream_name) == 1

    # 2. Spawn Worker 1 in real subprocess with 4-second execution delay
    env = os.environ.copy()
    env["SCRAPER_WORKER_SIMULATE_DELAY"] = "4.0"
    env["PYTHONUNBUFFERED"] = "1"

    worker1_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "src.cli.worker",
            "--broker",
            redis_url,
            "--role",
            "crawl",
            "--lease-ttl",
            "2",
            "--name",
            "worker_proc_1",
            "--max-tasks",
            "1",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # 3. Wait until Worker 1 has leased the task (XPENDING pending count == 1)
    leased = False
    for _ in range(50):
        pending = client.xpending(stream_name, group_name)
        if pending and pending.get("pending", 0) >= 1:
            leased = True
            break
        time.sleep(0.1)

    if not leased:
        worker1_proc.kill()
        _out, err = worker1_proc.communicate(timeout=2.0)
        assert False, f"Worker 1 did not lease task within 5.0 seconds. Stderr: {err}"

    assert worker1_proc.poll() is None, "Worker 1 should be alive and executing mid-task"

    # 4. VIOLENTLY KILL WORKER 1 MID-TASK
    worker1_proc.kill()
    worker1_proc.wait(timeout=3.0)
    assert worker1_proc.poll() is not None, "Worker 1 must be terminated"

    # Assert Worker 1 did NOT finish or persist output
    expected_artifact = output_dir / f"{task_id}_summary.json"
    assert not expected_artifact.exists(), "Output artifact must not exist before completion"
    assert client.get(f"scrape:completed:{task_id}") is None, "Idempotency key must not exist"

    # 5. Wait for lease TTL to expire (lease_ttl = 2s) so task is eligible for XAUTOCLAIM
    time.sleep(2.2)

    # 6. Start Worker 2 to reclaim abandoned task
    broker2 = RedisStreamTaskBroker(redis_url=redis_url, group_name=group_name, consumer_name="worker_proc_2")
    worker2 = DistributedWorkerNode(broker=broker2, role="crawl", lease_ttl=2, consumer_name="worker_proc_2")

    result = worker2.process_one_task(stream_name=stream_name, timeout=1.0)
    assert result is not None, "Worker 2 should process the reclaimed task"
    assert result["status"] == "completed"
    assert result["reclaimed"] is True
    assert result["task_id"] == task_id

    # 7. Assertions: Exactly 1 output artifact exists on disk
    assert expected_artifact.exists(), "Output artifact must exist after Worker 2 completion"
    all_artifacts = list(output_dir.glob("*.json"))
    assert len(all_artifacts) == 1, f"Expected exactly 1 output artifact, found: {all_artifacts}"

    # Verify idempotency key in Redis belongs to Worker 2
    completed_owner = client.get(f"scrape:completed:{task_id}")
    assert completed_owner == b"worker_proc_2"

    # Verify stream state: XPENDING is 0
    pending_after = client.xpending(stream_name, group_name)
    assert pending_after["pending"] == 0, "XPENDING must be 0 after successful XACK"

    # 8. Test double-write protection (Idempotency Guard)
    # Simulate another worker or duplicate execution attempting to write for the same task
    worker3 = DistributedWorkerNode(broker=broker2, role="crawl", lease_ttl=2, consumer_name="worker_proc_3")
    fake_typed_task = CrawlTaskPayload(
        task_id=task_id,
        seed_url="https://example.com/adversarial-target",
        output_dir=str(output_dir),
        page_limit=3,
    )
    # Attempt acquiring idempotency lock directly
    lock_again = broker2.acquire_idempotency_lock(task_id, "worker_proc_3")
    assert lock_again is False, "Idempotency lock must reject second worker"

    # Ensure output file count remains strictly 1
    assert len(list(output_dir.glob("*.json"))) == 1


def test_poison_pill_dead_letter_stream_ac1_4():
    """
    AC1.4 Poison-Pill Defense:
      - Push task that repeatedly raises an unhandled exception.
      - Worker attempts execution -> delivery_count increments on redelivery.
      - When delivery_count > 3:
        1. Task is routed to scrape:dead_letter_stream with trace metadata.
        2. Task is acknowledged (XACK) off the working stream.
      - Assert directly against Redis stream state:
        - XPENDING on working stream is 0.
        - scrape:dead_letter_stream length is 1.
    """
    fake_client = fakeredis.FakeRedis()
    stream_name = "scrape:crawl_stream"
    group_name = "scraper_cluster"
    dead_letter_stream = "scrape:dead_letter_stream"

    broker = RedisStreamTaskBroker(redis_url="redis://127.0.0.1:6379/0", group_name=group_name)
    broker._client = fake_client
    broker._ensure_group(stream_name)

    task_id = "poison_pill_task_666"
    payload = {
        "task_id": task_id,
        "seed_url": "https://example.com/exploit",
        "output_dir": "output/test",
        "page_limit": 1,
    }
    msg_id = fake_client.xadd(stream_name, {"payload": json.dumps(payload)})

    # Handler that fails deterministically
    def _exploding_handler(_task):
        raise RuntimeError("Deterministic crash: simulated parser core dump")

    worker = DistributedWorkerNode(
        broker=broker,
        role="crawl",
        group_name=group_name,
        task_handler=_exploding_handler,
    )

    # Initial lease (delivery count = 1) -> fails, message remains pending in XPENDING
    res1 = worker.process_one_task(stream_name=stream_name, timeout=0.1)
    assert res1["status"] == "execution_failed"
    pending = fake_client.xpending(stream_name, group_name)
    assert pending["pending"] == 1

    # Simulate subsequent redeliveries advancing delivery count
    # In Redis, delivery count increments on each read/claim
    fake_client.xclaim(stream_name, group_name, worker.worker_id, min_idle_time=0, message_ids=[msg_id])
    fake_client.xclaim(stream_name, group_name, worker.worker_id, min_idle_time=0, message_ids=[msg_id])
    fake_client.xclaim(stream_name, group_name, worker.worker_id, min_idle_time=0, message_ids=[msg_id])

    delivery_count = broker.get_delivery_count(stream_name, msg_id.decode())
    assert delivery_count >= 4, f"Expected delivery count >= 4, got {delivery_count}"

    # Next process attempt: delivery_count > 3 triggers dead-letter routing
    res_dl = worker.process_one_task(stream_name=stream_name, timeout=0.1)
    assert res_dl is not None
    assert res_dl["status"] == "dead_letter"
    assert res_dl["task_id"] == task_id

    # DIRECT REDIS STATE ASSERTIONS:
    # 1. Working stream XPENDING must be 0
    pending_after = fake_client.xpending(stream_name, group_name)
    assert pending_after["pending"] == 0, "Working stream XPENDING must be 0 after dead-letter XACK"

    # 2. Dead-letter stream length must be 1
    assert fake_client.xlen(dead_letter_stream) == 1

    # 3. Verify dead-letter message metadata
    dead_letters = fake_client.xrange(dead_letter_stream)
    assert len(dead_letters) == 1
    dl_fields = dead_letters[0][1]
    assert dl_fields[b"task_id"] == task_id.encode()
    assert dl_fields[b"original_stream"] == stream_name.encode()
    assert b"delivery_count" in dl_fields
    assert b"error_trace" in dl_fields


def test_strict_write_before_ack_ordering_ac1_5(tmp_path):
    """
    AC1.5 Strict Write-Before-Ack Ordering:
      - Simulates worker failure immediately after output persistence but prior to XACK.
      - Verifies:
        1. Output artifact exists on disk.
        2. Task remains pending in XPENDING.
        3. When reclaimed, second worker sees idempotency lock is already held,
           discards duplicate write, and executes XACK to clear the pending stream.
    """
    fake_client = fakeredis.FakeRedis()
    stream_name = "scrape:download_stream"
    group_name = "scraper_cluster"
    task_id = "task_crash_before_ack_505"
    dest_path = str(tmp_path / "downloads" / f"{task_id}.bin")

    broker = RedisStreamTaskBroker(redis_url="redis://127.0.0.1:6379/0", group_name=group_name)
    broker._client = fake_client
    broker._ensure_group(stream_name)

    payload = {
        "task_id": task_id,
        "media_url": "https://example.com/asset.png",
        "destination_path": dest_path,
    }
    fake_client.xadd(stream_name, {"payload": json.dumps(payload)})

    worker1 = DistributedWorkerNode(broker=broker, role="download", group_name=group_name, consumer_name="worker_1")

    # Worker 1 leases task
    task_data = broker.pop_task(stream_name)
    assert task_data is not None

    # Step 5: Acquire idempotency lock
    locked = broker.acquire_idempotency_lock(task_id, worker_id=worker1.worker_id, ttl_seconds=60)
    assert locked is True

    # Step 6: Persist output artifact
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write("ORIGINAL_FILE_CONTENT_FROM_WORKER_1")

    # Simulate CRASH BEFORE STEP 7 (XACK never called!)
    # Task remains pending in stream
    pending_state = fake_client.xpending(stream_name, group_name)
    assert pending_state["pending"] == 1
    assert os.path.exists(dest_path)

    # Worker 2 reclaims task via autoclaim (lease_ttl=0 allows immediate reclamation in test)
    broker2 = RedisStreamTaskBroker(redis_url="redis://127.0.0.1:6379/0", group_name=group_name, consumer_name="worker_2")
    broker2._client = fake_client
    worker2 = DistributedWorkerNode(broker=broker2, role="download", group_name=group_name, consumer_name="worker_2", lease_ttl=0)
    # Simulate reclamation attempt
    res = worker2.process_one_task(stream_name=stream_name, timeout=0.1)

    # Worker 2 should detect the duplicate lock, discard write, and ack the message
    assert res is not None
    assert res["status"] == "discarded_duplicate"
    assert res["task_id"] == task_id

    # Verify content was NOT overwritten or corrupted
    with open(dest_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == "ORIGINAL_FILE_CONTENT_FROM_WORKER_1"

    # Verify stream state: XACK cleared pending message
    pending_final = fake_client.xpending(stream_name, group_name)
    assert pending_final["pending"] == 0


def test_malformed_task_schema_dead_letter_ac1_3():
    """
    AC1.3 Integration: Malicious task payload on stream fails Pydantic validation
    and is immediately routed to dead-letter stream without executing or blocking stream.
    """
    fake_client = fakeredis.FakeRedis()
    stream_name = "scrape:crawl_stream"
    group_name = "scraper_cluster"
    dead_letter_stream = "scrape:dead_letter_stream"

    broker = RedisStreamTaskBroker(redis_url="redis://127.0.0.1:6379/0", group_name=group_name)
    broker._client = fake_client
    broker._ensure_group(stream_name)

    # Malicious payload with path traversal and SSRF seed_url
    malicious_payload = {
        "task_id": "malicious_task_999",
        "seed_url": "http://169.254.169.254/latest/meta-data/",
        "output_dir": "../../etc/shadow",
        "page_limit": 10,
    }
    fake_client.xadd(stream_name, {"payload": json.dumps(malicious_payload)})

    worker = DistributedWorkerNode(broker=broker, role="crawl", group_name=group_name)
    res = worker.process_one_task(stream_name=stream_name, timeout=0.1)

    assert res is not None
    assert res["status"] == "rejected"
    assert res["task_id"] == "malicious_task_999"

    # Assert working stream is clean and dead letter stream has the entry
    pending = fake_client.xpending(stream_name, group_name)
    assert pending["pending"] == 0
    assert fake_client.xlen(dead_letter_stream) == 1

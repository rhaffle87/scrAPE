"""
tests/core/test_advanced_core_systems.py — Validates Phase 4 Advanced Core Systems Modernization.

Covers:
1. ContentAddressableStore: Zero-RAM chunked streaming ingestion (store_stream) and deduplication.
2. CrawlGovernor: TCP & socket exhaustion backpressure detection, concurrency throttling, and emergency brake.
3. SqliteTaskBroker: Zero-dependency multi-process persistent task queue, atomic leasing, auto-recovery, and idempotency locks.
4. DistributedWorkerNode: Initialization with sqlite:// URL protocol and resilient local execution.
5. SelfHealingDOMParser: Tier 4 VLM visual synthesis integration and selector cache promotion.
"""

from __future__ import annotations

import io
from pathlib import Path
import time
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup
import pytest

from core.governor import CrawlGovernor
from core.self_healing_parser import SelfHealingDOMParser
from core.worker_pool import SqliteTaskBroker
from storage.cas_store import ContentAddressableStore


# =========================================================================
# 1. Zero-RAM Streaming Storage (store_stream)
# =========================================================================

class TestZeroRAMStreamingCAS:
    def test_store_stream_creates_valid_cas_asset(self, tmp_path):
        cas = ContentAddressableStore(root_dir=tmp_path / "cas")
        payload_chunks = [b"chunk_1_", b"chunk_2_", b"final_chunk"]
        expected_bytes = b"".join(payload_chunks)

        import hashlib
        expected_hash = hashlib.sha256(expected_bytes).hexdigest()

        sha, cas_path, total_bytes = cas.store_stream(iter(payload_chunks), extension="mp4")

        assert sha == expected_hash
        assert total_bytes == len(expected_bytes)
        assert cas_path.exists()
        assert cas_path.read_bytes() == expected_bytes
        assert cas.exists(sha, extension="mp4")

    def test_store_stream_deduplicates_existing_asset(self, tmp_path):
        cas = ContentAddressableStore(root_dir=tmp_path / "cas")
        payload = b"duplicate_stream_payload"

        sha1, path1, bytes1 = cas.store_stream(iter([payload]), extension="jpg")
        sha2, path2, bytes2 = cas.store_stream(iter([payload]), extension="jpg")

        assert sha1 == sha2
        assert path1 == path2
        assert bytes1 == bytes2
        # Temporary directory should be cleaned up
        tmp_files = list((tmp_path / "cas" / "tmp").glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_store_stream_cleans_up_tmp_on_failure(self, tmp_path):
        cas = ContentAddressableStore(root_dir=tmp_path / "cas")

        def failing_generator():
            yield b"good_chunk"
            raise IOError("Simulated network stream disconnect")

        with pytest.raises(IOError, match="Simulated network stream disconnect"):
            cas.store_stream(failing_generator(), extension="bin")

        tmp_files = list((tmp_path / "cas" / "tmp").glob("*.tmp"))
        assert len(tmp_files) == 0


# =========================================================================
# 2. Adaptive TCP / Socket Exhaustion Backpressure
# =========================================================================

class TestGovernorSocketBackpressure:
    def test_socket_pressure_throttles_concurrency_and_acquisition(self):
        governor = CrawlGovernor(initial_concurrency=10, min_concurrency=1)
        governor.report_yield("example.com", 10)  # Enter deep scrape mode

        # Normal condition: allowed concurrency is at max
        assert governor.get_allowed_concurrency("example.com") == 10
        assert governor.get_global_concurrency_limit() == 10
        assert governor.can_acquire_worker("example.com") is True

        # Simulate high socket count exceeding safe limit
        with patch("psutil.net_connections") as mock_conns:
            mock_conns.return_value = [MagicMock()] * 1500  # Exceeds 1200 threshold
            # Force refresh
            governor._last_socket_check = 0.0

            assert governor.is_socket_pressure_active() is True
            # Concurrency halved under socket pressure
            assert governor.get_allowed_concurrency("example.com") == 5
            assert governor.get_global_concurrency_limit() == 5

            # If active workers already reach half ceiling, cannot acquire more
            governor.active_workers["example.com"] = 5
            assert governor.can_acquire_worker("example.com") is False

    def test_report_socket_error_triggers_emergency_brake(self):
        governor = CrawlGovernor(initial_concurrency=8, min_concurrency=1)
        governor.report_yield("test.com", 10)

        # Report Windows WSAENOBUFS (10055)
        governor.report_socket_error(10055)
        assert governor.is_socket_pressure_active() is True
        assert governor.get_allowed_concurrency("test.com") == 4


# =========================================================================
# 3. SqliteTaskBroker Multi-Process Leasing & Idempotency
# =========================================================================

class TestSqliteTaskBroker:
    def test_push_pop_and_ack_lifecycle(self, tmp_path):
        db_file = tmp_path / "test_tasks.db"
        broker = SqliteTaskBroker(db_path=str(db_file), consumer_name="worker_alpha")

        assert broker.get_queue_length("test_queue") == 0

        payload = {"task_id": "job_101", "url": "https://example.com/item"}
        assert broker.push_task("test_queue", payload) is True
        assert broker.get_queue_length("test_queue") == 1

        # Pop leases task
        leased = broker.pop_task("test_queue", timeout=0.5)
        assert leased is not None
        assert leased["task_id"] == "job_101"
        assert leased["_task_id"] == "job_101"
        assert leased["delivery_count"] == 1
        # Once leased, no more pending tasks
        assert broker.get_queue_length("test_queue") == 0

        # Ack task marks completed
        assert broker.ack_task("test_queue", "job_101") is True

    def test_autoclaim_abandoned_tasks(self, tmp_path):
        db_file = tmp_path / "test_abandoned.db"
        broker_1 = SqliteTaskBroker(db_path=str(db_file), consumer_name="worker_dead")
        broker_2 = SqliteTaskBroker(db_path=str(db_file), consumer_name="worker_survivor")

        broker_1.push_task("crawl_queue", {"task_id": "job_dead", "url": "https://abandoned.com"})
        leased = broker_1.pop_task("crawl_queue", timeout=0.5)
        assert leased is not None

        # Manually backdate leased_at to simulate worker crash timeout
        with broker_1._get_connection() as conn:
            conn.execute("UPDATE broker_tasks SET leased_at = ? WHERE task_id = ?", (time.time() - 100.0, "job_dead"))
            conn.commit()

        # Surviving worker claims abandoned task
        reclaimed = broker_2.autoclaim_abandoned_tasks("crawl_queue", min_idle_ms=5000)
        assert len(reclaimed) == 1
        assert reclaimed[0]["task_id"] == "job_dead"
        assert reclaimed[0]["delivery_count"] == 2

    def test_idempotency_lock_and_release(self, tmp_path):
        db_file = tmp_path / "test_locks.db"
        broker = SqliteTaskBroker(db_path=str(db_file), consumer_name="worker_1")

        # First acquisition succeeds
        assert broker.acquire_idempotency_lock("task_alpha", "worker_1", ttl_seconds=10) is True
        # Second acquisition by worker_2 fails while lock is active
        assert broker.acquire_idempotency_lock("task_alpha", "worker_2", ttl_seconds=10) is False

        # Release lock allows new acquisition
        assert broker.release_idempotency_lock("task_alpha") is True
        assert broker.acquire_idempotency_lock("task_alpha", "worker_2", ttl_seconds=10) is True

    def test_route_dead_letter(self, tmp_path):
        db_file = tmp_path / "test_dlq.db"
        broker = SqliteTaskBroker(db_path=str(db_file))

        ok = broker.route_dead_letter("poison_queue", "msg_99", {"task_id": "job_err"}, "Traceback: ZeroDivisionError")
        assert ok is True

        with broker._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT queue_name, task_id, error_trace FROM broker_dead_letters")
            row = cursor.fetchone()
            assert row[0] == "poison_queue"
            assert row[1] == "msg_99"
            assert "ZeroDivisionError" in row[2]


# =========================================================================
# 4. DistributedWorkerNode with Sqlite Broker
# =========================================================================

class TestDistributedWorkerNodeSqlite:
    def test_worker_initialization_with_sqlite_url(self, tmp_path):
        from core.distributed_worker import DistributedWorkerNode

        db_path = str(tmp_path / "cluster_tasks.db")
        sqlite_url = f"sqlite://{db_path}"

        worker = DistributedWorkerNode(broker_url=sqlite_url, role="crawl", consumer_name="worker_node_1")
        assert isinstance(worker.broker, SqliteTaskBroker)
        assert worker.worker_id == "worker_node_1"

        # Push task and process it via worker node
        worker.broker.push_task("scrape:crawl_stream", {"task_id": "task_crawl_1", "url": "https://node.org"})
        processed_task = worker.process_one_task("scrape:crawl_stream", timeout=0.5)
        assert processed_task is not None
        assert processed_task["task_id"] == "task_crawl_1"


# =========================================================================
# 5. Tier 4 VLM Self-Healing DOM Parser Integration
# =========================================================================

class TestSelfHealingDOMParserVLM:
    def test_tier_4_vlm_escalation_and_cache_promotion(self, tmp_path):
        db_path = tmp_path / "vlm_repaired.db"
        parser = SelfHealingDOMParser(db_path=db_path, enable_vlm=True)

        html = """
        <html>
            <body>
                <div class="obfuscated_container_xyz99">
                    <img data-vlm-target="/images/gallery_photo_01.jpg" alt="Art 1" />
                    <img data-vlm-target="/images/gallery_photo_02.jpg" alt="Art 2" />
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        page_url = "https://vlm-target-site.com/gallery"

        # Mock VLM Healer to simulate vision model returning verified selector
        mock_vlm_result = MagicMock()
        mock_vlm_result.selector = ".obfuscated_container_xyz99 img"
        mock_vlm_result.attr = "data-vlm-target"
        mock_vlm_result.confidence = 0.95

        mock_healer = MagicMock()
        mock_healer.heal.return_value = mock_vlm_result
        parser._vlm_healer = mock_healer

        screenshot_bytes = b"fake_png_viewport_bytes"

        # Extract triggers Tier 4 VLM
        items = parser.extract(soup, page_url=page_url, screenshot_bytes=screenshot_bytes)

        assert len(items) == 2
        assert items[0].url == "https://vlm-target-site.com/images/gallery_photo_01.jpg"
        assert items[0].extraction_source == "self_healing_vlm:.obfuscated_container_xyz99 img"

        # Promoted to Tier 1 cache database
        metrics = parser.get_metrics()
        assert metrics["total_repaired_domains"] == 1
        assert metrics["repaired_domains"][0]["domain"] == "vlm-target-site.com"
        assert metrics["repaired_domains"][0]["selector"] == ".obfuscated_container_xyz99 img"
        assert metrics["repaired_domains"][0]["attr"] == "data-vlm-target"


# =========================================================================
# 5. Seed Concurrency Priming & Domain Succession Hardening
# =========================================================================

class TestCrawlSuccessionAndGovernorPriming:
    def test_governor_seed_hosts_initial_concurrency_boost(self):
        governor = CrawlGovernor(initial_concurrency=8, min_concurrency=1)
        governor.register_seed_hosts(["seedsite.com", "gallery.org"])

        # Unseeded host starts with 1 worker prior to yield
        assert governor.get_allowed_concurrency("unseeded.com") == 1

        # Seeded host starts with 2 workers to jumpstart broad discovery
        assert governor.get_allowed_concurrency("seedsite.com") == 2
        assert governor.get_allowed_concurrency("www.seedsite.com") == 2

        # After first successful response, seeded host scales into AIMD window
        governor.report_success("seedsite.com", latency_s=0.5)
        assert governor.get_allowed_concurrency("seedsite.com") >= 2

    def test_is_same_domain_and_subdomain_normalizes_www(self):
        from core.url_classifier import is_same_domain, is_subdomain_of

        assert is_same_domain("https://www.erome.com/a/123", "https://erome.com/search") is True
        assert is_same_domain("https://erome.com/a/123", "https://www.erome.com/search") is True
        assert is_same_domain("https://site.com", "https://diff.com") is False

        assert is_subdomain_of("https://cdn.erome.com/i/1.jpg", "www.erome.com") is True
        assert is_subdomain_of("https://www.erome.com/i/1.jpg", "erome.com") is True

    def test_preflight_bounded_concurrency(self):
        import asyncio
        from unittest.mock import AsyncMock
        from core.coordinator import CrawlCoordinator

        options = MagicMock()
        options.max_results = 10
        options.seed_domains = ["test.com"]
        options.domain_profiles = {}
        options.seed_urls = []

        coordinator = CrawlCoordinator(
            search_provider=MagicMock(),
            video_scraper=MagicMock(),
            options=options,
            result=MagicMock(),
            state_cache=None,
            workers=4,
        )

        urls = [f"https://test.com/item/{i}" for i in range(25)]
        with patch("core.coordinator.httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_client.head = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

            valid = asyncio.run(coordinator._run_preflight(urls))
            assert len(valid) == 25
            assert mock_client.head.call_count == 25


# =========================================================================
# 6. Core Optimization, Half-Open Circuit Breaking & Cooldown Sync
# =========================================================================

class TestCoreOptimizationAndCircuitBreaker:
    def test_circuit_breaker_half_open_single_flight_canary(self):
        from network.stealth.base import _StrategyCircuitBreaker

        cb = _StrategyCircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)
        strategy = "camoufox"
        host = "challenge-target.com"

        # Initially healthy
        assert cb.is_cooling_down(strategy, host) is False

        # Trip circuit breaker
        cb.record_failure(strategy, host)
        cb.record_failure(strategy, host)
        assert cb.is_cooling_down(strategy, host) is True

        # Wait for cooldown to elapse
        time.sleep(0.15)

        # Thread 1: gets canary probe (is_cooling_down == False)
        assert cb.is_cooling_down(strategy, host) is False

        # Thread 2: blocked during in-flight canary probe (is_cooling_down == True)
        assert cb.is_cooling_down(strategy, host) is True

        # Canary probe succeeds -> tier restored for everyone
        cb.record_success(strategy, host)
        assert cb.is_cooling_down(strategy, host) is False

    def test_domain_profiler_mtime_cached_loading(self, tmp_path):
        import json
        from core.profiler import DomainProfiler

        d_conf = tmp_path / "domain_config.json"
        r_conf = tmp_path / "url_normalisation_rules.json"
        d_conf.write_text(json.dumps({"auto_mapped": ["cached.com"]}), encoding="utf-8")
        r_conf.write_text(json.dumps([]), encoding="utf-8")

        profiler = DomainProfiler()
        profiler.domain_config_path = d_conf
        profiler.rules_config_path = r_conf
        profiler._load_configs(force=True)

        assert profiler.domain_config.get("auto_mapped") == ["cached.com"]

        # Call _load_configs again; mtime is unchanged, so no disk re-parsing
        old_mtime = profiler._domain_config_mtime
        profiler._load_configs()
        assert profiler._domain_config_mtime == old_mtime

    def test_url_normalization_and_archetype_caching(self):
        from core.url_classifier import normalize_url, normalize_media_url
        from core.priority_queue import URLPatternBandit

        raw_url = "https://example.com/gallery/12345/view?utm_source=twitter&hl=en"
        norm1 = normalize_url(raw_url)
        norm2 = normalize_url(raw_url)
        assert norm1 == norm2
        assert "utm_source" not in norm1
        assert "hl=" not in norm1

        media1 = normalize_media_url("https://cdn.example.com/images/Pic_01.JPG?w=500")
        media2 = normalize_media_url("https://cdn.example.com/images/Pic_01.JPG?w=500")
        assert media1 == media2
        assert media1 == "https://cdn.example.com/images/pic_01.jpg"

        bandit = URLPatternBandit()
        arch1 = bandit.extract_archetype("https://site.com/art/001/full")
        arch2 = bandit.extract_archetype("https://site.com/art/999/full")
        assert arch1 == arch2 == "site.com::/art/{id}/full"

    def test_http_client_cooldown_sync(self):
        from network.http_client import HttpClient

        client = HttpClient()
        host = "ratelimited-api.com"

        # Initially no cooldown
        assert client.get_domain_cooldown_remaining(host) == 0.0

        # Simulate 3 consecutive 429s to cross DOMAIN_COOLDOWN_THRESHOLD
        cd_state = client._cooldown_state_for(f"https://{host}/page")
        duration = None
        for _ in range(3):
            duration = cd_state.record_429()

        assert duration is not None
        assert client.get_domain_cooldown_remaining(host) > 0.0

    def test_coordinator_host_parking_and_batch_requeue(self):
        from core.priority_queue import AdaptiveCrawlQueue

        q = AdaptiveCrawlQueue()
        host = "saturated-domain.com"
        q.push(f"https://{host}/page1", depth=1, score=90.0)
        q.push(f"https://{host}/page2", depth=1, score=85.0)
        q.push("https://other-domain.com/index", depth=1, score=50.0)

        # Simulate coordinator parking saturated host items
        item1 = q.pop()
        assert item1[5] == f"https://{host}/page1"
        q.park_host(host, item1)

        item2 = q.pop()
        assert item2[5] == f"https://{host}/page2"
        q.park_host(host, item2)

        # Only other-domain remains in ready heap
        top = q.pop()
        assert top[5] == "https://other-domain.com/index"

        # Saturated items remain tracked in length
        assert len(q) == 2
        # When worker finishes for host, unpark restores them
        restored = q.unpark_host(host)
        assert restored == 2
        assert len(q) == 2

        first_unparked = q.pop()
        assert first_unparked[5] == f"https://{host}/page1"
        assert first_unparked[0] == 90.0

    def test_governor_server_overload_exponential_backoff(self):
        gov = CrawlGovernor(initial_concurrency=4)
        host = "overloaded-api.com"

        # 3 consecutive 503 errors trigger exponential backoff without marking host failed
        gov.report_error(host, is_server_overload=True)
        assert gov.cooldown_remaining(host) > 0.0
        assert host not in gov.failed_hosts

        gov.report_error(host, is_server_overload=True)
        assert host not in gov.failed_hosts

        gov.report_error(host, is_server_overload=True)
        assert host not in gov.failed_hosts
        assert gov.cooldown_remaining(host) >= 15.0

    def test_governor_parked_half_open_single_flight_canary(self):
        gov = CrawlGovernor(initial_concurrency=4)
        host = "recovering-host.com"

        # Drive rolling success rate below 0.25 (5 attempts, 1 success, 4 429/overload)
        gov.report_success(host)
        gov.report_429(host, cooldown_s=1.0)
        gov.report_error(host, is_server_overload=True)
        gov.report_429(host, cooldown_s=1.0)
        gov.report_error(host, is_server_overload=True)

        assert gov.get_host_health_state(host) == "PARKED"
        assert gov.get_allowed_concurrency(host) == 1

        # Simulate cooldown expiration
        gov.host_cooldowns[host] = time.monotonic() - 1.0

        # Worker 1 can acquire canary probe
        assert gov.is_host_available(host) is True
        gov.increment_worker(host)

        # Worker 2 blocked while canary probe is in-flight
        assert gov.is_host_available(host) is False

        # Canary finishes with success -> restores health
        gov.decrement_worker(host)
        gov.report_success(host)
        assert gov.consecutive_host_failures[host] == 0

    def test_coordinator_bounded_rejected_items(self):
        from core.coordinator import CrawlCoordinator
        from core.models import ScrapeResult

        coord = CrawlCoordinator(
            search_provider=MagicMock(),
            video_scraper=MagicMock(),
            options=MagicMock(),
            result=ScrapeResult(keyword="test"),
            state_cache=None,
            workers=2,
        )

        # Add 10,050 unique rejected items
        for i in range(10050):
            coord.add_rejected("page", f"https://test.com/rejected_{i}", "https://test.com", "junk_pattern")

        # Result list is bounded at 10,000 items to protect memory footprint
        assert len(coord.result.rejected_items) == 10000



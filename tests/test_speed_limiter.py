"""
test_speed_limiter.py — Unit tests for BandwidthLimiter and global rate limiters.
"""

from __future__ import annotations

import time
import pytest
from utils.bandwidth_limiter import BandwidthLimiter
from utils.http_client import HttpClient
from cli.main import build_parser


def test_bandwidth_limiter_unlimited():
    limiter = BandwidthLimiter(max_kbps=0)
    start = time.monotonic()
    # 1MB byte chunk with 0 limit should take < 0.05s
    limiter.throttle(1024 * 1024)
    elapsed = time.monotonic() - start
    assert elapsed < 0.1


def test_bandwidth_limiter_throttled():
    # 100 KB/s limit -> 50 KB chunk should take approx ~0.5s
    limiter = BandwidthLimiter(max_kbps=100)
    # Drain initial burst capacity
    limiter.throttle(100 * 1024)
    start = time.monotonic()
    limiter.throttle(50 * 1024)
    elapsed = time.monotonic() - start
    assert elapsed >= 0.35


def test_cli_parser_speed_limiter_flags():
    parser = build_parser()
    args = parser.parse_args(["--dl-speed-limit", "1500", "--rate-limit", "2.5"])
    assert args.dl_speed_limit == 1500
    assert args.rate_limit == 2.5


def test_http_client_global_rate_limit():
    client = HttpClient(global_rate_limit_rps=2.0)
    assert client.global_rate_limit_rps == 2.0
    rl = client._rate_limiter_for("https://example.com/test")
    assert rl.requests_per_second <= 2.0

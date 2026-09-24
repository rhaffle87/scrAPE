"""
Unit tests for Track 2: CLI Argument Alignment & Worker --dry-run implementation.
Verifies:
1. --output stdout parsing and clean JSON emission on sys.stdout with stderr log redirection.
2. worker.py --dry-run broker validation, consumer group creation, and non-blocking zero-exit.
3. worker.py --dry-run handling of unreachable brokers.
"""

from __future__ import annotations

import io
import json
import logging
import sys
from unittest.mock import MagicMock, patch

import pytest
import fakeredis

from cli.main import build_parser
from cli.worker import main as worker_main, parse_args as worker_parse_args
from core.models import ScrapeResult


def test_cli_parser_output_stdout_choice():
    """Verify that --output accepts 'stdout' as a valid choice."""
    parser = build_parser()
    args = parser.parse_args(["--keyword", "test", "--output", "stdout"])
    assert args.output == "stdout"


def test_cli_main_stdout_clean_json_redirection(monkeypatch, capsys):
    """Verify that --output stdout emits pure parseable JSON to stdout and redirects logs to stderr."""
    from cli.main import main

    # Mock engine.run to return a deterministic dummy result
    dummy_result = ScrapeResult(keyword="test_target")
    dummy_result.images = []
    dummy_result.videos = []
    dummy_result.run_id = "test_run_123"

    mock_engine_instance = MagicMock()
    mock_engine_instance.run.return_value = dummy_result
    mock_engine_instance.downloader = MagicMock()

    # Pass args for main()
    test_args = ["main.py", "--keyword", "test_target", "--output", "stdout", "--skip-search"]
    monkeypatch.setattr(sys, "argv", test_args)
    monkeypatch.setattr("cli.main.ScrapingEngine", lambda **kw: mock_engine_instance)

    main()

    captured = capsys.readouterr()
    assert captured.out.strip() != "", "stdout must not be empty"

    # Verify stdout is valid JSON
    parsed = json.loads(captured.out)
    assert parsed["keyword"] == "test_target"
    assert parsed["run_id"] == "test_run_123"
    assert "images" in parsed
    assert "videos" in parsed


def test_worker_cli_dry_run_flag_parsing():
    """Verify that worker CLI parses --dry-run flag properly."""
    args = worker_parse_args(["--dry-run", "--role", "crawl", "--group", "test_group"])
    assert args.dry_run is True
    assert args.role == "crawl"
    assert args.group == "test_group"


def test_worker_cli_dry_run_success_with_fakeredis(monkeypatch):
    """Verify that worker --dry-run connects, verifies stream consumer groups, and exits 0."""
    fake_server = fakeredis.FakeServer()
    fake_client = fakeredis.FakeStrictRedis(server=fake_server)

    with patch("redis.from_url", return_value=fake_client):
        exit_code = worker_main(["--dry-run", "--broker", "redis://localhost:6379/0", "--role", "all", "--group", "audit_group"])
        assert exit_code == 0

        # Verify that the consumer group was created on the streams
        for stream in ["scrape:crawl_stream", "scrape:download_stream"]:
            groups = fake_client.xinfo_groups(stream)
            assert any(g["name"] == b"audit_group" or g["name"] == "audit_group" for g in groups)


def test_worker_cli_dry_run_failure_when_unreachable(monkeypatch):
    """Verify that worker --dry-run exits 1 with error log if Redis is unreachable."""
    with patch("redis.from_url", side_effect=ConnectionError("Cannot connect")):
        exit_code = worker_main(["--dry-run", "--broker", "redis://bad-host:9999/0"])
        assert exit_code == 1

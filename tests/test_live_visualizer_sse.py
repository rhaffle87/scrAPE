from __future__ import annotations

import json
import pytest
from monitoring.telemetry import (
    register_telemetry_listener,
    unregister_telemetry_listener,
    broadcast_telemetry_event,
)


def test_telemetry_listener_registration_and_dispatch():
    received_events = []

    def mock_listener(event_type: str, data: dict):
        received_events.append((event_type, data))

    register_telemetry_listener(mock_listener)

    try:
        broadcast_telemetry_event("crawl_graph_node", {
            "url": "https://example.com/page1",
            "domain": "example.com",
            "depth": 0,
            "type": "page_visited",
        })

        broadcast_telemetry_event("media_downloaded", {
            "url": "https://example.com/image.jpg",
            "file_path": "example/images/image.jpg",
            "media_kind": "image",
            "width": 1920,
            "height": 1080,
        })

        assert len(received_events) == 2
        assert received_events[0][0] == "crawl_graph_node"
        assert received_events[0][1]["domain"] == "example.com"
        assert received_events[1][0] == "media_downloaded"
        assert received_events[1][1]["width"] == 1920

    finally:
        unregister_telemetry_listener(mock_listener)


def test_broadcaster_subscribers_receive_telemetry(tmp_path):
    from frontend.app import LogBroadcaster

    bc = LogBroadcaster()

    q = bc.subscribe()
    try:
        bc.broadcast("crawl_graph_node", {
            "url": "https://test.com/item",
            "domain": "test.com",
            "depth": 1,
        })

        msg = q.get_nowait()
        assert "event: crawl_graph_node" in msg
        assert '"domain": "test.com"' in msg
    finally:
        bc.unsubscribe(q)

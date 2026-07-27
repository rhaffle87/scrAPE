from __future__ import annotations

import asyncio
import json
import pytest
from fastapi.testclient import TestClient

from frontend.app import app, LogBroadcaster, broadcaster, log_buffer


@pytest.mark.anyio
async def test_log_broadcaster_pub_sub():
    test_broadcaster = LogBroadcaster()
    q1 = test_broadcaster.subscribe()
    q2 = test_broadcaster.subscribe()

    test_broadcaster.broadcast("test_event", {"msg": "hello"})

    msg1 = q1.get_nowait()
    msg2 = q2.get_nowait()

    assert "event: test_event" in msg1
    assert '"msg": "hello"' in msg1
    assert msg1 == msg2

    test_broadcaster.unsubscribe(q1)
    test_broadcaster.broadcast("test_event2", {"msg": "world"})

    assert q1.empty() is True
    assert "test_event2" in q2.get_nowait()


def test_api_logs_offset_polling_backward_compatibility():
    client = TestClient(app)
    log_buffer.clear()
    log_buffer.append("Line 1: Test scrape initiated")
    log_buffer.append("Line 2: Fetching page https://example.com")

    resp = client.get("/api/logs?offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert "lines" in data
    assert len(data["lines"]) == 2
    assert data["next_offset"] == 2


@pytest.mark.anyio
async def test_api_logs_stream_generator():
    from unittest.mock import AsyncMock
    from frontend.app import stream_logs

    log_buffer.clear()
    log_buffer.append("Direct generator log test")

    mock_request = AsyncMock()
    mock_request.is_disconnected = AsyncMock(side_effect=[False, True])

    response = await stream_logs(mock_request)
    assert response.media_type == "text/event-stream"

    first_chunk = None
    async for chunk in response.body_iterator:
        first_chunk = chunk
        break

    assert first_chunk is not None
    chunk_str = first_chunk.decode("utf-8") if isinstance(first_chunk, bytes) else str(first_chunk)
    assert "event: log" in chunk_str
    assert "Direct generator log test" in chunk_str

import pytest
from fastapi.testclient import TestClient
from frontend.app import app

client = TestClient(app)


def test_api_telemetry_stats_snapshot():
    """Verify /api/telemetry/stats returns structured metric snapshot."""
    response = client.get("/api/telemetry/stats")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "rps" in data
    assert "speed_kbps" in data
    assert "active_workers" in data
    assert "http_status_codes" in data
    assert "200_ok" in data["http_status_codes"]
    assert "429_rate_limit" in data["http_status_codes"]
    assert "waf_bypasses" in data["http_status_codes"]


@pytest.mark.anyio
async def test_api_telemetry_stream_endpoint():
    """Verify /api/telemetry/stream generator returns event-stream payload."""
    from unittest.mock import AsyncMock
    from frontend.app import stream_telemetry

    mock_request = AsyncMock()
    mock_request.is_disconnected = AsyncMock(side_effect=[False, True])

    response = await stream_telemetry(mock_request)
    assert response.media_type == "text/event-stream"

    first_chunk = None
    async for chunk in response.body_iterator:
        first_chunk = chunk
        break

    assert first_chunk is not None
    chunk_str = first_chunk.decode("utf-8") if isinstance(first_chunk, bytes) else str(first_chunk)
    assert "event: telemetry" in chunk_str

from __future__ import annotations

import json
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# List of registered event listeners (e.g. LogBroadcaster.broadcast)
_TELEMETRY_LISTENERS: list[Callable[[str, dict[str, Any]], None]] = []


def register_telemetry_listener(listener: Callable[[str, dict[str, Any]], None]) -> None:
    """Register a listener function for real-time telemetry events."""
    if listener not in _TELEMETRY_LISTENERS:
        _TELEMETRY_LISTENERS.append(listener)


def unregister_telemetry_listener(listener: Callable[[str, dict[str, Any]], None]) -> None:
    """Unregister a telemetry event listener."""
    if listener in _TELEMETRY_LISTENERS:
        _TELEMETRY_LISTENERS.remove(listener)


def broadcast_telemetry_event(event_type: str, data: dict[str, Any]) -> None:
    """Broadcast a real-time telemetry event to all registered listeners."""
    for listener in _TELEMETRY_LISTENERS:
        try:
            listener(event_type, data)
        except Exception as err:
            logger.debug(f"Failed to deliver telemetry event {event_type}: {err}")

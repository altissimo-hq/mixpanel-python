"""Shared test fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pytest

from altissimo.mixpanel import MixpanelClient


@dataclass
class RecordingConsumer:
    """A consumer that records all sent messages for test assertions."""

    sent: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def send(self, endpoint: str, json_message: str, api_key: str | None = None) -> None:
        """Record a sent message."""
        self.sent.append((endpoint, json.loads(json_message)))


@dataclass
class FailingConsumer:
    """A consumer that always raises an exception."""

    error: Exception = field(default_factory=lambda: RuntimeError("Consumer failed"))

    def send(self, endpoint: str, json_message: str, api_key: str | None = None) -> None:
        """Always raise an error."""
        raise self.error


@pytest.fixture
def recording_consumer() -> RecordingConsumer:
    """Provide a fresh recording consumer."""
    return RecordingConsumer()


@pytest.fixture
def failing_consumer() -> FailingConsumer:
    """Provide a consumer that raises on send."""
    return FailingConsumer()


@pytest.fixture
def client(recording_consumer: RecordingConsumer) -> MixpanelClient:
    """Provide a MixpanelClient wired to a recording consumer."""
    return MixpanelClient(token="test-token", consumer=recording_consumer)


@pytest.fixture
def disabled_client() -> MixpanelClient:
    """Provide a disabled MixpanelClient."""
    return MixpanelClient(token="test-token", enabled=False)

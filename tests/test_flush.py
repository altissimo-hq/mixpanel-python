"""Tests for flushing buffered events."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from mixpanel import BufferedConsumer

from altissimo.mixpanel import MixpanelClient

from .conftest import FailingFlushConsumer, RecordingConsumer


class TestFlush:
    """flush() sends what a buffering consumer is holding."""

    def test_buffered_events_sent_on_flush(self) -> None:
        # BufferedConsumer sends each batch through an inner Consumer.send
        with patch("mixpanel.Consumer.send") as send:
            client = MixpanelClient(token="test-token", consumer=BufferedConsumer())
            client.track("user-123", "Event A")
            client.track("user-123", "Event B")
            assert send.call_count == 0

            client.flush()

        assert send.call_count == 1
        endpoint, batch = send.call_args.args[:2]
        assert endpoint == "events"
        assert "Event A" in batch
        assert "Event B" in batch

    def test_flush_with_default_consumer_is_noop(self) -> None:
        client = MixpanelClient(token="test-token")
        client.flush()  # should not raise or build the SDK client
        assert getattr(client._local, "mp", None) is None

    def test_flush_with_consumer_without_flush_is_noop(self, client: MixpanelClient) -> None:
        client.flush()  # RecordingConsumer has no flush method

    def test_flush_when_disabled_is_noop(self) -> None:
        consumer = MagicMock()
        client = MixpanelClient(token="test-token", enabled=False, consumer=consumer)

        client.flush()

        consumer.flush.assert_not_called()


class TestContextManager:
    """Leaving a ``with`` block flushes the client."""

    def test_flushes_on_exit(self) -> None:
        consumer = MagicMock()
        with MixpanelClient(token="test-token", consumer=consumer) as client:
            assert isinstance(client, MixpanelClient)
            consumer.flush.assert_not_called()

        consumer.flush.assert_called_once_with()

    def test_flushes_when_block_raises(self) -> None:
        consumer = MagicMock()
        with pytest.raises(ValueError, match="boom"), MixpanelClient(token="test-token", consumer=consumer):
            raise ValueError("boom")

        consumer.flush.assert_called_once_with()

    def test_track_then_exit_sends_buffered_events(self) -> None:
        with patch("mixpanel.Consumer.send") as send:
            with MixpanelClient(token="test-token", consumer=BufferedConsumer()) as client:
                client.track("user-123", "Event A")
                assert send.call_count == 0

            assert send.call_count == 1


class TestFlushErrors:
    """A failing flush follows ``on_error`` like every other operation."""

    def test_log(self, caplog: pytest.LogCaptureFixture) -> None:
        client = MixpanelClient(token="test-token", consumer=FailingFlushConsumer(), on_error="log")

        with caplog.at_level(logging.ERROR):
            client.flush()

        assert "Mixpanel flush error" in caplog.text

    def test_raise(self) -> None:
        client = MixpanelClient(token="test-token", consumer=FailingFlushConsumer(), on_error="raise")

        with pytest.raises(RuntimeError, match="Flush failed"):
            client.flush()

    def test_ignore(self, caplog: pytest.LogCaptureFixture) -> None:
        client = MixpanelClient(token="test-token", consumer=FailingFlushConsumer(), on_error="ignore")

        with caplog.at_level(logging.ERROR):
            client.flush()

        assert "Mixpanel" not in caplog.text


def test_recording_consumer_unaffected_by_flush(client: MixpanelClient, recording_consumer: RecordingConsumer) -> None:
    client.track("user-123", "Event")
    client.flush()
    assert len(recording_consumer.sent) == 1

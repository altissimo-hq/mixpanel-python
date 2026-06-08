"""Tests for error handling modes."""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from altissimo.mixpanel import MixpanelClient

from .conftest import FailingConsumer


class TestOnErrorLog:
    """on_error='log' should catch exceptions and log them."""

    def test_track_logs_error(self, failing_consumer: FailingConsumer, caplog: pytest.LogCaptureFixture) -> None:
        client = MixpanelClient(token="test-token", consumer=failing_consumer, on_error="log")

        with caplog.at_level(logging.ERROR):
            client.track("user-123", "Event")

        assert "Mixpanel track error" in caplog.text

    def test_people_set_logs_error(self, failing_consumer: FailingConsumer, caplog: pytest.LogCaptureFixture) -> None:
        client = MixpanelClient(token="test-token", consumer=failing_consumer, on_error="log")

        with caplog.at_level(logging.ERROR):
            client.people_set("user-123", {"key": "val"})

        assert "Mixpanel people_set error" in caplog.text


class TestOnErrorRaise:
    """on_error='raise' should re-raise exceptions."""

    def test_track_raises(self, failing_consumer: FailingConsumer) -> None:
        client = MixpanelClient(token="test-token", consumer=failing_consumer, on_error="raise")

        with pytest.raises(RuntimeError, match="Consumer failed"):
            client.track("user-123", "Event")

    def test_people_set_raises(self, failing_consumer: FailingConsumer) -> None:
        client = MixpanelClient(token="test-token", consumer=failing_consumer, on_error="raise")

        with pytest.raises(RuntimeError, match="Consumer failed"):
            client.people_set("user-123", {"key": "val"})

    def test_alias_raises(self, failing_consumer: FailingConsumer) -> None:
        client = MixpanelClient(token="test-token", consumer=failing_consumer, on_error="raise")

        # alias() bypasses custom consumers and uses its own sync Consumer,
        # so we mock the sync consumer to simulate failure
        with (
            patch("mixpanel.Consumer.send", side_effect=RuntimeError("Consumer failed")),
            pytest.raises(RuntimeError, match="Consumer failed"),
        ):
            client.alias("new-id", "original-id")


class TestOnErrorIgnore:
    """on_error='ignore' should silently swallow exceptions."""

    def test_track_ignores(self, failing_consumer: FailingConsumer, caplog: pytest.LogCaptureFixture) -> None:
        client = MixpanelClient(token="test-token", consumer=failing_consumer, on_error="ignore")

        with caplog.at_level(logging.ERROR):
            client.track("user-123", "Event")  # should not raise

        assert "Mixpanel" not in caplog.text

    def test_people_set_ignores(self, failing_consumer: FailingConsumer, caplog: pytest.LogCaptureFixture) -> None:
        client = MixpanelClient(token="test-token", consumer=failing_consumer, on_error="ignore")

        with caplog.at_level(logging.ERROR):
            client.people_set("user-123", {"key": "val"})  # should not raise

        assert "Mixpanel" not in caplog.text

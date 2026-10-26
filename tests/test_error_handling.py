"""Tests for error handling modes."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from altissimo.mixpanel import MixpanelClient, MixpanelImportError

from .conftest import FailingConsumer

if TYPE_CHECKING:
    from collections.abc import Iterator


class TestMissingSdk:
    """A missing ``mixpanel`` SDK is reported once, not on every call."""

    @pytest.fixture(autouse=True)
    def _no_sdk(self) -> Iterator[None]:
        # A None entry makes ``import mixpanel`` raise ImportError
        with patch.dict(sys.modules, {"mixpanel": None}):
            yield

    def test_log_once_then_disabled(self, caplog: pytest.LogCaptureFixture) -> None:
        client = MixpanelClient(token="test-token", on_error="log")

        with caplog.at_level(logging.ERROR):
            client.track("user-123", "Event A")
            client.track("user-123", "Event B")
            client.people_set("user-123", {"key": "val"})

        errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert len(errors) == 1
        assert "Mixpanel tracking disabled" in errors[0].getMessage()
        assert "pip install altissimo-mixpanel[mixpanel]" in errors[0].getMessage()
        assert errors[0].exc_info is None  # no traceback for a setup error
        assert not client.enabled

    def test_raise(self) -> None:
        client = MixpanelClient(token="test-token", on_error="raise")

        with pytest.raises(MixpanelImportError):
            client.track("user-123", "Event")

    def test_ignore_disables_silently(self, caplog: pytest.LogCaptureFixture) -> None:
        client = MixpanelClient(token="test-token", on_error="ignore")

        with caplog.at_level(logging.ERROR):
            client.track("user-123", "Event")

        assert caplog.records == []
        assert not client.enabled


def test_handle_error_raises_outside_except_block() -> None:
    """``_handle_error`` re-raises the exception it is given, wherever it's called from."""
    client = MixpanelClient(token="test-token", on_error="raise")

    with pytest.raises(ValueError, match="given"):
        client._handle_error(ValueError("given"), "track")


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

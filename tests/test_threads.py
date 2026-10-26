"""Tests for sharing one MixpanelClient across threads."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from altissimo.mixpanel import MixpanelClient

from .conftest import RecordingConsumer

if TYPE_CHECKING:
    from collections.abc import Callable

    from mixpanel import Mixpanel

THREADS = 8


def _run_in_threads(target: Callable[[], None], count: int = THREADS) -> None:
    """Run ``target`` in ``count`` threads that all start together."""
    barrier = threading.Barrier(count)

    def run() -> None:
        barrier.wait()
        target()

    threads = [threading.Thread(target=run) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


class TestPerThreadSdkClient:
    """Each thread gets its own Mixpanel instance."""

    def test_default_consumer_one_instance_per_thread(self) -> None:
        client = MixpanelClient(token="test-token")
        instances: list[Mixpanel] = []
        lock = threading.Lock()

        def get() -> None:
            first = client._get_mp()
            assert client._get_mp() is first  # reused within the thread
            with lock:
                instances.append(first)

        _run_in_threads(get)

        assert len({id(mp) for mp in instances}) == THREADS
        # The SDK's default Consumer, and with it the HTTP session, isn't shared either
        assert len({id(mp._consumer) for mp in instances}) == THREADS

    def test_consumer_factory_called_once_per_thread(self) -> None:
        made: list[RecordingConsumer] = []
        lock = threading.Lock()

        def factory() -> RecordingConsumer:
            consumer = RecordingConsumer()
            with lock:
                made.append(consumer)
            return consumer

        client = MixpanelClient(token="test-token", consumer_factory=factory)

        def track_twice() -> None:
            client.track("user-123", "Event A")
            client.track("user-123", "Event B")

        _run_in_threads(track_twice)

        assert len(made) == THREADS
        assert all(len(consumer.sent) == 2 for consumer in made)

    def test_shared_consumer_used_by_every_thread(self) -> None:
        consumer = RecordingConsumer()
        client = MixpanelClient(token="test-token", consumer=consumer)
        consumers: list[object] = []
        lock = threading.Lock()

        def get() -> None:
            mp = client._get_mp()
            with lock:
                consumers.append(mp._consumer)

        _run_in_threads(get)

        assert all(c is consumer for c in consumers)


class TestFlushAcrossThreads:
    """flush() reaches the consumer of every thread that used the client."""

    def test_flushes_every_factory_consumer(self) -> None:
        made: list[MagicMock] = []
        lock = threading.Lock()

        def factory() -> MagicMock:
            consumer = MagicMock()
            with lock:
                made.append(consumer)
            return consumer

        client = MixpanelClient(token="test-token", consumer_factory=factory)
        _run_in_threads(lambda: client.track("user-123", "Event"))

        client.flush()

        assert len(made) == THREADS
        for consumer in made:
            consumer.flush.assert_called_once_with()

    def test_flush_before_any_thread_tracked_is_noop(self) -> None:
        factory = MagicMock()
        client = MixpanelClient(token="test-token", consumer_factory=factory)

        client.flush()

        factory.assert_not_called()

    def test_one_failing_flush_doesnt_stop_the_rest_when_logging(self) -> None:
        failing = MagicMock()
        failing.flush.side_effect = RuntimeError("Flush failed")
        ok = MagicMock()
        consumers = iter([failing, ok])
        client = MixpanelClient(token="test-token", consumer_factory=lambda: next(consumers), on_error="log")
        _run_in_threads(lambda: client.track("user-123", "Event"), count=2)

        client.flush()

        failing.flush.assert_called_once_with()
        ok.flush.assert_called_once_with()


class TestConsumerArguments:
    """consumer and consumer_factory are alternatives."""

    def test_both_raises(self) -> None:
        with pytest.raises(ValueError, match="not both"):
            MixpanelClient(token="test-token", consumer=RecordingConsumer(), consumer_factory=RecordingConsumer)

    def test_from_env_forwards_factory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")
        consumer = RecordingConsumer()
        client = MixpanelClient.from_env(consumer_factory=lambda: consumer)

        client.track("user-123", "Event")

        assert len(consumer.sent) == 1

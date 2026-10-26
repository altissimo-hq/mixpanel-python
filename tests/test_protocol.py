"""Tests for MixpanelClientProtocol conformance."""

from __future__ import annotations

from mixpanel import BufferedConsumer, Consumer

from altissimo.mixpanel import FakeMixpanelClient, MixpanelClient, MixpanelClientProtocol, MixpanelConsumer

from .conftest import FailingConsumer, FailingFlushConsumer, RecordingConsumer


class TestProtocolConformance:
    """Both MixpanelClient and FakeMixpanelClient should satisfy the protocol."""

    def test_client_satisfies_protocol(self) -> None:
        client = MixpanelClient(token="test-token")
        assert isinstance(client, MixpanelClientProtocol)

    def test_fake_satisfies_protocol(self) -> None:
        fake = FakeMixpanelClient()
        assert isinstance(fake, MixpanelClientProtocol)


class TestConsumerProtocol:
    """The SDK's consumers and the test consumers match MixpanelConsumer."""

    def test_sdk_consumers(self) -> None:
        assert isinstance(Consumer(), MixpanelConsumer)
        assert isinstance(BufferedConsumer(), MixpanelConsumer)

    def test_test_consumers(self) -> None:
        assert isinstance(RecordingConsumer(), MixpanelConsumer)
        assert isinstance(FailingConsumer(), MixpanelConsumer)
        assert isinstance(FailingFlushConsumer(), MixpanelConsumer)

    def test_object_without_send_does_not_match(self) -> None:
        assert not isinstance(object(), MixpanelConsumer)

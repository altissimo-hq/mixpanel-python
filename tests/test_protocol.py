"""Tests for MixpanelClientProtocol conformance."""

from __future__ import annotations

from altissimo.mixpanel import FakeMixpanelClient, MixpanelClient, MixpanelClientProtocol


class TestProtocolConformance:
    """Both MixpanelClient and FakeMixpanelClient should satisfy the protocol."""

    def test_client_satisfies_protocol(self) -> None:
        client = MixpanelClient(token="test-token")
        assert isinstance(client, MixpanelClientProtocol)

    def test_fake_satisfies_protocol(self) -> None:
        fake = FakeMixpanelClient()
        assert isinstance(fake, MixpanelClientProtocol)

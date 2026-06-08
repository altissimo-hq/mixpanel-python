"""Tests for MixpanelClient.from_env() factory."""

from __future__ import annotations

import pytest

from altissimo.mixpanel import MixpanelClient


class TestFromEnv:
    """Tests for the from_env() class method."""

    def test_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")
        client = MixpanelClient.from_env()
        assert client.enabled
        assert client._token == "my-token"

    def test_missing_token_disables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MIXPANEL_TOKEN", raising=False)
        client = MixpanelClient.from_env()
        assert not client.enabled
        assert client._token == "disabled"

    def test_empty_token_disables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "")
        client = MixpanelClient.from_env()
        assert not client.enabled

    def test_custom_token_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_MP_TOKEN", "custom-token")
        client = MixpanelClient.from_env(token_var="MY_MP_TOKEN")
        assert client.enabled
        assert client._token == "custom-token"

    def test_api_secret_is_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")
        monkeypatch.setenv("MIXPANEL_API_SECRET", "my-secret")
        client = MixpanelClient.from_env()
        assert client._api_secret == "my-secret"

    def test_custom_api_secret_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")
        monkeypatch.setenv("MY_SECRET", "custom-secret")
        client = MixpanelClient.from_env(api_secret_var="MY_SECRET")
        assert client._api_secret == "custom-secret"

    @pytest.mark.parametrize("value", ["false", "False", "FALSE", "no", "0", "nope"])
    def test_mixpanel_enabled_false(self, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")
        monkeypatch.setenv("MIXPANEL_ENABLED", value)
        client = MixpanelClient.from_env()
        assert not client.enabled

    @pytest.mark.parametrize("value", ["true", "True", "TRUE", "yes", "1"])
    def test_mixpanel_enabled_true(self, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")
        monkeypatch.setenv("MIXPANEL_ENABLED", value)
        client = MixpanelClient.from_env()
        assert client.enabled

    def test_mixpanel_enabled_not_set_defaults_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")
        monkeypatch.delenv("MIXPANEL_ENABLED", raising=False)
        client = MixpanelClient.from_env()
        assert client.enabled

    def test_explicit_enabled_true_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")
        monkeypatch.setenv("MIXPANEL_ENABLED", "false")
        client = MixpanelClient.from_env(enabled=True)
        assert client.enabled

    def test_explicit_enabled_false_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")
        monkeypatch.setenv("MIXPANEL_ENABLED", "true")
        client = MixpanelClient.from_env(enabled=False)
        assert not client.enabled

    def test_missing_token_overrides_enabled_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing token always forces disabled, even with MIXPANEL_ENABLED=true."""
        monkeypatch.delenv("MIXPANEL_TOKEN", raising=False)
        monkeypatch.setenv("MIXPANEL_ENABLED", "true")
        client = MixpanelClient.from_env()
        assert not client.enabled

    def test_on_error_forwarded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")
        client = MixpanelClient.from_env(on_error="raise")
        assert client._on_error == "raise"

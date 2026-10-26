"""Tests for MixpanelClient.from_env() factory."""

from __future__ import annotations

import logging

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


class TestFromEnvMissingToken:
    """What from_env() does when the token is missing depends on how tracking was turned on."""

    @pytest.mark.parametrize("token", [None, ""])
    def test_explicit_enabled_true_raises(self, monkeypatch: pytest.MonkeyPatch, token: str | None) -> None:
        if token is None:
            monkeypatch.delenv("MIXPANEL_TOKEN", raising=False)
        else:
            monkeypatch.setenv("MIXPANEL_TOKEN", token)

        with pytest.raises(ValueError, match="MIXPANEL_TOKEN is not set"):
            MixpanelClient.from_env(enabled=True)

    def test_explicit_enabled_true_names_custom_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MY_MP_TOKEN", raising=False)

        with pytest.raises(ValueError, match="MY_MP_TOKEN is not set"):
            MixpanelClient.from_env(token_var="MY_MP_TOKEN", enabled=True)

    def test_explicit_enabled_true_raises_even_if_env_says_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MIXPANEL_TOKEN", raising=False)
        monkeypatch.setenv("MIXPANEL_ENABLED", "false")

        with pytest.raises(ValueError, match="MIXPANEL_TOKEN"):
            MixpanelClient.from_env(enabled=True)

    def test_default_warns_once(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        monkeypatch.delenv("MIXPANEL_TOKEN", raising=False)
        monkeypatch.delenv("MIXPANEL_ENABLED", raising=False)

        with caplog.at_level(logging.WARNING, logger="altissimo.mixpanel.client"):
            client = MixpanelClient.from_env()

        assert not client.enabled
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert warnings[0].getMessage() == "Mixpanel tracking disabled: MIXPANEL_TOKEN is not set"

    def test_env_enabled_true_warns(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        monkeypatch.delenv("MIXPANEL_TOKEN", raising=False)
        monkeypatch.setenv("MIXPANEL_ENABLED", "true")

        with caplog.at_level(logging.WARNING, logger="altissimo.mixpanel.client"):
            client = MixpanelClient.from_env()

        assert not client.enabled
        assert "MIXPANEL_TOKEN is not set" in caplog.text

    def test_explicit_enabled_false_is_quiet(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        monkeypatch.delenv("MIXPANEL_TOKEN", raising=False)

        with caplog.at_level(logging.WARNING, logger="altissimo.mixpanel.client"):
            client = MixpanelClient.from_env(enabled=False)

        assert not client.enabled
        assert caplog.records == []

    def test_env_enabled_false_is_quiet(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        monkeypatch.delenv("MIXPANEL_TOKEN", raising=False)
        monkeypatch.setenv("MIXPANEL_ENABLED", "false")

        with caplog.at_level(logging.WARNING, logger="altissimo.mixpanel.client"):
            client = MixpanelClient.from_env()

        assert not client.enabled
        assert caplog.records == []

    def test_token_set_is_quiet(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        monkeypatch.setenv("MIXPANEL_TOKEN", "my-token")

        with caplog.at_level(logging.WARNING, logger="altissimo.mixpanel.client"):
            client = MixpanelClient.from_env(enabled=True)

        assert client.enabled
        assert caplog.records == []

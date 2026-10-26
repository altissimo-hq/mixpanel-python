"""Tests for disabled mode."""

from __future__ import annotations

from altissimo.mixpanel import MixpanelClient


class TestDisabledMode:
    """All operations should silently no-op when disabled."""

    def test_enabled_property_returns_false(self, disabled_client: MixpanelClient) -> None:
        assert not disabled_client.enabled

    def test_track_noop(self, disabled_client: MixpanelClient) -> None:
        disabled_client.track("user-123", "Page Viewed", properties={"page": "/"})

    def test_people_set_noop(self, disabled_client: MixpanelClient) -> None:
        disabled_client.people_set("user-123", {"$name": "Jane"})

    def test_people_set_once_noop(self, disabled_client: MixpanelClient) -> None:
        disabled_client.people_set_once("user-123", {"$created": "2024-01-01"})

    def test_people_increment_noop(self, disabled_client: MixpanelClient) -> None:
        disabled_client.people_increment("user-123", {"count": 1})

    def test_people_union_noop(self, disabled_client: MixpanelClient) -> None:
        disabled_client.people_union("user-123", {"tags": ["vip"]})

    def test_people_unset_noop(self, disabled_client: MixpanelClient) -> None:
        disabled_client.people_unset("user-123", ["old_prop"])

    def test_alias_noop(self, disabled_client: MixpanelClient) -> None:
        disabled_client.alias("new-id", "original-id")

    def test_mp_stays_none(self, disabled_client: MixpanelClient) -> None:
        """The SDK is never initialized when disabled."""
        disabled_client.track("user-123", "Event")
        disabled_client.people_set("user-123", {"key": "val"})
        disabled_client.alias("a", "b")
        assert getattr(disabled_client._local, "mp", None) is None

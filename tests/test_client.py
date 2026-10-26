"""Tests for MixpanelClient core operations."""

from __future__ import annotations

from unittest.mock import patch

from altissimo.mixpanel import MixpanelClient

from .conftest import RecordingConsumer


class TestTrack:
    """Tests for the track() method."""

    def test_track_sends_event(self, client: MixpanelClient, recording_consumer: RecordingConsumer) -> None:
        client.track("user-123", "Page Viewed")

        assert len(recording_consumer.sent) == 1
        endpoint, data = recording_consumer.sent[0]
        assert endpoint == "events"
        assert data["event"] == "Page Viewed"
        assert data["properties"]["distinct_id"] == "user-123"

    def test_track_with_properties(self, client: MixpanelClient, recording_consumer: RecordingConsumer) -> None:
        client.track("user-123", "Button Clicked", properties={"button": "signup"})

        assert len(recording_consumer.sent) == 1
        _, data = recording_consumer.sent[0]
        assert data["properties"]["button"] == "signup"

    def test_track_with_meta(self, client: MixpanelClient, recording_consumer: RecordingConsumer) -> None:
        client.track("user-123", "Page Viewed", meta={"$ip": "1.2.3.4"})

        assert len(recording_consumer.sent) == 1
        _, data = recording_consumer.sent[0]
        # Meta properties are at the top level of the JSON, not inside 'properties'
        assert data["$ip"] == "1.2.3.4"

    def test_track_default_properties_empty_dict(
        self, client: MixpanelClient, recording_consumer: RecordingConsumer
    ) -> None:
        """Properties default to empty dict when not provided."""
        client.track("user-123", "Page Viewed")
        assert len(recording_consumer.sent) == 1


class TestPeopleSet:
    """Tests for people_set()."""

    def test_people_set(self, client: MixpanelClient, recording_consumer: RecordingConsumer) -> None:
        client.people_set("user-123", {"$name": "Jane Doe"})

        assert len(recording_consumer.sent) == 1
        endpoint, data = recording_consumer.sent[0]
        assert endpoint == "people"
        assert data["$distinct_id"] == "user-123"
        assert data["$set"]["$name"] == "Jane Doe"


class TestPeopleSetOnce:
    """Tests for people_set_once()."""

    def test_people_set_once(self, client: MixpanelClient, recording_consumer: RecordingConsumer) -> None:
        client.people_set_once("user-123", {"$created": "2024-01-01"})

        assert len(recording_consumer.sent) == 1
        endpoint, data = recording_consumer.sent[0]
        assert endpoint == "people"
        assert data["$distinct_id"] == "user-123"
        assert data["$set_once"]["$created"] == "2024-01-01"


class TestPeopleIncrement:
    """Tests for people_increment()."""

    def test_people_increment(self, client: MixpanelClient, recording_consumer: RecordingConsumer) -> None:
        client.people_increment("user-123", {"login_count": 1})

        assert len(recording_consumer.sent) == 1
        endpoint, data = recording_consumer.sent[0]
        assert endpoint == "people"
        assert data["$distinct_id"] == "user-123"
        assert data["$add"]["login_count"] == 1


class TestPeopleUnion:
    """Tests for people_union()."""

    def test_people_union(self, client: MixpanelClient, recording_consumer: RecordingConsumer) -> None:
        client.people_union("user-123", {"tags": ["vip"]})

        assert len(recording_consumer.sent) == 1
        endpoint, data = recording_consumer.sent[0]
        assert endpoint == "people"
        assert data["$distinct_id"] == "user-123"
        assert data["$union"]["tags"] == ["vip"]


class TestPeopleUnset:
    """Tests for people_unset()."""

    def test_people_unset(self, client: MixpanelClient, recording_consumer: RecordingConsumer) -> None:
        client.people_unset("user-123", ["old_prop"])

        assert len(recording_consumer.sent) == 1
        endpoint, data = recording_consumer.sent[0]
        assert endpoint == "people"
        assert data["$distinct_id"] == "user-123"
        assert "old_prop" in data["$unset"]


class TestAlias:
    """Tests for alias().

    Note: The Mixpanel SDK's alias() method always uses its own synchronous
    Consumer, bypassing any custom consumer. We mock the sync consumer to
    verify the call is forwarded correctly.
    """

    def test_alias(self, client: MixpanelClient) -> None:
        with patch("mixpanel.Consumer.send") as mock_send:
            client.alias("new-id", "original-id")

        mock_send.assert_called_once()
        endpoint = mock_send.call_args[0][0]
        assert endpoint == "events"


class TestLazyInit:
    """Tests for lazy SDK initialization."""

    def test_mp_is_none_initially(self) -> None:
        client = MixpanelClient(token="test-token")
        assert getattr(client._local, "mp", None) is None

    def test_mp_is_cached(self, client: MixpanelClient) -> None:
        """The Mixpanel instance is created once per thread and reused."""
        client.track("user-123", "Event 1")
        mp_first = client._local.mp
        client.track("user-123", "Event 2")
        mp_second = client._local.mp
        assert mp_first is mp_second

    def test_custom_consumer_is_used(self, recording_consumer: RecordingConsumer) -> None:
        client = MixpanelClient(token="test-token", consumer=recording_consumer)
        client.track("user-123", "Test Event")
        assert len(recording_consumer.sent) == 1

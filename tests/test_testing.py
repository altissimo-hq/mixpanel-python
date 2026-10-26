"""Tests for FakeMixpanelClient test helper."""

from __future__ import annotations

from altissimo.mixpanel import FakeMixpanelClient


class TestFakeMixpanelClient:
    """Test the in-memory fake client records calls correctly."""

    def test_all_lists_start_empty(self) -> None:
        fake = FakeMixpanelClient()
        assert fake.tracked == []
        assert fake.people_updates == []
        assert fake.people_set_onces == []
        assert fake.people_increments == []
        assert fake.people_unions == []
        assert fake.people_unsets == []
        assert fake.aliases == []
        assert fake.flush_count == 0

    def test_flush_records(self) -> None:
        fake = FakeMixpanelClient()
        fake.flush()
        fake.flush()
        assert fake.flush_count == 2

    def test_track_records(self) -> None:
        fake = FakeMixpanelClient()
        fake.track("user-1", "Event A", properties={"key": "val"})
        assert len(fake.tracked) == 1
        assert fake.tracked[0] == ("user-1", "Event A", {"key": "val"}, None)

    def test_track_without_properties(self) -> None:
        fake = FakeMixpanelClient()
        fake.track("user-1", "Event A")
        assert fake.tracked[0] == ("user-1", "Event A", {}, None)

    def test_track_with_meta(self) -> None:
        fake = FakeMixpanelClient()
        fake.track("user-1", "Event A", meta={"$ip": "1.2.3.4"})
        assert fake.tracked[0] == ("user-1", "Event A", {}, {"$ip": "1.2.3.4"})

    def test_people_set_records(self) -> None:
        fake = FakeMixpanelClient()
        fake.people_set("user-1", {"$name": "Jane"})
        assert fake.people_updates == [("user-1", {"$name": "Jane"}, None)]

    def test_people_set_once_records(self) -> None:
        fake = FakeMixpanelClient()
        fake.people_set_once("user-1", {"$created": "2024-01-01"})
        assert fake.people_set_onces == [("user-1", {"$created": "2024-01-01"}, None)]

    def test_people_increment_records(self) -> None:
        fake = FakeMixpanelClient()
        fake.people_increment("user-1", {"login_count": 1})
        assert fake.people_increments == [("user-1", {"login_count": 1}, None)]

    def test_people_union_records(self) -> None:
        fake = FakeMixpanelClient()
        fake.people_union("user-1", {"tags": ["vip"]})
        assert fake.people_unions == [("user-1", {"tags": ["vip"]}, None)]

    def test_people_unset_records(self) -> None:
        fake = FakeMixpanelClient()
        fake.people_unset("user-1", ["old_prop"])
        assert fake.people_unsets == [("user-1", ["old_prop"], None)]

    def test_alias_records(self) -> None:
        fake = FakeMixpanelClient()
        fake.alias("new-id", "original-id")
        assert fake.aliases == [("new-id", "original-id", None)]

    def test_multiple_calls_accumulate(self) -> None:
        fake = FakeMixpanelClient()
        fake.track("u1", "E1")
        fake.track("u2", "E2")
        fake.people_set("u1", {"a": 1})
        assert len(fake.tracked) == 2
        assert len(fake.people_updates) == 1

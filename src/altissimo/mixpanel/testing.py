"""Test helpers for downstream projects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeMixpanelClient:
    """In-memory fake that records all calls.

    Satisfies :class:`~altissimo.mixpanel.protocol.MixpanelClientProtocol`
    structurally, so it can be used as a drop-in replacement in tests.

    Example::

        fake = FakeMixpanelClient()
        my_service = MyService(mixpanel=fake)
        my_service.do_something()

        assert len(fake.tracked) == 1
        assert fake.tracked[0][1] == "Order Created"
    """

    tracked: list[tuple[str, str, dict[str, Any], dict[str, Any] | None]] = field(default_factory=list)
    people_updates: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = field(default_factory=list)
    people_set_onces: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = field(default_factory=list)
    people_increments: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = field(default_factory=list)
    people_unions: list[tuple[str, dict[str, Any], dict[str, Any] | None]] = field(default_factory=list)
    people_unsets: list[tuple[str, list[str], dict[str, Any] | None]] = field(default_factory=list)
    aliases: list[tuple[str, str, dict[str, Any] | None]] = field(default_factory=list)

    def track(
        self,
        distinct_id: str,
        event_name: str,
        *,
        properties: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Record a tracked event."""
        self.tracked.append((distinct_id, event_name, properties or {}, meta))

    def people_set(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Record a people_set call."""
        self.people_updates.append((distinct_id, properties, meta))

    def people_set_once(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Record a people_set_once call."""
        self.people_set_onces.append((distinct_id, properties, meta))

    def people_increment(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Record a people_increment call."""
        self.people_increments.append((distinct_id, properties, meta))

    def people_union(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Record a people_union call."""
        self.people_unions.append((distinct_id, properties, meta))

    def people_unset(
        self,
        distinct_id: str,
        property_names: list[str],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Record a people_unset call."""
        self.people_unsets.append((distinct_id, property_names, meta))

    def alias(
        self,
        alias_id: str,
        original_id: str,
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Record an alias call."""
        self.aliases.append((alias_id, original_id, meta))

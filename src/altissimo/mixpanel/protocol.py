"""Protocol for Mixpanel client dependency injection."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MixpanelClientProtocol(Protocol):
    """Protocol for Mixpanel client implementations.

    Use this protocol for dependency injection in downstream projects,
    allowing easy substitution of the real client with test fakes.
    """

    def track(
        self,
        distinct_id: str,
        event_name: str,
        *,
        properties: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None: ...

    def people_set(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None: ...

    def people_set_once(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None: ...

    def people_increment(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None: ...

    def people_union(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None: ...

    def people_unset(
        self,
        distinct_id: str,
        property_names: list[str],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None: ...

    def alias(
        self,
        alias_id: str,
        original_id: str,
        *,
        meta: dict[str, Any] | None = None,
    ) -> None: ...

    def flush(self) -> None: ...

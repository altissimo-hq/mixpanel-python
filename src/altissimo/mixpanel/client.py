"""Mixpanel analytics client with typed wrappers for common operations."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Literal

from altissimo.mixpanel.exceptions import MixpanelImportError

if TYPE_CHECKING:
    from types import TracebackType

    from mixpanel import Mixpanel

logger = logging.getLogger(__name__)

__all__ = ["MixpanelClient"]


class MixpanelClient:
    """Thin, typed wrapper around the Mixpanel SDK.

    Provides typed methods for all common Mixpanel operations: event tracking,
    user profile management, and identity aliasing.

    The underlying ``Mixpanel`` instance is lazily initialized on the first
    API call, so constructing a ``MixpanelClient`` is side-effect-free.

    When ``enabled=False``, all tracking calls silently no-op without making
    any network requests or importing the SDK.

    Args:
        token: Mixpanel project token.
        api_secret: Optional API secret for import endpoints.
        enabled: When ``False``, all calls silently no-op.
        consumer: Optional custom consumer for the Mixpanel SDK. Supports
            ``BufferedConsumer`` or any object with a ``send`` method. A
            consumer that buffers must be flushed with :meth:`flush` (or by
            using the client as a context manager) before the process exits,
            or the buffered messages are lost.
        on_error: Error handling strategy:
            - ``"log"`` (default): Catch exceptions and log them.
            - ``"raise"``: Re-raise exceptions to the caller.
            - ``"ignore"``: Silently swallow all exceptions.
    """

    def __init__(
        self,
        token: str,
        *,
        api_secret: str | None = None,
        enabled: bool = True,
        consumer: object | None = None,
        on_error: Literal["log", "raise", "ignore"] = "log",
    ) -> None:
        self._token = token
        self._api_secret = api_secret
        self._enabled = enabled
        self._consumer = consumer
        self._on_error = on_error
        self._mp: Mixpanel | None = None

    @classmethod
    def from_env(
        cls,
        *,
        token_var: str = "MIXPANEL_TOKEN",  # noqa: S107
        api_secret_var: str = "MIXPANEL_API_SECRET",  # noqa: S107
        enabled: bool | None = None,
        on_error: Literal["log", "raise", "ignore"] = "log",
    ) -> MixpanelClient:
        """Create a client using environment variables.

        What happens when the token environment variable is missing or empty
        depends on how tracking was turned on:

        - ``enabled=True`` passed explicitly: raises ``ValueError``. The caller
          said this process must send events, so a missing secret should fail
          at startup rather than look like Mixpanel going quiet.
        - ``enabled`` left as ``None``: the client is disabled and a warning
          naming the variable is logged. Analytics should never be a hard
          dependency by default.
        - ``enabled=False``, or ``MIXPANEL_ENABLED`` falsey: the client is
          disabled with no warning, as tracking was turned off deliberately.

        Args:
            token_var: Name of the environment variable containing the
                Mixpanel project token.
            api_secret_var: Name of the environment variable containing
                the API secret.
            enabled: Override the enabled state.  If ``None`` (default),
                reads from the ``MIXPANEL_ENABLED`` environment variable
                (truthy values: ``1``, ``true``, ``yes``; defaults to
                ``True`` when the variable is not set).
            on_error: Error handling strategy (see class docstring).

        Returns:
            A configured ``MixpanelClient`` instance.

        Raises:
            ValueError: If ``enabled=True`` was passed and the token
                environment variable is missing or empty.
        """
        token = os.environ.get(token_var, "")
        api_secret = os.environ.get(api_secret_var)

        if not token and enabled is True:
            raise ValueError(f"{token_var} is not set, but enabled=True requires a Mixpanel token")

        if enabled is None:
            env_enabled = os.environ.get("MIXPANEL_ENABLED")
            enabled = env_enabled.lower() in ("1", "true", "yes") if env_enabled is not None else True

        # Missing token → disabled mode, said once unless tracking was off anyway
        if not token:
            if enabled:
                logger.warning("Mixpanel tracking disabled: %s is not set", token_var)
            enabled = False

        return cls(
            token=token or "disabled",
            api_secret=api_secret,
            enabled=enabled,
            on_error=on_error,
        )

    @property
    def enabled(self) -> bool:
        """Whether tracking is currently enabled."""
        return self._enabled

    def _get_mp(self) -> Mixpanel:
        """Return the lazily-initialized ``Mixpanel`` instance.

        Raises:
            MixpanelImportError: If the ``mixpanel`` package is not installed.
        """
        if self._mp is None:
            try:
                from mixpanel import Mixpanel as _Mixpanel
            except ImportError:
                raise MixpanelImportError from None

            kwargs: dict[str, Any] = {}
            if self._consumer is not None:
                kwargs["consumer"] = self._consumer

            self._mp = _Mixpanel(self._token, **kwargs)
        return self._mp

    def _handle_error(self, exc: Exception, operation: str, **context: Any) -> None:
        """Handle an exception according to the configured error strategy."""
        if self._on_error == "raise":
            raise
        if self._on_error == "log":
            logger.exception("Mixpanel %s error", operation, extra=context)

    # ------------------------------------------------------------------
    # Event tracking
    # ------------------------------------------------------------------

    def track(
        self,
        distinct_id: str,
        event_name: str,
        *,
        properties: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Track an event.

        Args:
            distinct_id: Unique identifier for the user.
            event_name: Name of the event to track.
            properties: Optional event properties.
            meta: Optional request-level metadata (e.g., ``$ip``,
                ``$ignore_time``).
        """
        if not self._enabled:
            return
        try:
            self._get_mp().track(distinct_id, event_name, properties or {}, meta)
        except Exception as exc:
            self._handle_error(exc, "track", event_name=event_name)

    # ------------------------------------------------------------------
    # People operations
    # ------------------------------------------------------------------

    def people_set(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Set user profile properties (overwrites existing values).

        Args:
            distinct_id: Unique identifier for the user.
            properties: Properties to set on the user profile.
            meta: Optional request-level metadata.
        """
        if not self._enabled:
            return
        try:
            self._get_mp().people_set(distinct_id, properties, meta)
        except Exception as exc:
            self._handle_error(exc, "people_set")

    def people_set_once(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Set properties only if they are not already set.

        Args:
            distinct_id: Unique identifier for the user.
            properties: Properties to set (only if not already present).
            meta: Optional request-level metadata.
        """
        if not self._enabled:
            return
        try:
            self._get_mp().people_set_once(distinct_id, properties, meta)
        except Exception as exc:
            self._handle_error(exc, "people_set_once")

    def people_increment(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Increment numeric user profile properties.

        Args:
            distinct_id: Unique identifier for the user.
            properties: Properties to increment (values are the amounts).
            meta: Optional request-level metadata.
        """
        if not self._enabled:
            return
        try:
            self._get_mp().people_increment(distinct_id, properties, meta)
        except Exception as exc:
            self._handle_error(exc, "people_increment")

    def people_union(
        self,
        distinct_id: str,
        properties: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Append to list properties on a user profile.

        Args:
            distinct_id: Unique identifier for the user.
            properties: Properties whose values (lists) will be unioned.
            meta: Optional request-level metadata.
        """
        if not self._enabled:
            return
        try:
            self._get_mp().people_union(distinct_id, properties, meta)
        except Exception as exc:
            self._handle_error(exc, "people_union")

    def people_unset(
        self,
        distinct_id: str,
        property_names: list[str],
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Remove properties from a user profile.

        Args:
            distinct_id: Unique identifier for the user.
            property_names: Names of properties to remove.
            meta: Optional request-level metadata.
        """
        if not self._enabled:
            return
        try:
            self._get_mp().people_unset(distinct_id, property_names, meta)
        except Exception as exc:
            self._handle_error(exc, "people_unset")

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    def alias(
        self,
        alias_id: str,
        original_id: str,
        *,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Create an identity alias.

        Args:
            alias_id: The new alias ID.
            original_id: The original distinct ID.
            meta: Optional request-level metadata.
        """
        if not self._enabled:
            return
        try:
            self._get_mp().alias(alias_id, original_id, meta)
        except Exception as exc:
            self._handle_error(exc, "alias")

    # ------------------------------------------------------------------
    # Delivery
    # ------------------------------------------------------------------

    def flush(self) -> None:
        """Send any messages the consumer is still holding.

        Only a buffering consumer such as ``BufferedConsumer`` holds messages;
        it sends them when its buffer fills, so whatever is buffered when the
        process exits is lost unless flushed. With the default consumer, which
        sends each message as it is made, this does nothing.
        """
        if not self._enabled:
            return
        flush = getattr(self._consumer, "flush", None)
        if flush is None:
            return
        try:
            flush()
        except Exception as exc:
            self._handle_error(exc, "flush")

    def __enter__(self) -> MixpanelClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Flush on leaving the ``with`` block, including when it raised."""
        self.flush()

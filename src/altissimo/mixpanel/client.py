"""Mixpanel analytics client with typed wrappers for common operations."""

from __future__ import annotations

import logging
import os
import threading
import weakref
from typing import TYPE_CHECKING, Any, Literal

from altissimo.mixpanel.exceptions import MixpanelImportError

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType

    from altissimo.mixpanel.protocol import MixpanelConsumer
    from mixpanel import Mixpanel

logger = logging.getLogger(__name__)

__all__ = ["MixpanelClient"]


class MixpanelClient:
    """Thin, typed wrapper around the Mixpanel SDK.

    Provides typed methods for all common Mixpanel operations: event tracking,
    user profile management, and identity aliasing.

    The underlying ``Mixpanel`` instance is lazily initialized on the first
    API call, so constructing a ``MixpanelClient`` is side-effect-free.

    One client can be shared across threads: each thread gets its own
    ``Mixpanel`` instance, and so its own consumer and HTTP session, since
    neither the SDK's ``Consumer`` (one ``requests.Session``) nor its
    ``BufferedConsumer`` (unlocked buffers) is safe to share.

    When ``enabled=False``, all tracking calls silently no-op without making
    any network requests or importing the SDK.

    Args:
        token: Mixpanel project token.
        enabled: When ``False``, all calls silently no-op.
        consumer: Optional custom consumer for the Mixpanel SDK, such as
            ``BufferedConsumer`` or anything matching
            :class:`~altissimo.mixpanel.protocol.MixpanelConsumer`. This one
            object is shared by every thread, so it must be thread-safe if
            the client is used from more than one; otherwise pass
            ``consumer_factory``.
        consumer_factory: Optional callable returning a new consumer, called
            once per thread that uses the client. Use it instead of
            ``consumer`` in threaded apps, e.g.
            ``consumer_factory=lambda: Consumer(request_timeout=5)``.

            When a thread that used the client exits, its consumer is
            flushed and released, so short-lived threads, such as an idle
            worker a thread pool retires, don't leave buffered messages
            behind. A consumer that buffers must still be flushed with
            :meth:`flush` (or by using the client as a context manager)
            before the process exits, or the buffered messages of threads
            still running are lost.
        on_error: Error handling strategy:
            - ``"log"`` (default): Catch exceptions and log them.
            - ``"raise"``: Re-raise exceptions to the caller.
            - ``"ignore"``: Silently swallow all exceptions.

            A missing ``mixpanel`` SDK is a setup error rather than a failed
            call: with ``"raise"`` it is raised, otherwise it is logged once
            (not with ``"ignore"``) and the client disables itself.
    """

    def __init__(
        self,
        token: str,
        *,
        enabled: bool = True,
        consumer: MixpanelConsumer | None = None,
        consumer_factory: Callable[[], MixpanelConsumer] | None = None,
        on_error: Literal["log", "raise", "ignore"] = "log",
    ) -> None:
        if consumer is not None and consumer_factory is not None:
            raise ValueError("Pass consumer or consumer_factory, not both")
        self._token = token
        self._enabled = enabled
        self._consumer = consumer
        self._consumer_factory = consumer_factory
        self._on_error = on_error
        # One Mixpanel instance per thread (see class docstring)
        self._local = threading.local()
        # The consumer consumer_factory made for each thread still using the
        # client, with its thread, so flush() reaches all threads' consumers
        self._factory_consumers: list[tuple[threading.Thread, MixpanelConsumer]] = []
        self._factory_consumers_lock = threading.Lock()

    @classmethod
    def from_env(
        cls,
        *,
        token_var: str = "MIXPANEL_TOKEN",  # noqa: S107
        enabled: bool | None = None,
        consumer: MixpanelConsumer | None = None,
        consumer_factory: Callable[[], MixpanelConsumer] | None = None,
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
            enabled: Override the enabled state.  If ``None`` (default),
                reads from the ``MIXPANEL_ENABLED`` environment variable
                (truthy values: ``1``, ``true``, ``yes``; defaults to
                ``True`` when the variable is not set).
            consumer: Optional custom consumer (see class docstring).
            consumer_factory: Optional per-thread consumer factory (see
                class docstring).
            on_error: Error handling strategy (see class docstring).

        Returns:
            A configured ``MixpanelClient`` instance.

        Raises:
            ValueError: If ``enabled=True`` was passed and the token
                environment variable is missing or empty.
        """
        token = os.environ.get(token_var, "")

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
            enabled=enabled,
            consumer=consumer,
            consumer_factory=consumer_factory,
            on_error=on_error,
        )

    @property
    def enabled(self) -> bool:
        """Whether tracking is currently enabled."""
        return self._enabled

    def _get_mp(self) -> Mixpanel:
        """Return this thread's ``Mixpanel`` instance, creating it on first use.

        Raises:
            MixpanelImportError: If the ``mixpanel`` package is not installed.
        """
        mp: Mixpanel | None = getattr(self._local, "mp", None)
        if mp is None:
            try:
                from mixpanel import Mixpanel as _Mixpanel
            except ImportError:
                raise MixpanelImportError from None

            kwargs: dict[str, Any] = {}
            entry: tuple[threading.Thread, MixpanelConsumer] | None = None
            if self._consumer_factory is not None:
                consumer = self._consumer_factory()
                entry = (threading.current_thread(), consumer)
                with self._factory_consumers_lock:
                    self._factory_consumers.append(entry)
                kwargs["consumer"] = consumer
            elif self._consumer is not None:
                kwargs["consumer"] = self._consumer

            mp = _Mixpanel(self._token, **kwargs)
            self._local.mp = mp
            if entry is not None:
                # The thread's Mixpanel instance is released when the thread
                # exits; flush and release its consumer then. A weak reference
                # to the client, so a live thread doesn't keep the client alive.
                finalizer = weakref.finalize(mp, MixpanelClient._retire_consumer, weakref.ref(self), entry)
                finalizer.atexit = False
        return mp

    @staticmethod
    def _retire_consumer(
        client_ref: weakref.ref[MixpanelClient],
        entry: tuple[threading.Thread, MixpanelConsumer],
    ) -> None:
        """Flush and release the consumer of a thread that has exited.

        No caller is left to raise to, so a flush error is logged (not with
        ``on_error="ignore"``) instead of raised.
        """
        client = client_ref()
        if client is None:
            return
        with client._factory_consumers_lock:
            if not any(e is entry for e in client._factory_consumers):
                return  # flush() already released it
            client._factory_consumers = [e for e in client._factory_consumers if e is not entry]
        if not client._enabled:
            return
        try:
            client._flush_consumer(entry[1])
        except Exception:
            if client._on_error != "ignore":
                logger.exception("Mixpanel flush error for exited thread %s", entry[0].name)

    @staticmethod
    def _flush_consumer(consumer: MixpanelConsumer) -> None:
        flush = getattr(consumer, "flush", None)
        if flush is not None:
            flush()

    def _handle_error(self, exc: Exception, operation: str, **context: Any) -> None:
        """Handle an exception according to the configured error strategy."""
        if self._on_error == "raise":
            raise exc
        if isinstance(exc, MixpanelImportError):
            # A setup error, not a failed call: say so once and stop trying,
            # rather than logging a traceback for every event.
            self._enabled = False
            if self._on_error == "log":
                logger.error("Mixpanel tracking disabled: %s", exc)
            return
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
        """Send any messages the consumers are still holding.

        Only a buffering consumer such as ``BufferedConsumer`` holds messages;
        it sends them when its buffer fills, so whatever is buffered when the
        process exits is lost unless flushed. With the default consumer, which
        sends each message as it is made, this does nothing.

        With ``consumer_factory`` this flushes the consumer of every thread
        that has used the client, so call it when no other thread is tracking,
        such as at shutdown: a buffering consumer isn't safe to flush while
        its own thread is adding to it. It also releases the consumers of
        threads that have exited, if any are still held.
        """
        if not self._enabled:
            return
        if self._consumer_factory is not None:
            with self._factory_consumers_lock:
                entries = self._factory_consumers
                # Flush exited threads' consumers one last time, then release them
                self._factory_consumers = [e for e in entries if e[0].is_alive()]
            consumers = [consumer for _, consumer in entries]
        else:
            consumers = [self._consumer] if self._consumer is not None else []
        for consumer in consumers:
            try:
                self._flush_consumer(consumer)
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
        """Flush on leaving the ``with`` block, including when it raised.

        If the block raised, a flush error is logged rather than raised, so
        it doesn't replace the block's own exception.
        """
        if exc is None:
            self.flush()
            return
        try:
            self.flush()
        except Exception:
            logger.exception("Mixpanel flush error while leaving a with block that raised")

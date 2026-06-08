"""Exceptions for altissimo-mixpanel."""

from __future__ import annotations


class MixpanelError(Exception):
    """Base exception for all altissimo-mixpanel errors."""


class MixpanelImportError(MixpanelError, ImportError):
    """Raised when the ``mixpanel`` SDK is not installed.

    Install with::

        pip install altissimo-mixpanel[mixpanel]
    """

    def __init__(self) -> None:
        super().__init__(
            "The 'mixpanel' package is required but not installed. "
            "Install it with: pip install altissimo-mixpanel[mixpanel]"
        )

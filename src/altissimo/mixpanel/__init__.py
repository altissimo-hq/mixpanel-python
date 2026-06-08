"""Altissimo Mixpanel — reusable Mixpanel analytics client."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .client import MixpanelClient
from .exceptions import MixpanelError, MixpanelImportError
from .protocol import MixpanelClientProtocol
from .testing import FakeMixpanelClient

try:
    __version__ = version("altissimo-mixpanel")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = [
    "FakeMixpanelClient",
    "MixpanelClient",
    "MixpanelClientProtocol",
    "MixpanelError",
    "MixpanelImportError",
    "__version__",
]

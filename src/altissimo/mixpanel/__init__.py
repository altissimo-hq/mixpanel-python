"""Altissimo Mixpanel — reusable Mixpanel analytics client."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .client import MixpanelClient
from .exceptions import MixpanelError, MixpanelImportError
from .protocol import MixpanelClientProtocol, MixpanelConsumer
from .testing import FakeMixpanelClient

try:
    __version__ = version("altissimo-mixpanel")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "FakeMixpanelClient",
    "MixpanelClient",
    "MixpanelClientProtocol",
    "MixpanelConsumer",
    "MixpanelError",
    "MixpanelImportError",
    "__version__",
]

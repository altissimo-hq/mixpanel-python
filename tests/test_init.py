"""Tests for the public API surface."""

from __future__ import annotations

import altissimo.mixpanel as mp


class TestPublicAPI:
    """Test the package's public interface."""

    def test_version_is_string(self) -> None:
        assert isinstance(mp.__version__, str)

    def test_all_contains_expected_names(self) -> None:
        expected = {
            "FakeMixpanelClient",
            "MixpanelClient",
            "MixpanelClientProtocol",
            "MixpanelConsumer",
            "MixpanelError",
            "MixpanelImportError",
            "__version__",
        }
        assert set(mp.__all__) == expected

    def test_imports(self) -> None:
        """All public names are importable from the top-level package."""
        from altissimo.mixpanel import (
            FakeMixpanelClient,
            MixpanelClient,
            MixpanelClientProtocol,
            MixpanelConsumer,
            MixpanelError,
            MixpanelImportError,
        )

        assert FakeMixpanelClient is not None
        assert MixpanelClient is not None
        assert MixpanelClientProtocol is not None
        assert MixpanelConsumer is not None
        assert MixpanelError is not None
        assert MixpanelImportError is not None

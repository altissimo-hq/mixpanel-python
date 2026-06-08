"""Tests for exception hierarchy."""

from __future__ import annotations

from altissimo.mixpanel import MixpanelError, MixpanelImportError


class TestExceptionHierarchy:
    """Test the exception class hierarchy."""

    def test_mixpanel_error_is_exception(self) -> None:
        assert issubclass(MixpanelError, Exception)

    def test_import_error_is_mixpanel_error(self) -> None:
        assert issubclass(MixpanelImportError, MixpanelError)

    def test_import_error_is_import_error(self) -> None:
        assert issubclass(MixpanelImportError, ImportError)

    def test_import_error_message(self) -> None:
        exc = MixpanelImportError()
        assert "mixpanel" in str(exc)
        assert "pip install" in str(exc)

    def test_import_error_catchable_as_import_error(self) -> None:
        with __import__("pytest").raises(ImportError):
            raise MixpanelImportError

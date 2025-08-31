"""Tests for the D-Bus clipboard handler."""

import pytest

from normcap.clipboard.handlers import dbus


class TestDBusClipboardHandler:
    """Test the D-Bus clipboard handler."""

    def test_implements_protocol(self):
        """Test that the handler implements the required protocol."""
        # Test required attributes
        assert hasattr(dbus, "install_instructions")
        assert isinstance(dbus.install_instructions, str)

        # Test required methods
        assert hasattr(dbus, "copy")
        assert hasattr(dbus, "is_compatible")
        assert hasattr(dbus, "is_installed")
        assert callable(dbus.copy)
        assert callable(dbus.is_compatible)
        assert callable(dbus.is_installed)

    def test_is_compatible_requires_flatpak(self, monkeypatch):
        """Test that is_compatible returns True only for flatpak applications."""
        # Mock flatpak detection to return False
        monkeypatch.setattr(
            "normcap.clipboard.system_info.is_flatpak_package", lambda: False
        )
        assert dbus.is_compatible() is False

        # Mock flatpak detection to return True
        monkeypatch.setattr(
            "normcap.clipboard.system_info.is_flatpak_package", lambda: True
        )
        assert dbus.is_compatible() is True

    def test_is_installed_checks_dbus_interfaces(self, monkeypatch):
        """Test that is_installed checks for required D-Bus interfaces."""

        # Mock successful introspection with required interfaces
        def mock_introspect():
            return [
                "org.freedesktop.portal.Clipboard and "
                "org.freedesktop.portal.RemoteDesktop"
            ]

        class MockProxy:
            def introspect(self):
                return mock_introspect()

        def mock_open_connection():
            class MockConnection:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return MockConnection()

        def mock_proxy_constructor(generator, connection):
            return MockProxy()

        monkeypatch.setattr(
            "normcap.clipboard.handlers.dbus.open_dbus_connection", mock_open_connection
        )
        monkeypatch.setattr(
            "normcap.clipboard.handlers.dbus.Proxy", mock_proxy_constructor
        )

        result = dbus.is_installed()
        assert result is True

    def test_copy_requires_session(self, monkeypatch):
        """Test that copy method requires a valid session."""
        # Mock session creation to fail
        monkeypatch.setattr(
            "normcap.clipboard.handlers.dbus._get_or_create_session", lambda: None
        )

        with pytest.raises(
            RuntimeError, match="Could not create or access clipboard session"
        ):
            dbus.copy("test text")

    def test_install_instructions_empty(self):
        """Test that install instructions are empty (no additional deps needed)."""
        assert dbus.install_instructions == ""

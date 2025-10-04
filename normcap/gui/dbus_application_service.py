"""DBus activation service for NormCap.

This module provides DBus service activation functionality, allowing external
applications to activate NormCap via DBus calls with optional parameters.
"""

import logging

from PySide6 import QtCore, QtDBus

from normcap import app_id

logger = logging.getLogger(__name__)

SERVICE_NAME = app_id
OBJECT_PATH = f"/{app_id.replace('.', '/')}"
INTERFACE_NAME = "org.freedesktop.Application"


class DBusApplicationService(QtCore.QObject):
    """DBus service for handling application activation requests.

    This service allows external applications to activate NormCap via DBus
    with optional parameters. It's designed to work properly in Flatpak
    sandboxed environments.
    """

    # Signal emitted when activation is requested
    activated = QtCore.Signal(list)
    action_activated = QtCore.Signal(str, list)

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        """Initialize the DBus activation service.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._bus = QtDBus.QDBusConnection.sessionBus()
        self._registered = False

    def register_service(self) -> bool:
        """Register the DBus service.

        Returns:
            True if service was successfully registered, False otherwise
        """
        if not self._bus.isConnected():
            logger.error("Cannot connect to DBus session bus")
            return False

        # Register the service name
        if not self._bus.registerService(SERVICE_NAME):
            error = self._bus.lastError()
            logger.error(
                "Failed to register DBus service '%s': %s",
                SERVICE_NAME,
                error.message(),
            )
            return False

        # Register the object with specific interface name
        if not self._bus.registerObject(
            OBJECT_PATH,
            INTERFACE_NAME,
            self,
            QtDBus.QDBusConnection.RegisterOption.ExportAllSlots,
        ):
            error = self._bus.lastError()
            logger.error(
                "Failed to register DBus object '%s': %s", OBJECT_PATH, error.message()
            )
            self._bus.unregisterService(SERVICE_NAME)
            return False

        self._registered = True
        logger.info("DBus activation service registered: %s", SERVICE_NAME)
        return True

    def unregister_service(self) -> None:
        """Unregister the DBus service."""
        if not self._registered:
            return

        self._bus.unregisterObject(OBJECT_PATH)
        self._bus.unregisterService(SERVICE_NAME)
        self._registered = False
        logger.debug("DBus activation service unregistered")

    @QtCore.Slot(dict, result=bool)
    def Activate(self, platform_data: dict) -> bool:  # noqa: N802
        """DBus method: Activate the application with platform data.

        This method implements the standard org.freedesktop.Application.Activate
        method and can be called via DBus to activate NormCap.

        Args:
            platform_data: Dictionary containing platform-specific data such as
                          desktop-startup-id and activation-token

        Returns:
            True if activation was handled successfully
        """
        # Extract useful information from platform data
        activation_token = platform_data.get("activation-token", "")

        logger.info(
            "Activated via org.freedesktop.Application.Activate with platform_data: %s",
            platform_data,
        )

        # Convert to list format for consistency with existing signal
        params = [activation_token] if activation_token else []

        # Emit signal for the main application to handle
        self.activated.emit(params)

        return True

    @QtCore.Slot(str, list, dict, result=bool)
    def ActivateAction(  # noqa: N802
        self, action_name: str, params: list, platform_data: dict
    ) -> bool:
        # For some reason, the parameters are returned as list of list. In that case,
        # unpack it:
        if (
            len(params) == 1
            and isinstance(params, list)
            and isinstance(params[0], list)
        ):
            params = params[0]

        logger.info(
            "ActivateAction signal received. %s: %s (%s)",
            action_name,
            params,
            platform_data,
        )

        self.action_activated.emit(action_name, params)
        return True

    def __del__(self) -> None:
        """Cleanup when object is destroyed."""
        self.unregister_service()

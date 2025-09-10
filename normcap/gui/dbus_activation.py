"""DBus activation service for NormCap.

This module provides DBus service activation functionality, allowing external
applications to activate NormCap via DBus calls with optional parameters.
"""

import logging

from PySide6 import QtCore, QtDBus

logger = logging.getLogger(__name__)

SERVICE_NAME = "com.github.dynobo.normcap"
OBJECT_PATH = "/com/github/dynobo/normcap"
INTERFACE_NAME = "com.github.dynobo.normcap.Application"


class DBusActivationService(QtCore.QObject):
    """DBus service for handling application activation requests.

    This service allows external applications to activate NormCap via DBus
    with optional parameters. It's designed to work properly in Flatpak
    sandboxed environments.
    """

    # Signal emitted when activation is requested
    activation_requested = QtCore.Signal(list)

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

        # Register the object without specifying interface -
        # QtDBus will auto-export slots
        if not self._bus.registerObject(
            OBJECT_PATH, self, QtDBus.QDBusConnection.RegisterOption.ExportAllSlots
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

    @QtCore.Slot(result=bool)
    @QtCore.Slot(QtDBus.QDBusVariant, result=bool)
    def Activate(self, parameters: QtDBus.QDBusVariant | None = None) -> bool:  # noqa: N802
        """DBus method: Activate the application with optional parameters.

        This method can be called via DBus to activate NormCap. It logs the
        activation request and emits a signal for the main application to handle.

        Args:
            parameters: Optional list of string parameters (QDBusVariant)

        Returns:
            True if activation was handled successfully
        """
        # Convert QDBusVariant to Python list if provided
        params = []
        if parameters is not None:
            try:
                # Handle QDBusVariant conversion
                if hasattr(parameters, "variant"):
                    variant_data = parameters.variant()
                    if isinstance(variant_data, list):
                        params = variant_data
                    elif variant_data:
                        params = [str(variant_data)]
                elif isinstance(parameters, list):
                    params = parameters
                elif parameters:
                    params = [str(parameters)]
            except Exception as e:
                logger.warning("Failed to parse parameters: %s", e)

        # Log the activation with parameters
        if params:
            logger.info("Activated with %s", params)
        else:
            logger.info("Activated with []")

        # Emit signal for the main application to handle
        self.activation_requested.emit(params)

        return True

    def __del__(self) -> None:
        """Cleanup when object is destroyed."""
        self.unregister_service()

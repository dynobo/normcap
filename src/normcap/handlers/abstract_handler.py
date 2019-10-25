"""Define Abstract (base) handler for Chain of Responsibility Handlers."""

# Default
import abc
import logging
from typing import Any, Optional


class Handler(abc.ABC):
    """
    The Handler interface declares a method for building the chain of handlers.
    It also declares a method for executing a request.
    """

    @abc.abstractmethod
    def set_next(self, handler: "Handler") -> "Handler":
        """Define handler that is exectued next."""

    @abc.abstractmethod
    def handle(self, request) -> Any:
        """Execute handler logic."""


class AbstractHandler(Handler):
    """
    Implementing he default chaining behavior.
    """

    _next_handler: Optional[Handler] = None

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler

    @abc.abstractmethod
    def handle(self, request: Any) -> Any:
        if self._next_handler:
            return self._next_handler.handle(request)

        return None

"""[summary]
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging


class Handler(ABC):
    """
    The Handler interface declares a method for building the chain of handlers.
    It also declares a method for executing a request.
    """

    @abstractmethod
    def set_next(self, handler: "Handler") -> "Handler":
        pass

    @abstractmethod
    def handle(self, request) -> Any:
        pass


class AbstractHandler(Handler):
    """
    The default chaining behavior can be implemented inside a base handler
    class.
    """

    _next_handler: Optional[Handler] = None
    _logger = logging.getLogger(__name__)

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        # Returning a handler from here will let us link handlers in a
        # convenient way like this:
        # monkey.set_next(squirrel).set_next(dog)
        return handler

    @abstractmethod
    def handle(self, request: Any) -> Any:
        if self._next_handler:
            return self._next_handler.handle(request)

        return None

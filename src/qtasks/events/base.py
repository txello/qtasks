"""Base events."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import Generic, Literal, overload

from qtasks.events.events import OnEvents
from qtasks.types.typing import TAsyncFlag


class BaseEvents(Generic[TAsyncFlag], ABC):
    """Base class for events."""

    def __init__(self, on: "OnEvents"):
        """Initialize the base event class."""
        self._on = on

    @property
    def on(self):
        """Task event."""
        return self._on

    @overload
    def fire(
        self: "BaseEvents[Literal[False]]", event_name: str, *args, **kwargs
    ) -> None: ...

    @overload
    async def fire(
        self: "BaseEvents[Literal[True]]", event_name: str, *args, **kwargs
    ) -> None: ...

    @abstractmethod
    def fire(self, event_name: str, *args, **kwargs) -> None | Awaitable[None]:
        """
        The event is fired.
        
                Args:
                    event_name (str): Event name.
                    *args: Positional arguments.
                    **kwargs: Named arguments.
        """
        pass

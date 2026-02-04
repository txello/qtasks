"""Async events."""

import asyncio
from typing import Literal

from qtasks.events.base import BaseEvents
from qtasks.events.events import OnEvents


class AsyncEvents(BaseEvents[Literal[True]]):
    """A class for handling asynchronous events."""

    def __init__(self):
        """Initialize a class to handle asynchronous events."""
        super().__init__(on=OnEvents())
        pass

    async def fire(self, event_name: str, *args, **kwargs):
        """Fire all callbacks for the event."""
        callbacks = self.on._events.get(event_name, [])
        for callback in callbacks:
            result = callback(*args, **kwargs)
            if asyncio.iscoroutine(result):
                await result

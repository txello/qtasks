"""Sync events."""

from qtasks.events.base import BaseEvents
from qtasks.events.events import OnEvents


class SyncEvents(BaseEvents):
    """Class for processing synchronous events."""

    def __init__(self):
        """Initializing a class to handle synchronous events."""
        super().__init__(on=OnEvents())
        pass

    def fire(self, event_name: str, *args, **kwargs):
        """Fire all callbacks for the event."""
        callbacks = self.on._events.get(event_name, [])
        for callback in callbacks:
            callback(*args, **kwargs)
        return

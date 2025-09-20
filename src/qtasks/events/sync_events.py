"""Sync events."""

from qtasks.events.base import BaseEvents
from qtasks.events.events import OnEvents


class SyncEvents(BaseEvents):
    """Класс для обработки синхронных событий."""

    def __init__(self):
        """Инициализация класса для обработки синхронных событий."""
        super().__init__(on=OnEvents())
        pass

    def fire(self, event_name: str, *args, **kwargs):
        """Запустить все колбэки для события."""
        callbacks = self.on._events.get(event_name, [])
        for callback in callbacks:
            callback(*args, **kwargs)
        return

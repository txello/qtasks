"""Async events."""

import asyncio

from qtasks.events.base import BaseEvents
from qtasks.events.events import OnEvents


class AsyncEvents(BaseEvents):
    """Класс для обработки асинхронных событий."""

    def __init__(self):
        """Инициализация класса для обработки асинхронных событий."""
        super().__init__(on=OnEvents())
        pass

    async def fire(self, event_name: str, *args, **kwargs):
        """Запустить все колбэки для события."""
        callbacks = self.on._events.get(event_name, [])
        for callback in callbacks:
            result = callback(*args, **kwargs)
            if asyncio.iscoroutine(result):
                await result

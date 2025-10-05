"""Base events."""

from abc import ABC, abstractmethod
from typing import Awaitable, Generic, Literal, Union, overload

from qtasks.events.events import OnEvents
from qtasks.types.typing import TAsyncFlag


class BaseEvents(Generic[TAsyncFlag], ABC):
    """Базовый класс для событий."""

    def __init__(self, on: "OnEvents"):
        """Инициализация базового класса событий."""
        self._on = on

    @property
    def on(self):
        """Событие задачи."""
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
    def fire(self, event_name: str, *args, **kwargs) -> Union[None, Awaitable[None]]:
        """Срабатывает событие.

        Args:
            event_name (str): Имя события.
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
        """
        pass

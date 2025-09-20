"""Base events."""

from abc import ABC, abstractmethod

from qtasks.events.events import OnEvents


class BaseEvents(ABC):
    """Базовый класс для событий."""

    def __init__(self, on: "OnEvents"):
        """Инициализация базового класса событий."""
        self._on = on

    @property
    def on(self):
        """Событие задачи."""
        return self._on

    @abstractmethod
    def fire(self, event_name: str, *args, **kwargs) -> None:
        """Срабатывает событие.

        Args:
            event_name (str): Имя события.
            *args: Позиционные аргументы.
            **kwargs: Именованные аргументы.
        """
        pass

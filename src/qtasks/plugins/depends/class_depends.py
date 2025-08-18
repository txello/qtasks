"""Depends Class."""

from typing import Callable


class Depends:
    """Класс для управления зависимостями."""

    def __init__(self, func: Callable):
        """Инициализация класса Depends."""
        self.func = func

"""Depends Class."""

from collections.abc import Callable
from typing import Union

from qtasks.plugins.depends.enums.scope import ScopeEnum
from qtasks.types.annotations import P, R


class Depends:
    """Класс для управления зависимостями."""

    def __init__(self, func: Callable[P, R], scope: Union[ScopeEnum, str] = ScopeEnum.TASK):
        """Инициализация класса Depends."""
        self.func = func
        self.scope = scope.value if isinstance(scope, ScopeEnum) else scope

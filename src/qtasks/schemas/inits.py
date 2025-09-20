"""Init Inits."""

from dataclasses import dataclass
from types import FunctionType


@dataclass
class InitsExecSchema:
    """`InitsExecSchema` схема.

    Args:
        name (str): Имя события.
        func (FunctionType): Функция инициализации.

        awaiting (bool): Асинхронность инициализации. По умолчанию: False
    """

    name: str
    func: FunctionType

    awaiting: bool = False

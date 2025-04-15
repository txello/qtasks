from dataclasses import dataclass
from types import FunctionType


@dataclass
class InitsExecSchema:
    """`InitsExecSchema` схема.

    Args:
        typing (str): Тип инициализации.
        func (FunctionType): Функция инициализации.
        awaiting (bool): Асинхронность инициализации. По умолчанию: False
    """
    typing: str
    func: FunctionType
    
    awaiting: bool = False
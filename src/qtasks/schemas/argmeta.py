"""ArgMeta Schema."""

from dataclasses import dataclass
from typing import Any, Type, Optional


@dataclass
class ArgMeta:
    """Метаданные аргумента.

    Args:
        name (str): Имя аргумента.
        origin (Optional[Type]): Происхождение аргумента (например, list, dict и т. д.).
        raw_type (Optional[Type]): Исходный тип аргумента.
        annotation (Any): Аннотация аргумента.
        is_kwarg (bool): Является ли аргумент ключевым словом.
        index (Optional[int]): Индекс аргумента (только для позиционных аргументов).
        key (Optional[str]): Ключ аргумента (только для аргументов с ключевым словом).
    """

    name: str
    origin: Optional[Type]
    raw_type: Optional[Type]
    annotation: Any
    is_kwarg: bool
    index: Optional[int] = None
    key: Optional[str] = None

"""ArgMeta Schema."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ArgMeta:
    """
    Argument metadata.
    
        Args:
            name (str): Name of the argument.
            origin (Optional[Type]): The origin of the argument (e.g. list, dict, etc.).
            raw_type (Optional[Type]): The raw type of the argument.
            annotation (Any): Annotation of the argument.
            is_kwarg (bool): Whether the argument is a keyword.
            index (Optional[int]): Index of the argument (for positional arguments only).
            key (Optional[str]): The key of the argument (for keyword arguments only).
    """

    name: str
    value: Any
    origin: type | None
    raw_type: type | None
    annotation: Any
    is_kwarg: bool
    index: int | None = None
    key: str | None = None

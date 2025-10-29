"""QTasks type annotations."""

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

from collections.abc import Callable
from typing import TypeVar

P = ParamSpec("P", bound=Callable)  # type: ignore
R = TypeVar("R")

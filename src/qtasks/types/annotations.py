"""QTasks type annotations."""
try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

from typing import Callable, TypeVar

P = ParamSpec("P", bound=Callable)
R = TypeVar("R")

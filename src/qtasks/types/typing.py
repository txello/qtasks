"""QTasks typing utilities."""

from typing import Literal, TypeVar


T = TypeVar("T")

TAsyncFlag = TypeVar("TAsyncFlag", Literal[True], Literal[False])

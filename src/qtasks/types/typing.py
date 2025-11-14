"""QTasks typing utilities."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

if TYPE_CHECKING:
    from qtasks.registries.async_task_decorator import AsyncTask
    from qtasks.registries.sync_task_decorator import SyncTask

T = TypeVar("T")

TAsyncFlag = TypeVar("TAsyncFlag", Literal[True], Literal[False])

TTask = TypeVar("TTask", "AsyncTask", "SyncTask")

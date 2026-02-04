from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from qtasks.schemas.task import Task
from qtasks.schemas.task_cls import BaseTaskCls

if TYPE_CHECKING:
    from qtasks.registries.sync_task_decorator import SyncTask


class SyncChain:
    def __init__(self, *tasks: BaseTaskCls[SyncTask]) -> None:
        self.tasks = tasks

    async def get(self, timeout: float = 50.0) -> list[Task | None]:
        results = []
        older_result: Optional[tuple] = None


        for task_cls in self.tasks:
            if not task_cls._task_deco:
                results.append(None)
                continue

            if not task_cls.timeout:
                task_cls.timeout = timeout
            if older_result is not None:
                task_cls.args = (*task_cls.args, older_result)

            task = task_cls.add_task()
            if task:
                older_result = task.returning
            results.append(task)

        return results

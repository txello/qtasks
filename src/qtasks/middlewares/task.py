from typing import TYPE_CHECKING

from .base import BaseMiddleware

if TYPE_CHECKING:
    from qtasks.executors.base import BaseTaskExecutor


class TaskMiddleware(BaseMiddleware):
    def __init__(self,
            task_executor: "BaseTaskExecutor"
        ):
        super().__init__(name="TaskMiddleware")
        self.task_executor = task_executor

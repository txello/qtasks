"""Base Task Middleware."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import BaseMiddleware

if TYPE_CHECKING:
    from qtasks.executors.base import BaseTaskExecutor


class TaskMiddleware(BaseMiddleware):
    """
    `TaskMiddleware` - An abstract class that is the foundation for task Middleware classes for `TaskExecutor`.

    ## Example

    ```python
    from qtasks.middlewares import TaskMiddleware
    from qtasks.executors.base import BaseTaskExecutor

    class MyTaskMiddleware(TaskMiddleware):
        def __init__(self, task_executor: BaseTaskExecutor):
            super().__init__(name="MyTaskMiddleware")
            self.task_executor = task_executor
    ```
    """

    def __init__(self, task_executor: BaseTaskExecutor):
        """
        Initializing the task middleware.

        Args:
            task_executor (BaseTaskExecutor): A task executor instance.
        """
        super().__init__(name="TaskMiddleware")
        self.task_executor = task_executor

    def __call__(self, *args, **kwargs) -> Any:
        """
        Processing the task middleware call.

        Returns:
            Any: Processing result.
        """
        pass

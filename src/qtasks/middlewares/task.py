from typing import TYPE_CHECKING

from .base import BaseMiddleware

if TYPE_CHECKING:
    from qtasks.executors.base import BaseTaskExecutor


class TaskMiddleware(BaseMiddleware):
    """
    `TaskMiddleware` - Абстрактный класс, который является фундаментом для классов Мидлварей задач для `TaskExecutor`.

    ## Пример

    ```python
    from qtasks.middlewares import TaskMiddleware
    from qtasks.executors.base import BaseTaskExecutor

    class MyTaskMiddleware(TaskMiddleware):
        def __init__(self, task_executor: BaseTaskExecutor):
            super().__init__(name="MyTaskMiddleware")
            self.task_executor = task_executor
    ```
    """
    def __init__(self,
            task_executor: "BaseTaskExecutor"
        ):
        super().__init__(name="TaskMiddleware")
        self.task_executor = task_executor

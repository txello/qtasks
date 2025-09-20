from qtasks.middlewares import TaskMiddleware
from qtasks.executors.base import BaseTaskExecutor


class MyTaskMiddleware(TaskMiddleware):
    def __init__(self, task_executor: "BaseTaskExecutor"):
        super().__init__(task_executor)

    async def __call__(self):
        return self.task_executor

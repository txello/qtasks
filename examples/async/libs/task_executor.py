from typing import Any, Union
from qtasks.executors.base import BaseTaskExecutor


class MyAsyncTaskExecutor(BaseTaskExecutor):
    def __init__(self, task_func, task_broker, log=None):
        super().__init__(task_func, task_broker, log)

    async def before_execute(self):
        pass

    async def after_execute(self):
        pass

    async def execute_middlewares(self):
        pass

    async def run_task(self) -> Any:
        pass

    async def execute(
        self,
        decode: bool = True
    ) -> Union[Any, str]:
        pass

    async def decode(self) -> str:
        return ""

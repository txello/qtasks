from typing import Any
from qtasks.executors.base import BaseTaskExecutor


class MySyncTaskExecutor(BaseTaskExecutor):
    def __init__(self, task_func, task_broker, middlewares = None, log = None):
        super().__init__(task_func, task_broker, middlewares, log)

    def before_execute(self):
        pass

    def after_execute(self):
        pass

    def execute_middlewares(self):
        pass

    def run_task(self) -> Any:
        pass
    
    def execute(self,
            decode: bool = True
        ) -> Any|str:
        pass

    def decode(self) -> str:
        pass

class MyAsyncTaskExecutor(BaseTaskExecutor):
    def __init__(self, task_func, task_broker, middlewares = None, log = None):
        super().__init__(task_func, task_broker, middlewares, log)

    def before_execute(self):
        pass

    def after_execute(self):
        pass

    def execute_middlewares(self):
        pass

    def run_task(self) -> Any:
        pass
    
    async def execute(self,
            decode: bool = True
        ) -> Any|str:
        pass

    def decode(self) -> str:
        pass
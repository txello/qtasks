from typing import Any, Union
from qtasks.executors.base import BaseTaskExecutor


class MySyncTaskExecutor(BaseTaskExecutor):
    def __init__(self, task_func, task_broker, log=None):
        super().__init__(task_func, task_broker, log)

    def before_execute(self):
        pass

    def after_execute(self):
        pass

    def execute_middlewares(self):
        pass

    def run_task(self) -> Any:
        pass

    def execute(
        self,
        decode: bool = True
    ) -> Union[Any, str]:
        pass

    def decode(self) -> str:
        return ""

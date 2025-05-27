import json
from typing import Any, Optional
from typing_extensions import Annotated, Doc
from qtasks.logs import Logger
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema


class SyncTaskExecutor:
    def __init__(self,
            task_func: Annotated[
                TaskExecSchema,
                Doc(
                    """
                    `TaskExecSchema` схема.
                    """
                )
            ],
            task_broker: Annotated[
                TaskPrioritySchema,
                Doc(
                    """
                    `TaskPrioritySchema` схема.
                    """
                )
            ],
            middlewares: Annotated[
                Optional[Any],
                Doc(
                    """
                    Массив Миддлварей.
                    
                    По умолчанию: `Пустой массив`.
                    """
                )
            ] = None,
            log: Annotated[
                Optional[Logger],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.logs.Logger`.
                    """
                )
            ] = None
        ):
        self.task_func = task_func
        self.task_broker = task_broker

        self.middlewares = middlewares or []
        self._result: Any = None

        self.log = log
        if self.log is None:
            import qtasks._state
            self.log = qtasks._state.log_main
        self.log = self.log.with_subname("SyncTaskExecutor")


    def before_execute(self):
        pass

    def after_execute(self):
        pass

    def execute_middlewares(self):
        for m in self.middlewares:
            self.log.debug(f"Вызван Middleware {m.name} для {self.task_func.name}")
            m(self)

    def run_task(self) -> Any:
        if self.task_broker.args and self.task_broker.kwargs:
            result = self.task_func.func(*self.task_broker.args, **self.task_broker.kwargs)
        elif self.task_broker.args:
            result = self.task_func.func(*self.task_broker.args)
        elif self.task_broker.kwargs:
            result = self.task_func.func(**self.task_broker.kwargs)
        else:
            result = self.task_func.func()
        return result
    
    def execute(self,
            decode: bool = True
        ) -> Any|str:
        self.log.debug(f"Вызван execute для {self.task_func.name}")
        self.execute_middlewares()
        self.before_execute()
        self._result = self.run_task()
        self.after_execute()
        if decode:
            return self.decode()
        return self._result

    def decode(self) -> str:
        return json.dumps(self._result, ensure_ascii=False)

from dataclasses import replace
import json
from typing import TYPE_CHECKING, Any, Optional
from typing_extensions import Annotated, Doc

from qtasks.registries.sync_task_decorator import SyncTask

from .base import BaseTaskExecutor
from qtasks.logs import Logger
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema

if TYPE_CHECKING:
    from qtasks.middlewares.task import TaskMiddleware


class SyncTaskExecutor(BaseTaskExecutor):
    """
    `SyncTaskExecutor` - Синхронный класс исполнителя задач. Используется по умолчанию в `SyncThreadWorker`.

    ## Пример

    ```python
    from qtasks.executors import SyncTaskExecutor
    
    task_func = TaskExecSchema(...)
    task_broker = TaskPrioritySchema(...)
    executor = SyncTaskExecutor(task_func, task_broker)
    result = executor.execute()
    """
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
                Optional["TaskMiddleware"],
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
        """Инициализация класса. Происходит внутри `Worker` перед обработкой задачи.

        Args:
            task_func (TaskExecSchema): Схема `TaskExecSchema`.
            task_broker (TaskPrioritySchema): Схема `TaskPrioritySchema`.
            middlewares (List[Type[TaskMiddleware]], optional): _description_. По умолчанию `None`.
            log (Logger, optional): класс `qtasks.logs.Logger`. По умолчанию: `qtasks._state.log_main`.
        """
        super().__init__(task_func=task_func, task_broker=task_broker, middlewares=middlewares, log=log)

        self._args = []
        self._kwargs = {}
        self._result: Any = None


    def before_execute(self):
        """Вызов перед запуском задач."""
        if self.task_func.echo:
            echo = SyncTask(task_name=self.task_broker.name, priority=self.task_broker.priority,
                echo=self.task_func.echo,
                executor=self.task_func.executor, middlewares=self.task_func.middlewares
            )
            self._args = self.task_broker.args[:]
            self._args.insert(0, echo)
        else:
            self._args = self.task_broker.args
        self._kwargs = self.task_broker.kwargs

    def after_execute(self):
        """Вызов после запуска задач."""
        pass

    def execute_middlewares(self):
        """Вызов мидлварей."""
        for m in self.middlewares:
            m = m(self)
            self.log.debug(f"Middleware {m.name} для {self.task_func.name} был вызван.")

    def run_task(self) -> Any:
        """Вызов задачи.

        Returns:
            Any: Результат задачи.
        """
        if self.task_broker.args and self.task_broker.kwargs:
            result = self.task_func(*self.task_broker.args, **self.task_broker.kwargs)
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
        """Вызов задачи.

        Args:
            decode (bool, optional): Декодирование результата задачи. По умолчанию: True.

        Returns:
            Any|str: Результат задачи.
        """
        self.log.debug(f"Вызван execute для {self.task_func.name}")
        self.before_execute()
        self.execute_middlewares()
        self._result = self.run_task()
        self.after_execute()
        if decode:
            return self.decode()
        return self._result

    def decode(self) -> str:
        """Декодирование задачи.

        Returns:
            str: Результат задачи.
        """
        return json.dumps(self._result, ensure_ascii=False)

"""Sync Task Executor."""

import json
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Tuple, Type
from typing_extensions import Annotated, Doc

from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.registries.sync_task_decorator import SyncTask

from .base import BaseTaskExecutor
from qtasks.logs import Logger
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema

if TYPE_CHECKING:
    from qtasks.middlewares.task import TaskMiddleware
    from qtasks.plugins.base import BasePlugin


class SyncTaskExecutor(BaseTaskExecutor, SyncPluginMixin):
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

    def __init__(
        self,
        task_func: Annotated[
            TaskExecSchema,
            Doc(
                """
                    `TaskExecSchema` схема.
                    """
            ),
        ],
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc(
                """
                    `TaskPrioritySchema` схема.
                    """
            ),
        ],
        middlewares: Annotated[
            Optional["TaskMiddleware"],
            Doc(
                """
                    Массив Миддлварей.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        log: Annotated[
            Optional[Logger],
            Doc(
                """
                    Логгер.

                    По умолчанию: `qtasks.logs.Logger`.
                    """
            ),
        ] = None,
        plugins: Annotated[
            Optional[Dict[str, List[Type["BasePlugin"]]]],
            Doc(
                """
                    Массив Плагинов.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
    ):
        """Инициализация класса. Происходит внутри `Worker` перед обработкой задачи.

        Args:
            task_func (TaskExecSchema): Схема `TaskExecSchema`.
            task_broker (TaskPrioritySchema): Схема `TaskPrioritySchema`.
            middlewares (List[Type[TaskMiddleware]], optional): _description_. По умолчанию `None`.
            log (Logger, optional): класс `qtasks.logs.Logger`. По умолчанию: `qtasks._state.log_main`.
        """
        super().__init__(
            task_func=task_func,
            task_broker=task_broker,
            middlewares=middlewares,
            log=log,
            plugins=plugins,
        )

        self._args = []
        self._kwargs = {}
        self._result: Any = None
        self.echo = None

    def before_execute(self):
        """Вызывается перед выполнением задачи."""
        if self.task_func.echo:
            self.echo = SyncTask(
                task_name=self.task_broker.name,
                priority=self.task_broker.priority,
                echo=self.task_func.echo,
                retry=self.task_func.retry,
                retry_on_exc=self.task_func.retry_on_exc,
                executor=self.task_func.executor,
                middlewares=self.task_func.middlewares,
            )
            self.echo.ctx._update(task_uuid=self.task_broker.uuid)
            self._args = self.task_broker.args[:]
            self._args.insert(0, self.echo)
        else:
            self._args = self.task_broker.args
        self._kwargs = self.task_broker.kwargs

        args_info = self._build_args_info(self._args, self._kwargs)

        new_args: Tuple[list, dict] = self._plugin_trigger(
            "task_executor_args_replace",
            task_executor=self,
            **{
                "args": self._args,
                "kwargs": self._kwargs,
                "args_info": args_info,
            }
        )
        if new_args:
            self._args, self._kwargs = new_args[-1]

        self._plugin_trigger("task_executor_before_execute", task_executor=self)

    def after_execute(self):
        """Вызывается после выполнения задачи."""
        self._plugin_trigger("task_executor_after_execute", task_executor=self)
        result: Any = self._plugin_trigger(
            "task_executor_result_replace", task_executor=self, result=self._result
        )
        if result:
            self._result = result[-1]
        return

    def execute_middlewares(self):
        """Вызов мидлварей."""
        self._plugin_trigger("task_executor_middlewares_execute", task_executor=self, middlewares=self.middlewares)
        for m in self.middlewares:
            m = m(self)
            self.log.debug(f"Middleware {m.name} для {self.task_func.name} был вызван.")

    def run_task(self) -> Any | list[Any]:
        """Вызов задачи.

        Returns:
            Any: Результат задачи.
        """
        if self._args and self._kwargs:
            result = self.task_func.func(*self._args, **self._kwargs)
        elif self._args:
            result = self.task_func.func(*self._args)
        elif self._kwargs:
            result = self.task_func.func(**self._kwargs)
        else:
            result = self.task_func.func()

        if self.task_func.generating:
            return self.run_task_gen(result)

        new_result = self._plugin_trigger("task_executor_run_task", task_executor=self, result=result)
        if new_result:
            result = new_result[-1]

        return result

    def run_task_gen(self, func: Generator) -> list[Any]:
        """Вызов генератора задачи.

        Args:
            func (FunctionType): Функция.

        Raises:
            RuntimeError: Невозможно запустить асинхронный генератор задачи в синхронном виде!

        Returns:
            Any: Результат задачи.
        """
        if self.echo:
            self.echo.ctx._update(generate_handler=self.task_func.generate_handler)

        results = []
        if self.task_func.generating == "async":
            raise RuntimeError(
                "Невозможно запустить асинхронный генератор задачи в синхронном виде!"
            )

        elif self.task_func.generating == "sync":
            try:
                while True:
                    result = next(func)
                    if self.task_func.generate_handler:
                        result = self.task_func.generate_handler(result)
                    results.append(result)
            except StopIteration:
                pass

        new_results = self._plugin_trigger("task_executor_run_task_gen", task_executor=self, results=results)
        if new_results:
            results = new_results[-1]
        return results

    def execute(self, decode: bool = True) -> Any | str:
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
        result = json.dumps(self._result, ensure_ascii=False)
        new_result = self._plugin_trigger("task_executor_decode", task_executor=self, result=result)
        if new_result:
            result = new_result[-1]
        return result

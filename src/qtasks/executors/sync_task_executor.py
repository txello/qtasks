"""Sync Task Executor."""

import json
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Type, Union
from typing_extensions import Annotated, Doc

from qtasks.exc.plugins import TaskPluginTriggerError
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
    ```
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
            log (Logger, optional): класс `qtasks.logs.Logger`. По умолчанию: `qtasks._state.log_main`.
            plugins (Dict[str, List[Type[BasePlugin]]], optional): Словарь плагинов. По умолчанию: `Пустой словарь`.
        """
        super().__init__(
            task_func=task_func,
            task_broker=task_broker,
            log=log,
            plugins=plugins,
        )

    def before_execute(self):
        """Вызывается перед выполнением задачи."""
        if self.task_func.echo:
            self.echo = SyncTask(
                task_name=self.task_broker.name,
                priority=self.task_broker.priority,
                echo=self.task_func.echo,
                retry=self.task_func.retry,
                retry_on_exc=self.task_func.retry_on_exc,
                decode=self.task_func.decode,
                tags=self.task_func.tags,
                description=self.task_func.description,
                executor=self.task_func.executor,
                middlewares_before=self.task_func.middlewares_before,
                middlewares_after=self.task_func.middlewares_after,
                extra=self.task_func.extra
            )
            self.echo.ctx._update(task_uuid=self.task_broker.uuid)
            self._args.insert(0, self.echo)

        args_from_func = self._extract_args_kwargs_from_func(self.task_func.func)
        args_info = self._build_args_info(args_from_func[0], args_from_func[1])
        new_args = self._plugin_trigger(
            "task_executor_args_replace",
            task_executor=self,
            **{
                "args": self._args,
                "kw": self._kwargs,
                "args_info": args_info,
            },
            return_last=True
        )
        if new_args:
            self._args, self._kwargs = new_args.get("args", self._args), new_args.get("kw", self._kwargs)

        self._plugin_trigger("task_executor_before_execute", task_executor=self)

    def after_execute(self):
        """Вызывается после выполнения задачи."""
        self._plugin_trigger("task_executor_after_execute", task_executor=self)
        result = self._plugin_trigger(
            "task_executor_after_execute_result_replace", task_executor=self, result=self._result, return_last=True
        )
        if result:
            self._result = result.get("result", self._result)
        return

    def execute_middlewares_before(self):
        """Вызов мидлварей до выполнения задачи."""
        self._plugin_trigger(
            "task_executor_middlewares_execute",
            task_executor=self,
            middlewares_before=self.task_func.middlewares_before
        )
        for m in self.task_func.middlewares_before:
            m: "TaskMiddleware" = m(self)
            new_task_executor: BaseTaskExecutor = m()
            if new_task_executor:
                self = new_task_executor
            self.log.debug(f"Middleware {m.name} для {self.task_func.name} был вызван.")

    def execute_middlewares_after(self):
        """Вызов мидлварей после выполнения задачи."""
        self._plugin_trigger(
            "task_executor_middlewares_execute",
            task_executor=self,
            middlewares_after=self.task_func.middlewares_after
        )
        for m in self.task_func.middlewares_after:
            m: "TaskMiddleware" = m(self)
            new_task_executor: BaseTaskExecutor = m()
            if new_task_executor:
                self = new_task_executor
            self.log.debug(f"Middleware {m.name} для {self.task_func.name} был вызван.")

    def run_task(self) -> Union[Any, list]:
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
            result = new_result.get("result", result)

        return result

    def run_task_gen(self, func: Generator) -> List[Any]:
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
            results = new_results.get("results", results)
        return results

    def execute(self, decode: bool = True) -> Union[Any, str]:
        """Вызов задачи.

        Args:
            decode (bool, optional): Декодирование результата задачи. По умолчанию: True.

        Returns:
            Any|str: Результат задачи.
        """
        self.log.debug(f"Вызван execute для {self.task_func.name}")
        self.before_execute()
        self.execute_middlewares_before()
        try:
            self._result = self.run_task()
        except TaskPluginTriggerError as e:
            new_result = self._plugin_trigger(
                "task_executor_run_task_trigger_error",
                task_executor=self,
                task_func=self.task_func,
                task_broker=self.task_broker,
                e=e,
                return_last=True
            )
            if new_result:
                self._result = new_result.get("result", self._result)
            else:
                raise e

        self.after_execute()
        self.execute_middlewares_after()
        if decode:
            self._result = self.decode()
        return self._result

    def decode(self) -> Any:
        """Декодирование задачи.

        Returns:
            Any: Результат задачи.
        """
        if self.task_func.decode is not None:
            result = self.task_func.decode(self._result)
        else:
            result = json.dumps(self._result, ensure_ascii=False)
        new_result = self._plugin_trigger("task_executor_decode", task_executor=self, result=result)
        if new_result:
            result = new_result.get("result", result)
        return result

"""Async Task Executor."""

import asyncio
import json
from collections.abc import AsyncGenerator, Generator
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
)

from typing_extensions import Doc

from qtasks.exc.plugins import TaskPluginTriggerError
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema

from .base import BaseTaskExecutor

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class AsyncTaskExecutor(BaseTaskExecutor, AsyncPluginMixin):
    """
    `AsyncTaskExecutor` - Синхронный класс исполнителя задач. Используется по умолчанию в `AsyncWorker`.

    ## Пример

    ```python
    import asyncio
    from qtasks.executors import AsyncTaskExecutor

    task_func = TaskExecSchema(...)
    task_broker = TaskPrioritySchema(...)
    executor = AsyncTaskExecutor(task_func, task_broker)
    result = asyncio.run(executor.execute())
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
            Logger | None,
            Doc(
                """
                    Логгер.

                    По умолчанию: `qtasks.logs.Logger`.
                    """
            ),
        ] = None,
        plugins: Annotated[
            dict[str, list["BasePlugin"]] | None,
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
            plugins (Dict[str, List[BasePlugin]], optional): Массив плагинов. По умолчанию: `Пустой массив`.
        """
        super().__init__(
            task_func=task_func,
            task_broker=task_broker,
            log=log,
            plugins=plugins,
        )

    async def before_execute(self):
        """Вызывается перед выполнением задачи."""
        if self.task_func.echo:
            task_cls = (
                SyncTask
                if not self.task_func.awaiting or self.task_func.generating == "sync"
                else AsyncTask
            )
            self.echo = task_cls(
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
                extra=self.task_func.extra,
            )
            self.echo.ctx._update(task_uuid=self.task_broker.uuid)
            self._args.insert(0, self.echo)

        args_from_func = self._extract_args_kwargs_from_func(self.task_func.func)
        args_info = self._build_args_info(args_from_func[0], args_from_func[1])
        new_args = await self._plugin_trigger(
            "task_executor_args_replace",
            task_executor=self,
            **{
                "args": self._args,
                "kw": self._kwargs,
                "args_info": args_info,
            },
            return_last=True,
        )
        if new_args:
            kw: dict = new_args.get("kw")  # type: ignore
            if not kw:
                self._args = kw.get("args", self._args)
                self._kwargs = kw.get("kw", self._kwargs)

        await self._plugin_trigger("task_executor_before_execute", task_executor=self)

    async def after_execute(self):
        """Вызов после запуска задач."""
        await self._plugin_trigger("task_executor_after_execute", task_executor=self)
        result: Any = await self._plugin_trigger(
            "task_executor_after_execute_result_replace",
            task_executor=self,
            result=self._result,
            return_last=True,
        )
        if result:
            self._result = result.get("result", self._result)
        return

    async def execute_middlewares_before(self):
        """Вызов мидлварей до выполнения задачи."""
        await self._plugin_trigger(
            "task_executor_middlewares_execute",
            task_executor=self,
            middlewares_before=self.task_func.middlewares_before,
        )
        for m in self.task_func.middlewares_before:
            m = m(self)
            new_task_executor: BaseTaskExecutor = await m()
            if new_task_executor:
                self = new_task_executor
            if self.log:
                self.log.debug(f"Middleware {m.name} для {self.task_func.name} был вызван.")

    async def execute_middlewares_after(self):
        """Вызов мидлварей после выполнения задачи."""
        await self._plugin_trigger(
            "task_executor_middlewares_execute",
            task_executor=self,
            middlewares_after=self.task_func.middlewares_after,
        )
        for m in self.task_func.middlewares_after:
            m = m(self)
            new_task_executor: BaseTaskExecutor = await m()
            if new_task_executor:
                self = new_task_executor
            if self.log:
                self.log.debug(f"Middleware {m.name} для {self.task_func.name} был вызван.")

    async def run_task(self) -> Any:
        """Вызов задачи.

        Returns:
            Any: Результат задачи.
        """
        if self._args and self._kwargs:
            result = (
                await self.task_func.func(*self._args, **self._kwargs)
                if self.task_func.awaiting
                else self.task_func.func(*self._args, **self._kwargs)
            )
        elif self._args:
            result = (
                await self.task_func.func(*self._args)
                if self.task_func.awaiting
                else self.task_func.func(*self._args)
            )
        elif self._kwargs:
            result = (
                await self.task_func.func(**self._kwargs)
                if self.task_func.awaiting
                else self.task_func.func(**self._kwargs)
            )
        else:
            result = (
                await self.task_func.func()
                if self.task_func.awaiting
                else self.task_func.func()
            )

        if self.task_func.generating:
            return await self.run_task_gen(result)

        new_result = await self._plugin_trigger(
            "task_executor_run_task", task_executor=self, result=result
        )
        if new_result:
            result = new_result.get("result", result)

        return result

    async def run_task_gen(self, func: AsyncGenerator | Generator) -> list[Any]:
        """Вызов генератора задачи.

        Args:
            func (AsyncGenerator, Generator): Функция.

        Returns:
            Any: Результат задачи.
        """
        if self.echo:
            self.echo.ctx._update(generate_handler=self.task_func.generate_handler)

        results = []
        if self.task_func.generating == "async":
            if isinstance(func, AsyncGenerator):
                async for result in func:
                    if self.task_func.generate_handler:
                        result = await self._maybe_await(
                            self.task_func.generate_handler(result)
                        )
                    results.append(result)

        elif self.task_func.generating == "sync":
            if isinstance(func, Generator):
                try:
                    while True:
                        result = next(func)
                        if self.task_func.generate_handler:
                            result = await self._maybe_await(
                                self.task_func.generate_handler(result)
                            )
                        results.append(result)
                except StopIteration:
                    pass
        new_results = await self._plugin_trigger(
            "task_executor_run_task_gen", task_executor=self, results=results
        )
        if new_results:
            results = new_results.get("results", results)
        return results

    async def _maybe_await(self, value):
        if asyncio.iscoroutine(value):
            return await value
        return value

    async def execute(self, decode: bool = True) -> Any | str:
        """Вызов задачи.

        Args:
            decode (bool, optional): Декодирование результата задачи. По умолчанию: True.

        Returns:
            Any|str: Результат задачи.
        """
        if self.log:
            self.log.debug(f"Вызван execute для {self.task_func.name}")

        await self.execute_middlewares_before()
        await self.before_execute()
        try:
            if self.task_func.max_time:
                self._result = await asyncio.wait_for(
                    self.run_task(), timeout=self.task_func.max_time
                )
            else:
                self._result = await self.run_task()
        except TaskPluginTriggerError as e:
            new_result = await self._plugin_trigger(
                "task_executor_run_task_trigger_error",
                task_executor=self,
                task_func=self.task_func,
                task_broker=self.task_broker,
                e=e,
                return_last=True,
            )
            if new_result:
                self._result = new_result.get("result", self._result)
            else:
                raise e
        except asyncio.TimeoutError as exc:
            msg = f"Время выполнения задачи {self.task_func.name} превысило лимит {self.task_func.max_time} секунд"
            if self.log:
                self.log.error(msg)
            raise asyncio.TimeoutError(msg) from exc

        await self.after_execute()
        await self.execute_middlewares_after()
        if decode:
            self._result = await self.decode()

        await self._plugin_trigger(
                "task_executor_task_close",
                task_executor=self,
                task_func=self.task_func,
                task_broker=self.task_broker
            )
        return self._result

    async def decode(self) -> Any:
        """Декодирование задачи.

        Returns:
            Any: Результат задачи.
        """
        if self.task_func.decode is not None:
            result = await self._maybe_await(self.task_func.decode(self._result))
        else:
            result = json.dumps(self._result, ensure_ascii=False)
        new_result = await self._plugin_trigger(
            "task_executor_decode", task_executor=self, result=result
        )
        if new_result:
            result = new_result.get("result", result)
        return result

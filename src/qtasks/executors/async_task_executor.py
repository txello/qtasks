"""Async Task Executor."""
from __future__ import annotations

import asyncio
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
    `AsyncTaskExecutor` - Synchronous task executor class. Used by default in `AsyncWorker`.

    ## Example

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
            Doc("""
                    `TaskExecSchema` schema.
                    """),
        ],
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc("""
                    `TaskPrioritySchema` schema.
                    """),
        ],
        log: Annotated[
            Logger | None,
            Doc("""
                    Logger.

                    Default: `qtasks.logs.Logger`.
                    """),
        ] = None,
        plugins: Annotated[
            dict[str, list[BasePlugin]] | None,
            Doc("""
                    Array of Plugins.

                    Default: `Empty array`.
                    """),
        ] = None,
    ):
        """
        Initializing the class. Occurs inside a `Worker` before a task is processed.

        Args:
            task_func (TaskExecSchema): Schema `TaskExecSchema`.
            task_broker(TaskPrioritySchema): Schema `TaskPrioritySchema`.
            log (Logger, optional): class `qtasks.logs.Logger`. Default: `qtasks._state.log_main`.
            plugins (Dict[str, List[BasePlugin]], optional): An array of plugins. Default: `Empty array`.
        """
        super().__init__(
            task_func=task_func,
            task_broker=task_broker,
            log=log,
            plugins=plugins,
        )

    async def before_execute(self):
        """Called before a task is executed."""
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
            self._args = new_args.get("args", self._args)
            self._kwargs = new_args.get("kw", self._kwargs)

        await self._plugin_trigger("task_executor_before_execute", task_executor=self)

    async def after_execute(self):
        """Call after starting tasks."""
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
        """Calling middleware before the task is completed."""
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
                self.log.debug(f"Middleware {m.name} for {self.task_func.name} was called.")

    async def execute_middlewares_after(self):
        """Calling middleware after completing a task."""
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
                self.log.debug(f"Middleware {m.name} for {self.task_func.name} was called.")

    async def run_task(self) -> Any:
        """
        Calling a task.

        Returns:
            Any: Result of the task.
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
        """
        Calling the task generator.

        Args:
            func(AsyncGenerator, Generator): Function.

        Returns:
            Any: Result of the task.
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
        """
        Calling a task.

        Args:
            decode (bool, optional): Decoding the result of the task. Default: True.

        Returns:
            Any|str: Result of the task.
        """
        if self.log:
            self.log.debug(f"Called execute for {self.task_func.name}")

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
            msg = f"Time limit exceeded for task {self.task_func.name}: {self.task_func.max_time} seconds"
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
        """
        Decoding the task.

        Returns:
            Any: Result of the task.
        """
        if self.task_func.decode is not None:
            result = await self._maybe_await(self.task_func.decode(self._result))
        else:
            result = self.decode_cls(self._result)

        new_result = await self._plugin_trigger(
            "task_executor_decode", task_executor=self, result=result
        )
        if new_result:
            result = new_result.get("result", result)
        return result

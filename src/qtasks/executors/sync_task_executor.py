"""Sync Task Executor."""
from __future__ import annotations

import json
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Annotated, Any

from typing_extensions import Doc

from qtasks.exc.plugins import TaskPluginTriggerError
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.registries.sync_task_decorator import SyncTask
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema

from .base import BaseTaskExecutor

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class SyncTaskExecutor(BaseTaskExecutor, SyncPluginMixin):
    """
    `SyncTaskExecutor` - Synchronous task executor class. Used by default in `SyncThreadWorker`.

    ## Example

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
            plugins (Dict[str, List[BasePlugin]], optional): Plugin dictionary. Default: `Empty dictionary`.
        """
        super().__init__(
            task_func=task_func,
            task_broker=task_broker,
            log=log,
            plugins=plugins,
        )

    def before_execute(self):
        """Called before a task is executed."""
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
                extra=self.task_func.extra,
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
            return_last=True,
        )
        if new_args:
            kw: dict = new_args.get("kw")  # type: ignore
            if not kw:
                self._args = kw.get("args", self._args)
                self._kwargs = kw.get("kw", self._kwargs)

        self._plugin_trigger("task_executor_before_execute", task_executor=self)

    def after_execute(self):
        """Called after a task has completed."""
        self._plugin_trigger("task_executor_after_execute", task_executor=self)
        result = self._plugin_trigger(
            "task_executor_after_execute_result_replace",
            task_executor=self,
            result=self._result,
            return_last=True,
        )
        if result:
            self._result = result.get("result", self._result)
        return

    def execute_middlewares_before(self):
        """Calling middleware before the task is completed."""
        self._plugin_trigger(
            "task_executor_middlewares_execute",
            task_executor=self,
            middlewares_before=self.task_func.middlewares_before,
        )
        for m in self.task_func.middlewares_before:
            m = m(self)
            new_task_executor: BaseTaskExecutor = m()
            if new_task_executor:
                self = new_task_executor
            self.log.debug(f"Middleware {m.name} for {self.task_func.name} was called.")

    def execute_middlewares_after(self):
        """Calling middleware after completing a task."""
        self._plugin_trigger(
            "task_executor_middlewares_execute",
            task_executor=self,
            middlewares_after=self.task_func.middlewares_after,
        )
        for m in self.task_func.middlewares_after:
            m = m(self)
            new_task_executor: BaseTaskExecutor = m()
            if new_task_executor:
                self = new_task_executor
            self.log.debug(f"Middleware {m.name} for {self.task_func.name} was called.")

    def run_task(self) -> Any | list:
        """
        Calling a task.

        Returns:
            Any: Result of the task.
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

        new_result = self._plugin_trigger(
            "task_executor_run_task", task_executor=self, result=result
        )
        if new_result:
            result = new_result.get("result", result)

        return result

    def run_task_gen(self, func: Generator) -> list[Any]:
        """
        Calling the task generator.

        Args:
            func(FunctionType): Function.

        Raises:
            RuntimeError: Unable to run synchronous task generator in synchronous form!

        Returns:
            Any: Result of the task.
        """
        if self.echo:
            self.echo.ctx._update(generate_handler=self.task_func.generate_handler)

        results = []
        if self.task_func.generating == "async":
            raise RuntimeError(
                "Cannot run an async task generator in synchronous mode!"
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

        new_results = self._plugin_trigger(
            "task_executor_run_task_gen", task_executor=self, results=results
        )
        if new_results:
            results = new_results.get("results", results)
        return results

    def execute(self, decode: bool = True) -> Any | str:
        """
        Calling a task.

        Args:
            decode (bool, optional): Decoding the result of the task. Default: True.

        Returns:
            Any|str: Result of the task.
        """
        if self.log:
            self.log.debug(f"Called execute for {self.task_func.name}")

        self.before_execute()
        self.execute_middlewares_before()
        try:
            if self.task_func.max_time:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self.run_task)
                    self._result = future.result(timeout=self.task_func.max_time)
            else:
                self._result = self.run_task()
        except TaskPluginTriggerError as e:
            new_result = self._plugin_trigger(
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
        except TimeoutError as exc:
            msg = f"Time limit exceeded for task {self.task_func.name}: {self.task_func.max_time} seconds"
            if self.log:
                self.log.error(msg)
            raise TimeoutError(msg) from exc

        self.after_execute()
        self.execute_middlewares_after()
        if decode:
            self._result = self.decode()

        self._plugin_trigger(
            "task_executor_task_close",
            task_executor=self,
            task_func=self.task_func,
            task_broker=self.task_broker
        )
        return self._result

    def decode(self) -> Any:
        """
        Decoding the task.

        Returns:
            Any: Result of the task.
        """
        if self.task_func.decode is not None:
            result = self.task_func.decode(self._result)
        else:
            result = json.dumps(self._result, ensure_ascii=False)
        new_result = self._plugin_trigger(
            "task_executor_decode", task_executor=self, result=result
        )
        if new_result:
            result = new_result.get("result", result)
        return result

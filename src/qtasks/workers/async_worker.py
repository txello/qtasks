"""Init module for async worker."""
from __future__ import annotations

import asyncio
import json
import traceback
from dataclasses import asdict
from datetime import datetime
from time import time
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional
from uuid import UUID

from anyio import Semaphore
from typing_extensions import Doc

from qtasks.brokers.async_redis import AsyncRedisBroker
from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.async_events import AsyncEvents
from qtasks.exc.task import TaskCancelError
from qtasks.executors.async_task_executor import AsyncTaskExecutor
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.plugins.depends.async_depends import AsyncDependsPlugin
from qtasks.plugins.pydantic import AsyncPydanticWrapperPlugin
from qtasks.plugins.retries import AsyncRetryPlugin
from qtasks.plugins.states.async_state import AsyncStatePlugin
from qtasks.schemas.task import Task
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import (
    TaskStatusCancelSchema,
    TaskStatusErrorSchema,
    TaskStatusProcessSchema,
    TaskStatusSuccessSchema,
)

from .base import BaseWorker

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.events.base import BaseEvents
    from qtasks.executors.base import BaseTaskExecutor


class AsyncWorker(BaseWorker, AsyncPluginMixin):
    """
    Worker, Receiving tasks from the Broker and processing them.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.workers import AsyncWorker

    worker = AsyncWorker()
    app = QueueTasks(worker=worker)
    ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc("""
                    Project name. This name is also used by the worker.

                    Default: `QueueTasks`.
                    """),
        ] = "QueueTasks",
        broker: Annotated[
            Optional[BaseBroker],
            Doc("""
                    Broker.

                    Default: `qtasks.brokers.AsyncRedisBroker`.
                    """),
        ] = None,
        log: Annotated[
            Logger | None,
            Doc("""
                    Logger.

                    Default: `qtasks.logs.Logger`.
                    """),
        ] = None,
        config: Annotated[
            QueueConfig | None,
            Doc("""
                    Config.

                    Default: `qtasks.configs.config.QueueConfig`.
                    """),
        ] = None,
        events: Annotated[
            Optional[BaseEvents],
            Doc("""
                    Events.

                    Default: `qtasks.events.AsyncEvents`.
                    """),
        ] = None,
    ):
        """
        Initializing an asynchronous worker.

        Args:
            name (str, optional): Project name. Default: "QueueTasks".
            broker (BaseBroker, optional): Broker. Default: `None`.
            log (Logger, optional): Logger. Default: `None`.
            config (QueueConfig, optional): Config. Default: `None`.
            events (BaseEvents, optional): Events. Default: `qtasks.events.AsyncEvents`.
        """
        super().__init__(
            name=name, broker=broker, log=log, config=config, events=events
        )

        self.events = self.events or AsyncEvents()
        self.events: BaseEvents[Literal[True]]

        self.broker = broker or AsyncRedisBroker(
            name=self.name, log=self.log, config=self.config
        )
        self.broker: BaseBroker[Literal[True]]

        self.queue = asyncio.PriorityQueue()

        self._tasks: dict[str, TaskExecSchema] = {}
        self._stop_event: asyncio.Event | None = None
        self.semaphore = asyncio.Semaphore(self.config.max_tasks_process)
        self.condition: asyncio.Condition | None = None

        self.task_executor = AsyncTaskExecutor

    async def worker(
        self,
        number: Annotated[
            int,
            Doc("""
                    Worker number.
                    """),
        ],
    ) -> None:
        """
        Task processor.

        Args:
            number (int): Worker number.

        Raises:
            RuntimeError: Worker is not running.
        """
        if not self._stop_event or not self.condition:
            raise RuntimeError("Worker is not running")

        await self.events.fire("worker_running", worker=self, number=number)

        try:
            while not self._stop_event.is_set():
                async with self.condition:
                    while self.queue.empty():
                        await self.condition.wait()

                task_broker: TaskPrioritySchema | None = await self.queue.get()
                if task_broker is None:
                    break
                asyncio.create_task(self._execute_task(task_broker))
        finally:
            await self.events.fire("worker_stopping", worker=self, number=number)

    async def _execute_task(
        self,
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc("""
                    Priority task diagram.
                    """),
        ],
    ) -> None:
        """
        Performs task independently.

        Args:
            task_broker (TaskPrioritySchema): The priority task schema.
        """
        async with self.semaphore:
            model = TaskStatusProcessSchema(
                task_name=task_broker.name,
                priority=task_broker.priority,
                created_at=task_broker.created_at,
                updated_at=time(),
                args=json.dumps(task_broker.args),
                kwargs=json.dumps(task_broker.kwargs),
            )

            task_func = await self._task_exists(task_broker=task_broker)
            if not task_func:
                self.queue.task_done()
                return

            new_model = await self._plugin_trigger(
                "worker_execute_before",
                worker=self,
                task_broker=task_broker,
                task_func=task_func,
                model=model,
                return_last=True,
            )
            if new_model:
                model = new_model.get("model", model)

            await self.broker.update(
                name=f"{self.name}:{task_broker.uuid}", mapping=asdict(model)
            )

            await self.events.fire(
                "task_running",
                worker=self,
                task_func=task_func,
                task_broker=task_broker,
            )
            model = await self._run_task(task_func, task_broker)
            await self.events.fire(
                "task_stopping",
                worker=self,
                task_func=task_func,
                task_broker=task_broker,
                model=model,
            )

            await self.remove_finished_task(
                task_func=task_func, task_broker=task_broker, model=model
            )

            await self._plugin_trigger(
                "worker_execute_after",
                task_func=task_func,
                task_broker=task_broker,
                model=model,
            )

            self.queue.task_done()

    async def add(
        self,
        name: Annotated[
            str,
            Doc("""
                    Task name.
                    """),
        ],
        uuid: Annotated[
            UUID,
            Doc("""
                    UUID of the task.
                    """),
        ],
        priority: Annotated[
            int,
            Doc("""
                    Task priority.
                    """),
        ],
        created_at: Annotated[
            float,
            Doc("""
                    Creating a task in timestamp format.
                    """),
        ],
        args: Annotated[
            tuple,
            Doc("""
                    Task arguments of type args.
                    """),
        ],
        kwargs: Annotated[
            dict,
            Doc("""
                    Task arguments of type kwargs.
                    """),
        ],
    ) -> Task:
        """
        Adding a task to the queue.

        Args:
            name (str): Name of the task.
            uuid (UUID): UUID of the task.
            priority (int): Task priority.
            created_at (float): Create a task in timestamp format.
            args (tuple): Task arguments of type args.
            kwargs (dict): Task arguments of type kwargs.

            Raises:
                RuntimeError: Worker is not running.
        """
        if not self.condition:
            raise RuntimeError("Worker is not running.")

        new_data = await self._plugin_trigger(
            "worker_add",
            worker=self,
            task_name=name,
            uuid=uuid,
            priority=priority,
            args=args,
            kw=kwargs,
            created_at=created_at,
            return_last=True,
        )
        if new_data:
            name = new_data.get("name", name)
            uuid = new_data.get("uuid", uuid)
            priority = new_data.get("priority", priority)
            args = new_data.get("args", args)
            kwargs = new_data.get("kw", kwargs)
            created_at = new_data.get("created_at", created_at)

        model = TaskPrioritySchema(
            priority=priority,
            uuid=uuid,
            name=name,
            args=list(args),
            kwargs=kwargs,
            created_at=created_at,
            updated_at=created_at,
        )
        async with self.condition:
            await self.queue.put(model)
            self.condition.notify_all()
        return Task(
            status=TaskStatusEnum.NEW.value,
            task_name=name,
            uuid=uuid,
            priority=priority,
            args=args,
            kwargs=kwargs,
            created_at=datetime.fromtimestamp(created_at),
            updated_at=datetime.fromtimestamp(created_at),
        )

    async def start(
        self,
        num_workers: Annotated[
            int,
            Doc("""
                    Number of workers.

                    Default: `4`.
                    """),
        ] = 4,
    ) -> None:
        """
        Runs multiple task handlers.

        Args:
            num_workers (int, optional): Number of workers. Default: 4.
        """
        self.num_workers = num_workers

        if self.condition is None:
            self.condition = asyncio.Condition()
        if self._stop_event is None:
            self._stop_event = asyncio.Event()
        await self._plugin_trigger("worker_start", worker=self)

        loop = asyncio.get_event_loop()
        workers = [
            loop.create_task(self.worker(number)) for number in range(self.num_workers)
        ]
        await self._stop_event.wait()

        for worker_task in workers:
            worker_task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    async def stop(self):
        """Stops workers."""
        await self._plugin_trigger("worker_stop", worker=self)
        if self._stop_event:
            self._stop_event.set()

    def update_config(
        self,
        config: Annotated[
            QueueConfig,
            Doc("""
                    Config.
                    """),
        ],
    ) -> None:
        """
        Updates the broker config and semaphore.

        Args:
            config (QueueConfig): Config.
        """
        self.config = config
        self.semaphore = Semaphore(config.max_tasks_process)

    async def _run_task(
        self, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusSuccessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema:
        """
        Run the task function.

        Args:
            task_func (TaskExecSchema): Schema `qtasks.schemas.TaskExecSchema`.
            task_broker(TaskPrioritySchema): Schema `qtasks.schemas.TaskPrioritySchema`.

        Returns:
            Any: The result of the task function.

        Raises:
            RuntimeError: task_executor is not defined.
        """
        if not self.task_executor:
            raise RuntimeError("task_executor is not defined.")

        if self.log:
            self.log.info(
                f"Task {task_broker.uuid} ({task_broker.name}) is running, priority: {task_broker.priority}.\n"
                f"Arguments of the task: {task_broker.args}, {task_broker.kwargs}"
            )

        new_data = await self._plugin_trigger(
            "worker_run_task_before",
            worker=self,
            task_func=task_func,
            task_broker=task_broker,
            return_last=True,
        )
        if new_data:
            task_func = new_data.get("task_func", task_func)
            task_broker = new_data.get("task_broker", task_broker)

        if self.task_middlewares_before:
            task_func.add_middlewares_before(self.task_middlewares_before)
        if self.task_middlewares_after:
            task_func.add_middlewares_after(self.task_middlewares_after)

        executor = (
            task_func.executor if task_func.executor is not None else self.task_executor
        )
        task_executor: BaseTaskExecutor[Literal[True]] = executor(
            task_func=task_func,
            task_broker=task_broker,
            log=self.log,
            plugins=self.plugins,
        )

        try:
            result = await task_executor.execute()
            return await self._task_success(result, task_func, task_broker)
        except TaskCancelError as e:
            return await self._task_cancel(e, task_func, task_broker)
        except BaseException as e:
            return await self._task_error(e, task_func, task_broker)

    async def _task_success(
        self, result: Any, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusSuccessSchema:
        """Event of successful completion of a task."""
        model = TaskStatusSuccessSchema(
            task_name=task_func.name,
            priority=task_func.priority,
            returning=result,
            created_at=task_broker.created_at,
            updated_at=time(),
            args=json.dumps(task_broker.args),
            kwargs=json.dumps(task_broker.kwargs),
        )
        if self.log:
            self.log.info(
                f"Task {task_broker.uuid} successfully completed, result: {result}"
            )
        return model

    async def _task_error(
        self, e, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusErrorSchema:
        """Event of task completion with an error."""
        trace = traceback.format_exc()

        # plugin: retry
        plugin_result = None

        should_retry = task_func.retry and (
            not task_func.retry_on_exc or type(e) in task_func.retry_on_exc
        )
        if should_retry and task_func.retry:
            plugin_result = await self._plugin_trigger(
                "worker_task_error_retry",
                broker=self.broker,
                task_func=task_func,
                task_broker=task_broker,
                trace=trace,
                return_last=True,
            )

        model = TaskStatusErrorSchema(
            task_name=task_func.name,
            priority=task_func.priority,
            traceback=trace,
            created_at=task_broker.created_at,
            updated_at=time(),
            args=json.dumps(task_broker.args),
            kwargs=json.dumps(task_broker.kwargs),
        )
        if plugin_result:
            model: TaskStatusErrorSchema = plugin_result.get("model", model)
        #

        if plugin_result and model.retry != 0:
            if self.log:
                self.log.error(
                    f"Task {task_broker.uuid} completed with an error and will be retried."
                )
        else:
            if self.log:
                self.log.error(f"Task {task_broker.uuid} completed with an error:\n{trace}")
        return model

    async def _task_cancel(
        self, e, task_func: TaskExecSchema, task_broker: TaskPrioritySchema
    ) -> TaskStatusCancelSchema:
        """Task cancellation event."""
        model = TaskStatusCancelSchema(
            task_name=task_func.name,
            priority=task_func.priority,
            cancel_reason=str(e),
            created_at=task_broker.created_at,
            updated_at=time(),
        )
        if self.log:
            self.log.error(f"Task {task_broker.uuid} was cancelled because: {e}")
        return model

    async def _task_exists(
        self, task_broker: TaskPrioritySchema
    ) -> TaskExecSchema | None:
        """
        Checking the existence of a task.

        Args:
            task_broker(TaskPrioritySchema): Schema `TaskPrioritySchema`.

        Returns:
            TaskExecSchema|None: Schema `TaskExecSchema` or `None`.
        """
        try:
            return self._tasks[task_broker.name]
        except KeyError as e:
            if self.log:
                self.log.warning(f"Task {e.args[0]} does not exist!")
            trace = traceback.format_exc()
            model = TaskStatusErrorSchema(
                task_name=task_broker.name,
                priority=task_broker.priority,
                traceback=trace,
                created_at=task_broker.created_at,
                updated_at=time(),
            )
            await self.remove_finished_task(
                task_func=None, task_broker=task_broker, model=model
            )
            if self.log:
                self.log.error(f"Task {task_broker.name} completed with an error:\n{trace}")
            return None

    async def remove_finished_task(
        self,
        task_func: Annotated[
            TaskExecSchema | None,
            Doc("""
                    Diagram of the task function.
                    """),
        ],
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc("""
                    Priority task diagram.
                    """),
        ],
        model: Annotated[
            TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema,
            Doc("""
                    Model of the task result.
                    """),
        ],
    ) -> None:
        """
        Updates storage data via the `self.storage.remove_finished_task` function.

        Args:
            task_func (TaskExecSchema, optional): Task function schema. Default: `None`.
            task_broker (TaskPrioritySchema): The priority task schema.
            model (TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema): Model of the task result.
        """
        new_data = await self._plugin_trigger(
            "worker_remove_finished_task",
            worker=self,
            broker=self.broker,
            task_func=task_func,
            task_broker=task_broker,
            model=model,
            return_last=True,
        )
        if new_data:
            task_broker, model = new_data.get("task_broker", task_broker), new_data.get(
                "model", model
            )
        await self.broker.remove_finished_task(task_broker, model)

    def init_plugins(self):
        """Initializing plugins."""
        self.add_plugin(AsyncRetryPlugin(), trigger_names=["worker_task_error_retry"])
        self.add_plugin(
            AsyncPydanticWrapperPlugin(),
            trigger_names=[
                "task_executor_args_replace",
                "task_executor_after_execute_result_replace",
            ],
        )
        self.add_plugin(
            AsyncDependsPlugin(), trigger_names=[
                "task_executor_args_replace",
                "task_executor_task_close",
                "worker_stop",
                "broker_stop",
                "storage_stop",
                "global_config_stop"
            ]
        )
        self.add_plugin(
            AsyncStatePlugin(), trigger_names=["task_executor_args_replace"]
        )

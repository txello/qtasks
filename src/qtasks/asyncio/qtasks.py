"""qtasks.py - Main asyncio module for the QueueTasks framework."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional, Union, overload
from uuid import UUID

import asyncio_atexit
from typing_extensions import Doc

from qtasks.base.qtasks import BaseQueueTasks
from qtasks.brokers.async_redis import AsyncRedisBroker
from qtasks.configs import QueueConfig
from qtasks.events.async_events import AsyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.results.async_result import AsyncResult
from qtasks.schemas.task_exec import TaskExecSchema
from qtasks.starters.async_starter import AsyncStarter
from qtasks.workers.async_worker import AsyncWorker

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.events.base import BaseEvents
    from qtasks.schemas.task import Task
    from qtasks.starters.base import BaseStarter
    from qtasks.workers.base import BaseWorker


class QueueTasks(BaseQueueTasks[Literal[True]], AsyncPluginMixin):
    """
    `QueueTasks` - Framework for task queues.

    Read more:
    [First steps](https://txello.github.io/qtasks/getting_started/).

    ## Example

    ```python
    from qtasks import QueueTasks

    app = QueueTasks()
    ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Project name.

                    Default: `QueueTasks`.
                    """
            ),
        ] = "QueueTasks",
        broker_url: Annotated[
            str | None,
            Doc(
                """
                    URL for the Broker. Used by the Broker by default via the url parameter.

                    Default: `None`.
                    """
            ),
        ] = None,
        broker: Annotated[
            Optional[BaseBroker],
            Doc(
                """
                    Broker. Stores processing from task queues and data storage.

                    Default: `qtasks.brokers.AsyncRedisBroker`.
                    """
            ),
        ] = None,
        worker: Annotated[
            Optional[BaseWorker],
            Doc(
                """
                    Worker. Stores task processing.

                    Default: `qtasks.workers.AsyncWorker`.
                    """
            ),
        ] = None,
        log: Annotated[
            Logger | None,
            Doc(
                """
                    Logger.

                    Default: `qtasks.logs.Logger`.
                    """
            ),
        ] = None,
        config: Annotated[
            QueueConfig | None,
            Doc(
                """
                    Config.

                    Default: `qtasks.configs.QueueConfig`.
                    """
            ),
        ] = None,
        events: Annotated[
            Optional[BaseEvents],
            Doc(
                """
                    Events.

                    Default: `qtasks.events.AsyncEvents`.
                    """
            ),
        ] = None,
    ):
        """
        Initializing QueueTasks.

        Args:
            name (str): Project name. Default: `QueueTasks`.
            broker_url (str, optional): URL for the Broker. Used by the Broker by default via the url parameter. Default: `None`.
            broker (Type[BaseBroker], optional): Broker. Stores processing from task queues and data storage. Default: `qtasks.brokers.AsyncRedisBroker`.
            worker (Type[BaseWorker], optional): Worker. Stores task processing. Default: `qtasks.workers.AsyncWorker`.
            log (Logger, optional): Logger. Default: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Config. Default: `qtasks.configs.QueueConfig`.
            events (BaseEvents, optional): Events. Default: `qtasks.events.AsyncEvents`.
        """
        broker = broker or AsyncRedisBroker(
            name=name, url=broker_url, log=log, config=config, events=events
        )
        worker = worker or AsyncWorker(
            name=name, broker=broker, log=log, config=config, events=events
        )

        events = events or AsyncEvents()

        super().__init__(
            name=name,
            broker=broker,
            worker=worker,
            log=log,
            config=config,
            events=events,
        )

        self._method = "async"

        self.broker: BaseBroker[Literal[True]]
        self.worker: BaseWorker[Literal[True]]

        self.starter: BaseStarter[Literal[True]] | None = None

        self._global_loop: Annotated[
            asyncio.AbstractEventLoop | None,
            Doc(
                """
                Async event loop, optional.

                Default: `None`.
                """
            ),
        ] = None

        self._registry_tasks()

        self._set_state()

    @overload
    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    The name of the task.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    Task args.

                    Default: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Task priority.

                    Default: Task priority value.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float,
            Doc(
                """
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """
            ),
        ] = 0.0,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Task kwargs.

                    Default: `{}`.
                    """
            ),
        ],
    ) -> Optional[Task]: ...

    @overload
    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    The name of the task.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    Task args.

                    Default: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Task priority.

                    Default: Task priority value.
                    """
            ),
        ] = None,
        timeout: Annotated[
            None,
            Doc(
                """
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Task kwargs.

                    Default: `{}`.
                    """
            ),
        ],
    ) -> Task: ...

    @overload
    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    The name of the task.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    Task args.

                    Default: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Task priority.

                    Default: Task priority value.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
            Doc(
                """
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Task kwargs.

                    Default: `{}`.
                    """
            ),
        ],
    ) -> Optional[Task]: ...

    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    The name of the task.
                    """
            ),
        ],
        *args: Annotated[
            Any,
            Doc(
                """
                    Task args.

                    Default: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Task priority.

                    Default: Task priority value.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
            Doc(
                """
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Task kwargs.

                    Default: `{}`.
                    """
            ),
        ],
    ) -> Union[Task, Optional[Task]]:
        """
        Add a task.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. Default: Task priority value.
            args (tuple, optional): Task args. Defaults to `()`.
            kwargs (dict, optional): Kwargs tasks. Defaults to `{}`.

            timeout (float, optional): Task timeout. If specified, the task is returned via `qtasks.results.AsyncResult`.

        Returns:
            Task|None: `schemas.task.Task` or `None`.
        """
        if priority is None:
            task_registry = self.tasks.get(task_name, 0)
            priority = (
                task_registry.priority
                if isinstance(task_registry, TaskExecSchema)
                else 0
            )

        args, kwargs = args or (), kwargs or {}
        extra = None

        new_args = await self._plugin_trigger(
            "qtasks_add_task_before_broker",
            qtasks=self,
            broker=self.broker,
            task_name=task_name,
            priority=priority,
            args=args,
            kw=kwargs,
            return_last=True,
        )

        task_priority: int = priority

        if new_args:
            task_name = new_args.get("task_name", task_name)
            task_priority = new_args.get("priority", task_priority)
            extra = new_args.get("extra", extra)
            args = new_args.get("args", args)
            kwargs = new_args.get("kw", kwargs)

        task = await self.broker.add(
            task_name=task_name,
            priority=task_priority,
            extra=extra,
            args=args,
            kwargs=kwargs,
        )

        await self._plugin_trigger(
            "qtasks_add_task_after_broker",
            qtasks=self,
            broker=self.broker,
            task_name=task_name,
            priority=task_priority,
            args=args,
            kwargs=kwargs,
        )

        if timeout is not None:
            return await AsyncResult(uuid=task.uuid, app=self, log=self.log).result(
                timeout=timeout
            )
        return task

    async def get(
        self,
        uuid: Annotated[
            UUID | str,
            Doc(
                """
                    UUID of the Task.
                    """
            ),
        ],
    ) -> Union[Task, None]:
        """
        Get a task.

        Args:
            uuid (UUID|str): UUID of the Task.

        Returns:
            Task|None: Task data or None.
        """
        if isinstance(uuid, str):
            uuid = UUID(uuid)

        result = await self.broker.get(uuid=uuid)
        new_result = await self._plugin_trigger(
            "qtasks_get", qtasks=self, broker=self.broker, task=result, return_last=True
        )
        if new_result:
            result = new_result.get("task", result)
        return result

    def run_forever(
        self,
        loop: Annotated[
            asyncio.AbstractEventLoop | None,
            Doc(
                """
                    Async Event loop.

                    Default: `None`.
                    """
            ),
        ] = None,
        starter: Annotated[
            Optional[BaseStarter],
            Doc(
                """
                    Starter.

                    Default: `qtasks.starters.AsyncStarter`.
                    """
            ),
        ] = None,
        num_workers: Annotated[
            int,
            Doc(
                """
                    Number of workers running.

                     Default: `4`.
                    """
            ),
        ] = 4,
        reset_config: Annotated[
            bool,
            Doc(
                """
                    Update the config of the worker and broker.

                     Default: `True`.
                    """
            ),
        ] = True,
    ) -> None:
        """
        Launch asynchronously Application.

        Args:
            loop (asyncio.AbstractEventLoop, optional): async loop. Default: `None`.
            starter (BaseStarter, optional): Starter. Default: `qtasks.starters.AsyncStarter`.
            num_workers (int, optional): Number of workers running. Default: `4`.
            reset_config (bool, optional): Update the config of the worker and broker. Default: `True`.
        """
        self.starter = starter or AsyncStarter(
            name=self.name,
            worker=self.worker,
            broker=self.broker,
            log=self.log,
            config=self.config,
            events=self.events,
        )

        plugins_hash = {}
        for plugins in [
            self.plugins,
            self.worker.plugins,
            self.broker.plugins,
            self.broker.storage.plugins,
        ]:
            plugins_hash.update(plugins)

        self._set_state()

        self.starter.start(
            loop=loop,
            num_workers=num_workers,
            reset_config=reset_config,
            plugins=plugins_hash,
        )

    async def stop(self):
        """Stops all components."""
        await self._plugin_trigger("qtasks_stop", qtasks=self, starter=self.starter)
        if self.starter:
            await self.starter.stop()

    async def ping(
        self,
        server: Annotated[
            bool,
            Doc(
                """
                    Verification via server.

                    Default: `True`.
                    """
            ),
        ] = True,
    ) -> bool:
        """
        Checking server startup.

        Args:
            server (bool, optional): Verification via server. Default: `True`.

        Returns:
            bool: True - Works, False - Doesn't work.
        """
        await self._plugin_trigger(
            "qtasks_ping", qtasks=self, global_config=self.broker.storage.global_config
        )
        if server and self.broker.storage.global_config:
            loop = asyncio.get_running_loop()
            asyncio_atexit.register(self.broker.storage.global_config.stop, loop=loop)
            status = await self.broker.storage.global_config.get("main", "status")
            return status is not None
        return True

    async def flush_all(self) -> None:
        """Delete all data."""
        await self._plugin_trigger("qtasks_flush_all", qtasks=self, broker=self.broker)
        await self.broker.flush_all()

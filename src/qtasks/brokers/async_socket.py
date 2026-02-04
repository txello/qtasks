"""Async Socket Broker."""
from __future__ import annotations

import asyncio
import contextlib
import json
from dataclasses import asdict
from datetime import datetime
from time import time
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional
from uuid import UUID, uuid4

import asyncio_atexit
from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.async_events import AsyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.schemas.task import Task
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import (
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusSuccessSchema,
)
from qtasks.storages.async_redis import AsyncRedisStorage

from .base import BaseBroker

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker


class AsyncSocketBroker(BaseBroker, AsyncPluginMixin):
    """
    A broker that listens to sockets and adds tasks to the queue.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import AsyncSocketBroker

    broker = AsyncSocketBroker(name="QueueTasks", url="127.0.0.1")

    app = QueueTasks(broker=broker)
    ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc("""
                    Project name. This name is also used by the broker.

                    Default: `QueueTasks`.
                    """),
        ] = "QueueTasks",
        url: Annotated[
            str,
            Doc("""
                    URL to connect to the socket.

                    Default: `127.0.0.1`.
                    """),
        ] = "127.0.0.1",
        port: Annotated[
            int,
            Doc("""
                    Port for connecting to a socket.

                    Default: `6379`.
                    """),
        ] = 6379,
        storage: Annotated[
            Optional[BaseStorage],
            Doc("""
                    Storage.

                    Default: `AsyncRedisStorage`.
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
        Initializing AsyncSocketBroker.

        Args:
            name (str, optional): Project name. Default: `QueueTasks`.
            url (str, optional): URL to connect to the socket. Default: `127.0.0.1`.
            port (int, optional): Port to connect to the socket. Default: `6379`.
            storage (BaseStorage, optional): Storage. Default: `None`.
            log (Logger, optional): Logger. Default: `None`.
            config (QueueConfig, optional): Config. Default: `None`.
            events (BaseEvents, optional): Events. Default: `qtasks.events.AsyncEvents`.
        """
        self.url = url
        self.port = port
        storage = storage or AsyncRedisStorage(
            name=name, log=log, config=config, events=events
        )

        super().__init__(
            name=name, log=log, config=config, events=events, storage=storage
        )

        self.storage: BaseStorage[Literal[True]]

        self.events = self.events or AsyncEvents()

        self.client = None
        self.default_sleep = 0.01
        self.running = False

        self.queue = asyncio.Queue()
        self._serve_task: asyncio.Task | None = None
        self._listen_task: asyncio.Task | None = None

    async def handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """
        Handles an incoming connection.

        Args:
            reader(asyncio.StreamReader): Reader for incoming data.
            writer(asyncio.StreamWriter): Writer for outgoing data.
        """
        try:
            data = await reader.read(4096)
            message = json.loads(data.decode())
            task_name = message["task_name"]
            uuid = message["uuid"]
            priority = message["priority"]
            args = message.get("args", ())
            kwargs = message.get("kwargs", {})
            created_at = message["created_at"]

            await self.storage.add(
                uuid=uuid,
                task_status=TaskStatusNewSchema(
                    task_name=task_name,
                    priority=priority,
                    args=args,
                    kwargs=kwargs,
                    created_at=created_at,
                    updated_at=created_at,
                ),
            )

            await self.queue.put((task_name, uuid, priority))
            writer.write(b"OK")
            await writer.drain()
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    async def listen(
        self,
        worker: Annotated[
            BaseWorker[Literal[True]],
            Doc("""
                    Worker class.
                    """),
        ],
    ):
        """
        Listens to the socket queue and transfers tasks to the worker.

        Args:
            worker (BaseWorker): Worker class.

        Raises:
            KeyError: Task not found.
        """
        await self._plugin_trigger("broker_listen_start", broker=self, worker=worker)
        self.running = True

        while self.running:
            try:
                item = await self.queue.get()
            except asyncio.CancelledError:
                break
            if item is None:
                break

            task_name, uuid, priority = item
            model_get = await self.get(uuid=uuid)
            if not model_get:
                raise KeyError(f"Task not found: {uuid}")

            args, kwargs, created_at = (
                model_get.args or (),
                model_get.kwargs or {},
                model_get.created_at.timestamp(),
            )

            await self.storage.add_process(f"{task_name}:{uuid}:{priority}", priority)

            if self.log:
                self.log.info(f"Received new task: {uuid}")
            new_args = await self._plugin_trigger(
                "broker_add_worker",
                broker=self,
                worker=worker,
                task_name=task_name,
                uuid=uuid,
                priority=int(priority),
                args=args,
                kw=kwargs,
                created_at=created_at,
                return_last=True,
            )
            if new_args:
                task_name = new_args.get("task_name", task_name)
                uuid = new_args.get("uuid", uuid)
                priority = new_args.get("priority", priority)
                args = new_args.get("args", args)
                kwargs = new_args.get("kw", kwargs)
                created_at = new_args.get("created_at", created_at)

            await worker.add(
                name=task_name,
                uuid=uuid,
                priority=int(priority),
                args=args,
                kwargs=kwargs,
                created_at=created_at,
            )
            return

    async def add(
        self,
        task_name: Annotated[
            str,
            Doc("""
                    Task name.
                    """),
        ],
        priority: Annotated[
            int,
            Doc("""
                    Task priority.

                    Default: `0`.
                    """),
        ] = 0,
        extra: Annotated[
            dict | None,
            Doc("""
                    Additional task parameters.

                    Default: `None`.
                    """),
        ] = None,
        args: Annotated[
            tuple | None,
            Doc("""
                    Task arguments of type args.

                    Default: `()`.
                    """),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc("""
                    Task arguments of type kwargs.

                    Default: `{}`.
                    """),
        ] = None,
    ) -> Task:
        """
        Adds a task to the broker.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. By default: 0.
            extra (dict, optional): Additional task parameters. Default: `None`.
            args (tuple, optional): Task arguments of type args. Default: `()`.
            kwargs (dict, optional): Task arguments of type kwargs. Default: `{}`.

        Returns:
            Task: `schemas.task.Task`

        Raises:
            ValueError: Invalid task status.
        """
        loop = asyncio.get_running_loop()
        asyncio_atexit.register(self.stop, loop=loop)
        asyncio_atexit.register(self.storage.stop, loop=loop)

        args, kwargs = args or (), kwargs or {}
        uuid = uuid4()
        uuid_str = str(uuid)
        created_at = time()
        model = TaskStatusNewSchema(
            task_name=task_name,
            priority=priority,
            created_at=created_at,
            updated_at=created_at,
            args=str(args),
            kwargs=str(kwargs),
        )

        if extra:
            model = self._dynamic_model(model=model, extra=extra)

        new_model = await self._plugin_trigger(
            "broker_add_before", broker=self, storage=self.storage, model=model
        )
        if new_model:
            model = new_model.get("model", model)

        if not isinstance(model, TaskStatusNewSchema):
            raise ValueError("Invalid task status.")

        await self.storage.add(uuid=uuid, task_status=model)
        reader, writer = await asyncio.open_connection(self.url, self.port)
        payload = asdict(model)
        payload.update({"uuid": uuid_str})
        writer.write(json.dumps(payload).encode())
        await writer.drain()
        with contextlib.suppress(Exception):
            writer.close()

        await self._plugin_trigger(
            "broker_add_after", broker=self, storage=self.storage, model=model
        )
        return Task(
            status=TaskStatusEnum.NEW.value,
            task_name=task_name,
            uuid=uuid,
            priority=priority,
            args=args,
            kwargs=kwargs,
            created_at=datetime.fromtimestamp(created_at),
            updated_at=datetime.fromtimestamp(created_at),
        )

    async def get(
        self,
        uuid: Annotated[
            UUID | str,
            Doc("""
                    UUID of the task.
                    """),
        ],
    ) -> Task | None:
        """
        Obtaining information about a task.

        Args:
            uuid (UUID|str): UUID of the task.

        Returns:
            Task|None: If there is task information, returns `schemas.task.Task`, otherwise `None`.
        """
        if isinstance(uuid, str):
            uuid = UUID(uuid)
        task = await self.storage.get(uuid=uuid)
        new_task = await self._plugin_trigger(
            "broker_get", broker=self, task=task, return_last=True
        )
        if new_task:
            task = new_task.get("task", task)
        return task

    async def update(
        self,
        **kwargs: Annotated[
            Any,
            Doc("""
                    Update arguments for storage type kwargs.
                    """),
        ],
    ) -> None:
        """
        Updates task information.

        Args:
            kwargs (dict, optional): task data of type kwargs.
        """
        new_kw = await self._plugin_trigger(
            "broker_update", broker=self, kw=kwargs, return_last=True
        )
        if new_kw:
            kwargs = new_kw.get("kw", kwargs)
        return await self.storage.update(**kwargs)

    async def start(
        self,
        worker: Annotated[
            BaseWorker,
            Doc("""
                    Worker class.
                    """),
        ],
    ) -> None:
        """
        Launches the broker.

        Args:
            worker (BaseWorker): Worker class.
        """
        await self._plugin_trigger("broker_start", broker=self, worker=worker)
        await self.storage.start()

        if self.config.delete_finished_tasks:
            await self.storage._delete_finished_tasks()

        if self.config.running_older_tasks:
            await self.storage._running_older_tasks(worker)

        self.client = await asyncio.start_server(
            self.handle_connection, self.url, self.port
        )

        self._listen_task = asyncio.create_task(
            self.listen(worker), name="broker-listen"
        )
        self._serve_task = asyncio.create_task(
            self.client.serve_forever(), name="broker-serve"
        )
        with contextlib.suppress(asyncio.CancelledError):
            await self._serve_task

    async def stop(self):
        """The broker stops."""
        await self._plugin_trigger("broker_stop", broker=self)
        self.running = False

        if self._listen_task and not self._listen_task.done():
            self.queue.put_nowait(None)

        if self.client:
            self.client.close()
            with contextlib.suppress(Exception):
                await self.client.wait_closed()

        if self._serve_task and not self._serve_task.done():
            self._serve_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._serve_task

        if self._listen_task and not self._listen_task.done():
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task

    async def remove_finished_task(
        self,
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc("""
                    Priority task diagram.
                    """),
        ],
        model: Annotated[
            TaskStatusSuccessSchema | TaskStatusErrorSchema,
            Doc("""
                    Model of the task result.
                    """),
        ],
    ) -> None:
        """
        Updates storage data via the `self.storage.remove_finished_task` function.

        Args:
            task_broker (TaskPrioritySchema): The priority task schema.
            model (TaskStatusSuccessSchema | TaskStatusErrorSchema): Model of the task result.
        """
        new_model = await self._plugin_trigger(
            "broker_remove_finished_task",
            broker=self,
            storage=self.storage,
            model=model,
            return_last=True,
        )
        if new_model:
            model = new_model.get("model", model)

        await self.storage.remove_finished_task(task_broker, model)
        return

    async def _running_older_tasks(self, worker):
        await self._plugin_trigger(
            "broker_running_older_tasks", broker=self, worker=worker
        )
        return await self.storage._running_older_tasks(worker)

    async def flush_all(self) -> None:
        """Delete all data."""
        await self._plugin_trigger("broker_flush_all", broker=self)
        await self.storage.flush_all()

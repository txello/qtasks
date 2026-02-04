"""Async RabbitMQ Broker."""
from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Optional

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.async_events import AsyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.schemas.task_exec import TaskPrioritySchema

try:
    import aio_pika
except ImportError as exc:
    raise ImportError("Install with `pip install qtasks[rabbitmq]` to use this broker.") from exc

from time import time
from typing import Annotated
from uuid import UUID, uuid4

from typing_extensions import Doc

from qtasks.schemas.task import Task
from qtasks.schemas.task_status import (
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusSuccessSchema,
)
from qtasks.storages import AsyncRedisStorage

from .base import BaseBroker

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker


class AsyncRabbitMQBroker(BaseBroker, AsyncPluginMixin):
    """
    A broker that listens to RabbitMQ and adds tasks to the queue.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import AsyncRabbitMQBroker

    broker = AsyncRabbitMQBroker(name="QueueTasks", url="amqp://guest:guest@localhost/")

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
                    URL to connect to RabbitMQ.

                    Default: `amqp://guest:guest@localhost/`.
                    """),
        ] = "amqp://guest:guest@localhost/",
        storage: Annotated[
            Optional[BaseStorage],
            Doc("""
                    Storage.

                    Default: `AsyncRedisStorage`.
                    """),
        ] = None,
        queue_name: Annotated[
            str,
            Doc("""
                    The name of the task queue for RabbitMQ. The title is updated to: `name:queue_name`

                    Default: `task_queue`.
                    """),
        ] = "task_queue",
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
        Initializing AsyncRabbitMQBroker.

        Args:
            name (str, optional): Project name. Default: `QueueTasks`.
            url (str, optional): URL to connect to RabbitMQ. Default: `None`.
            storage (BaseStorage, optional): Storage. Default: `None`.
            queue_name (str, optional): RabbitMQ queue name. Default: `task_queue`.
            log (Logger, optional): Logger. Default: `None`.
            config (QueueConfig, optional): Config. Default: `None`.
            events (BaseEvents, optional): Events. Default: `qtasks.events.AsyncEvents`.
        """
        self.url = url

        storage = storage or AsyncRedisStorage(
            name=name, log=log, config=config, events=events
        )
        super().__init__(
            name=name, log=log, config=config, events=events, storage=storage
        )

        self.storage: BaseStorage[Literal[True]]

        self.queue_name = f"{self.name}:{queue_name}"
        self.events = self.events or AsyncEvents()

        self.connection = None
        self.channel = None
        self.running = False

    async def connect(self):
        """Connecting to RabbitMQ is asynchronous."""
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        self.queue = await self.channel.declare_queue(self.queue_name, durable=True)

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
        Listens to the RabbitMQ queue and transfers tasks to the worker.

        Args:
            worker (BaseWorker): Worker class.
        """
        await self._plugin_trigger("broker_listen_start", broker=self, worker=worker)
        if not self.channel:
            await self.connect()

        async with self.queue.iterator() as queue_iter:
            self.running = True
            async for message in queue_iter:
                async with message.process():
                    task_data = json.loads(message.body)
                    task_name, uuid, priority = (
                        task_data["task_name"],
                        task_data["uuid"],
                        task_data["priority"],
                    )
                    args, kwargs = task_data.get("args", ()), task_data.get(
                        "kwargs", {}
                    )
                    created_at = task_data.get("created_at", 0)

                    await self.storage.add_process(
                        f'{task_data["task_name"]}:{task_data["uuid"]}:{task_data["priority"]}',
                        task_data["priority"],
                    )
                    if self.log:
                        self.log.info(f"Received new task: {task_data['uuid']}")
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
                        priority=priority,
                        args=args,
                        kwargs=kwargs,
                        created_at=created_at,
                    )
                if not self.running:
                    break

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

                    Default: `None`.
                    """),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc("""
                    Task arguments of type kwargs.

                    Default: `None`.
                    """),
        ] = None,
    ) -> Task:
        """
        Adds a task to the broker.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. Default: `0`.
            extra (dict, optional): Additional task parameters. Default: `None`.
            args (tuple, optional): Task arguments of type args. Default: `None`.
            kwargs (dict, optional): Task arguments of type kwargs. Default: `None`.

        Returns:
            Task: `schemas.task.Task`

        Raises:
            RuntimeError: self.channel is not defined. The server is not running!
        """
        args, kwargs = args or (), kwargs or {}
        if not self.channel:
            await self.connect()
        if not isinstance(self.channel, aio_pika.channel.Channel):
            raise RuntimeError("self.channel is not defined. The server is not running!")
        self.channel: aio_pika.channel.Channel

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
            "broker_add_before",
            broker=self,
            storage=self.storage,
            model=model,
            return_last=True,
        )
        if new_model:
            model = new_model.get("model", model)

        await self.storage.add(uuid=uuid, task_status=model)

        task_data = {
            "uuid": uuid_str,
            "task_name": task_name,
            "priority": priority,
            "args": args,
            "kwargs": kwargs,
            "created_at": created_at,
        }

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(task_data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=self.queue_name,
        )

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

        await self.listen(worker)

    async def stop(self):
        """The broker stops."""
        await self._plugin_trigger("broker_stop", broker=self)
        self.running = False
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None

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

        return await self.storage.remove_finished_task(task_broker, model)

    async def _running_older_tasks(self, worker):
        await self._plugin_trigger(
            "broker_running_older_tasks", broker=self, worker=worker
        )
        return await self.storage._running_older_tasks(worker)

    async def flush_all(self) -> None:
        """Delete all data."""
        await self._plugin_trigger("broker_flush_all", broker=self)
        await self.storage.flush_all()

"""Async Redis Broker."""
from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable
from datetime import datetime
from time import time
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional, cast
from uuid import UUID, uuid4

import asyncio_atexit
import redis.asyncio as aioredis
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


class AsyncRedisBroker(BaseBroker[Literal[True]], AsyncPluginMixin):
    """
    A broker that listens to Redis and adds tasks to the queue.
    
        ## Example
    
        ```python
        from qtasks import QueueTasks
        from qtasks.brokers import AsyncRedisBroker
    
        broker = AsyncRedisBroker(name="QueueTasks", url="redis://localhost:6379/2")
    
        app = QueueTasks(broker=broker)
        ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Имя проекта. Это имя также используется брокером.

                    По умолчанию: `QueueTasks`.
                    """
            ),
        ] = "QueueTasks",
        url: Annotated[
            str | None,
            Doc(
                """
                    URL для подключения к Redis.

                    По умолчанию: `redis://localhost:6379/0`.
                    """
            ),
        ] = None,
        storage: Annotated[
            Optional[BaseStorage],
            Doc(
                """
                    Хранилище.

                    По умолчанию: `AsyncRedisStorage`.
                    """
            ),
        ] = None,
        queue_name: Annotated[
            str,
            Doc(
                """
                    Имя массива очереди задач для Redis. Название обновляется на: `name:queue_name`.

                    По умолчанию: `task_queue`.
                    """
            ),
        ] = "task_queue",
        log: Annotated[
            Logger | None,
            Doc(
                """
                    Логгер.

                    По умолчанию: `qtasks.logs.Logger`.
                    """
            ),
        ] = None,
        config: Annotated[
            QueueConfig | None,
            Doc(
                """
                    Конфиг.

                    По умолчанию: `qtasks.configs.config.QueueConfig`.
                    """
            ),
        ] = None,
        events: Annotated[
            Optional[BaseEvents],
            Doc(
                """
                    События.

                    По умолчанию: `qtasks.events.AsyncEvents`.
                    """
            ),
        ] = None,
    ):
        """
        Initializing AsyncRedisBroker.
        
                Args:
                    name (str, optional): Project name. Default: "QueueTasks".
                    url (str, optional): URL to connect to Redis. Default: None.
                    storage (BaseStorage, optional): Storage. Default: None.
                    queue_name (str, optional): Name of the task queue array for Redis. Default: "task_queue".
                    log (Logger, optional): Logger. Default: None.
                    config (QueueConfig, optional): Config. Default: None.
                    events (BaseEvents, optional): Events. Default: `qtasks.events.AsyncEvents`.
        """
        self.url = url or "redis://localhost:6379/0"
        self.client = aioredis.Redis.from_url(
            self.url, decode_responses=True, encoding="utf-8"
        )
        storage = storage or AsyncRedisStorage(
            name=name,
            url=self.url,
            redis_connect=self.client,
            log=log,
            config=config,
            events=events,
        )

        events = events or AsyncEvents()

        super().__init__(
            name=name, log=log, config=config, events=events, storage=storage
        )

        self.storage: BaseStorage[Literal[True]]

        self.queue_name = f"{self.name}:{queue_name}"

        self.running = False
        self.default_sleep = 0.01

    async def listen(
        self,
        worker: Annotated[
            BaseWorker[Literal[True]],
            Doc(
                """
                    Класс воркера.
                    """
            ),
        ],
    ):
        """
        Listens to the Redis queue and passes tasks to the worker.
        
                Args:
                    worker (BaseWorker): Worker class.
        
                Raises:
                    ValueError: Unknown task data format.
                    KeyError: Task not found.
        """
        await self._plugin_trigger("broker_listen_start", broker=self, worker=worker)
        self.running = True

        while self.running:
            raw = self.client.lpop(self.queue_name)
            task_data = await cast(Awaitable[str | list[Any] | None], raw)

            if not task_data:
                await asyncio.sleep(self.default_sleep)
                continue

            if isinstance(task_data, list):
                raise ValueError("Неизвестный формат данных задачи.")

            task_name, uuid, priority = task_data.split(":")
            uuid = UUID(uuid, version=4)
            priority = int(priority)

            await self.storage.add_process(task_data, priority)

            model_get = await self.get(uuid=uuid)
            if not model_get:
                raise KeyError(f"Задача не найдена: {uuid}")

            args, kwargs, created_at = (
                model_get.args or (),
                model_get.kwargs or {},
                model_get.created_at.timestamp(),
            )
            if self.log:
                self.log.info(f"Получена новая задача: {uuid}")
            new_args = await self._plugin_trigger(
                "broker_add_worker",
                broker=self,
                worker=worker,
                task_name=task_name,
                uuid=uuid,
                priority=priority,
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
        return

    async def add(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    Имя задачи.
                    """
            ),
        ],
        priority: Annotated[
            int,
            Doc(
                """
                    Приоритет задачи.

                    По умолчанию: `0`.
                    """
            ),
        ] = 0,
        extra: Annotated[
            dict | None,
            Doc(
                """
                    Дополнительные параметры задачи.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        args: Annotated[
            tuple | None,
            Doc(
                """
                    Аргументы задачи типа args.

                    По умолчанию: `()`.
                    """
            ),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc(
                """
                    Аргументы задачи типа kwargs.

                    По умолчанию: `{}`.
                    """
            ),
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
                    ValueError: Incorrect task status.
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
            args=json.dumps(args),
            kwargs=json.dumps(kwargs),
        )

        if extra:
            model = self._dynamic_model(model=model, extra=extra)

        new_model = await self._plugin_trigger(
            "broker_add_before", broker=self, storage=self.storage, model=model
        )
        if new_model:
            model = new_model.get("model", model)

        if not isinstance(model, TaskStatusNewSchema):
            raise ValueError("Некорректный статус задачи.")

        await self.storage.add(uuid=uuid, task_status=model)

        raw = self.client.rpush(self.queue_name, f"{task_name}:{uuid_str}:{priority}")
        await cast(Awaitable[int], raw)

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
            Doc(
                """
                    UUID задачи.
                    """
            ),
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
            Doc(
                """
                    Аргументы обновления для хранилища типа kwargs.
                    """
            ),
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
            Doc(
                """
                    Класс Воркера.
                    """
            ),
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
        await self.client.aclose()

    async def remove_finished_task(
        self,
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc(
                """
                    Схема приоритетной задачи.
                    """
            ),
        ],
        model: Annotated[
            TaskStatusSuccessSchema | TaskStatusErrorSchema,
            Doc(
                """
                    Модель результата задачи.
                    """
            ),
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

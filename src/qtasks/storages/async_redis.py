"""Async Redis storage."""
from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional, Union, cast
from uuid import UUID

import asyncio_atexit
import redis.asyncio as aioredis
from typing_extensions import Doc

from qtasks.configs.async_redisglobalconfig import AsyncRedisGlobalConfig
from qtasks.configs.config import QueueConfig
from qtasks.contrib.redis.async_queue_client import AsyncRedisCommandQueue
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.async_events import AsyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import (
    TaskStatusCancelSchema,
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusSuccessSchema,
)

from .base import BaseStorage

if TYPE_CHECKING:
    from qtasks.configs.base import BaseGlobalConfig
    from qtasks.events.base import BaseEvents
    from qtasks.schemas.task import Task
    from qtasks.workers.base import BaseWorker


class AsyncRedisStorage(BaseStorage, AsyncPluginMixin):
    """
    A repository that works with Redis, storing information about tasks.
    
        ## Example
    
        ```python
        from qtasks import QueueTasks
        from qtasks.brokers import AsyncRedisBroker
        from qtasks.storages import AsyncRedisStorage
    
        storage = AsyncRedisStorage(name="QueueTasks")
        broker = AsyncRedisBroker(name="QueueTasks", storage=storage)
    
        app = QueueTasks(broker=broker)
        ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Имя проекта. Это имя также используется Хранилищем.

                    По умолчанию: `QueueTasks`.
                    """
            ),
        ] = "QueueTasks",
        url: Annotated[
            str,
            Doc(
                """
                    URL для подключения к Redis.

                    По умолчанию: `redis://localhost:6379/0`.
                    """
            ),
        ] = "redis://localhost:6379/0",
        queue_process: Annotated[
            str,
            Doc(
                """
                    Имя канала для задач в процессе.

                    По умолчанию: `task_process`.
                    """
            ),
        ] = "task_process",
        redis_connect: Annotated[
            aioredis.Redis | None,
            Doc(
                """
                    Внешний класс подключения к Redis.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        global_config: Annotated[
            Optional[BaseGlobalConfig],
            Doc(
                """
                    Глобальный конфиг.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
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
        Initializing an asynchronous Redis storage.
        
                Args:
                    name (str, optional): Project name. Default: "QueueTasks".
                    url (str, optional): URL to connect to Redis. Default: "redis://localhost:6379/0".
                    queue_process (str, optional): Channel name for tasks in the process. Default: "task_process".
                    redis_connect (aioredis.Redis, optional): External Redis connection class. Default: None.
                    global_config (BaseGlobalConfig, optional): Global config. Default: None.
                    log (Logger, optional): Logger. Default: `qtasks.logs.Logger`.
                    config (QueueConfig, optional): Config. Default: `qtasks.configs.config.QueueConfig`.
                    events (BaseEvents, optional): Events. Default: `qtasks.events.AsyncEvents`.
        """
        self.url = url
        super().__init__(name, log=log, config=config, events=events)
        self._queue_process = queue_process
        self.queue_process = f"{self.name}:{queue_process}"
        self.events = self.events or AsyncEvents()

        self.client = redis_connect or aioredis.from_url(
            self.url, decode_responses=True, encoding="utf-8"
        )
        self.redis_contrib = AsyncRedisCommandQueue(redis=self.client, log=self.log)

        self.global_config: BaseGlobalConfig[Literal[True]] = (
            global_config
            or AsyncRedisGlobalConfig(
                name=self.name,
                redis_connect=self.client,
                log=self.log,
                config=self.config,
            )
        )

    async def add(
        self,
        uuid: Annotated[
            UUID | str,
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
        task_status: Annotated[
            TaskStatusNewSchema,
            Doc(
                """
                    Схема статуса новой задачи.
                    """
            ),
        ],
    ) -> None:
        """
        Adding a task to the repository.
        
                Args:
                    uuid (UUID | str): UUID of the task.
                    task_status (TaskStatusNewSchema): The new task's status schema.
        """
        uuid = str(uuid)

        new_data = await self._plugin_trigger(
            "storage_add",
            storage=self,
            uuid=uuid,
            task_status=task_status,
            return_last=True,
        )
        if new_data:
            uuid = new_data.get("uuid", uuid)
            task_status = new_data.get("task_status", task_status)

        raw = self.client.hset(f"{self.name}:{uuid}", mapping=task_status.__dict__)
        await cast(Awaitable[int], raw)
        return

    async def get(self, uuid: UUID | str) -> Union[Task, None]:
        """
        Obtaining information about a task.
        
                Args:
                    uuid (UUID|str): UUID of the task.
        
                Returns:
                    Task|None: If there is task information, returns `schemas.task.Task`, otherwise `None`.
        """
        loop = asyncio.get_running_loop()
        asyncio_atexit.register(self.stop, loop=loop)

        key = f"{self.name}:{uuid}"
        raw = self.client.hgetall(key)
        result = await cast(Awaitable[dict], raw)
        if not result:
            return None

        result = self._build_task(uuid=uuid, result=result)
        new_result = await self._plugin_trigger(
            "storage_get", storage=self, result=result, return_last=True
        )
        if new_result:
            result = new_result.get("result", result)
        return result

    async def get_all(self) -> list[Task]:
        """
        Get all tasks.
        
                Returns:
                    List[Task]: Array of tasks.
        """
        pattern = f"{self.name}:*"

        results: list[Task] = []
        async for key in self.client.scan_iter(pattern):
            name, uuid, *_ = key.split(":")
            if uuid in [self._queue_process, "task_queue"]:
                continue
            if (
                self.global_config
                and self.global_config.config_name is not None
                and f"{name}:{uuid}".find(self.global_config.config_name) != -1
            ):
                continue

            task = await self.get(uuid=uuid)
            if not task:
                continue

            results.append(task)

        new_results = await self._plugin_trigger(
            "storage_get_all", storage=self, results=results, return_last=True
        )
        if new_results:
            results = new_results.get("results", results)

        return results

    async def update(
        self,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Аргументы обновления типа kwargs.
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
            "storage_update", storage=self, kw=kwargs, return_last=True
        )
        if new_kw:
            kwargs = new_kw.get("kw", kwargs)
        return await self.redis_contrib.execute(
            "hset", kwargs["name"], mapping=kwargs["mapping"]
        )

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
            TaskStatusSuccessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema,
            Doc(
                """
                    Модель результата задачи.
                    """
            ),
        ],
    ) -> None:
        """
        Updates data for a completed task.
        
                Args:
                    task_broker (TaskPrioritySchema): The priority task schema.
                    model (TaskStatusSuccessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema): Model of the task result.
        """
        if isinstance(model, TaskStatusSuccessSchema) and not isinstance(
            model.returning, (bytes, str, int, float)
        ):
            trace = "Invalid input of type: 'NoneType'. Convert to a bytes, string, int or float first."
            model = TaskStatusErrorSchema(
                task_name=task_broker.name,
                priority=task_broker.priority,
                traceback=trace,
                created_at=task_broker.created_at,
                updated_at=time.time(),
            )
            if self.log:
                self.log.error(
                    f"Задача {task_broker.uuid} завершена с ошибкой:\n{trace}"
                )
        await self.redis_contrib.execute(
            "hset", f"{self.name}:{task_broker.uuid}", mapping=model.__dict__
        )
        await self.redis_contrib.execute(
            "zrem",
            self.queue_process,
            f"{task_broker.name}:{task_broker.uuid}:{task_broker.priority}",
        )

        await self._plugin_trigger(
            "storage_remove_finished_task",
            storage=self,
            task_broker=task_broker,
            model=model,
        )
        return

    async def start(self):
        """Starts the repository."""
        await self._plugin_trigger("storage_start", storage=self)
        if self.global_config:
            await self.global_config.start()

    async def stop(self):
        """Stops storage."""
        await self._plugin_trigger("storage_stop", storage=self)
        return await self.client.aclose()

    async def add_process(
        self,
        task_data: Annotated[
            str,
            Doc(
                """
                    Данные задачи из брокера.
                    """
            ),
        ],
        priority: Annotated[
            int,
            Doc(
                """
                    Приоритет задачи.
                    """
            ),
        ],
    ) -> None:
        """
        Adds a task to the list of tasks in a process.
        
                Args:
                    task_data (str): Task data from the broker.
                    priority (int): Task priority.
        """
        new_data = await self._plugin_trigger(
            "storage_add_process", storage=self, return_last=True
        )
        if new_data:
            task_data = new_data.get("task_data", task_data)
            priority = new_data.get("priority", priority)
        await self.client.zadd(self.queue_process, {task_data: priority})
        return

    async def _running_older_tasks(self, worker: BaseWorker[Literal[True]]):
        tasks = await self.client.zrange(self.queue_process, 0, -1)
        for task_data in tasks:
            task_name, uuid, priority = task_data.split(":")
            name_ = f"{self.name}:{uuid}"
            raw = self.client.hmget(name_, ["args", "kwargs", "created_at"])
            args, kwargs, created_at = await cast(Awaitable[list], raw)
            args, kwargs, created_at = (
                json.loads(args) or (),
                json.loads(kwargs) or {},
                float(created_at),
            )
            new_data = await self._plugin_trigger(
                "storage_running_older_tasks",
                storage=self,
                worker=worker,
                return_last=True,
            )
            if new_data:
                task_name = new_data.get("task_name", task_name)
                uuid = new_data.get("uuid", uuid)
                priority = new_data.get("priority", priority)
                created_at = new_data.get("created_at", created_at)
                args = new_data.get("args", args)
                kwargs = new_data.get("kw", kwargs)
            await worker.add(
                name=task_name,
                uuid=uuid,
                priority=int(priority),
                created_at=created_at,
                args=args,
                kwargs=kwargs,
            )
        return

    async def _delete_finished_tasks(self):
        await self._plugin_trigger("storage_delete_finished_tasks", storage=self)
        pattern = f"{self.name}:"
        try:
            tasks: list[Task] = list(
                filter(
                    lambda task: task.status != TaskStatusEnum.NEW.value,
                    await self.get_all(),
                )
            )

            tasks_hash = [pattern + str(task.uuid) for task in tasks]
            tasks_queue = [
                f"{task.task_name}:{task.uuid}:{task.priority}" for task in tasks
            ]

            if tasks_queue:
                await self.client.zrem(self.queue_process, *tasks_queue)
            if tasks_hash:
                await self.client.delete(*tasks_hash)
        except BaseException:
            pass
        return

    async def flush_all(self) -> None:
        """Delete all data."""
        loop = asyncio.get_running_loop()
        asyncio_atexit.register(self.stop, loop=loop)

        await self._plugin_trigger("storage_flush_all", storage=self)

        pipe = self.client.pipeline()

        pattern = f"{self.name}:*"
        async for key in self.client.scan_iter(pattern):
            await self.client.delete(key)
        await pipe.execute()
        return

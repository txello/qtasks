import asyncio
import asyncio_atexit
import datetime
import json
from typing import Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID
import redis.asyncio as aioredis
from typing import TYPE_CHECKING

from qtasks.contrlib.redis.async_queue_client import AsyncRedisCommandQueue
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger

from .base import BaseStorage
from qtasks.configs.async_redisglobalconfig import AsyncRedisGlobalConfig
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusErrorSchema, TaskStatusNewSchema
from qtasks.schemas.task import Task

if TYPE_CHECKING:
    from qtasks.configs.base import BaseGlobalConfig
    from qtasks.workers.base import BaseWorker

class AsyncRedisStorage(BaseStorage):
    """
    Хранилище, работающий с Redis, сохраняя информацию о задачах.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import AsyncRedisBroker
    from qtasks.storages import AsyncRedisStorage
    
    storage = AsyncRedisBroker(name="QueueTasks")
    broker = AsyncRedisBroker(name="QueueTasks", storage=storage)
    
    app = QueueTasks(broker=broker)
    ```
    """
    
    def __init__(self,
            name: Annotated[
                str,
                Doc(
                    """
                    Имя проекта. Это имя также используется Хранилищем.
                    
                    По умолчанию: `QueueTasks`.
                    """
                )
            ] = "QueueTasks",
            url: Annotated[
                str,
                Doc(
                    """
                    URL для подключения к Redis.
                    
                    По умолчанию: `redis://localhost:6379/0`.
                    """
                )
            ] = "redis://localhost:6379/0",
            queue_process: Annotated[
                str,
                Doc(
                    """
                    Имя канала для задач в процессе.
                    
                    По умолчанию: `task_process`.
                    """
                )
            ] = "task_process",
            redis_connect: Annotated[
                Optional[aioredis.Redis],
                Doc(
                    """
                    Внешний класс подключения к Redis.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            global_config: Annotated[
                Optional["BaseGlobalConfig"],
                Doc(
                    """
                    Глобальный конфиг.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,

            log: Annotated[
                Optional[Logger],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.logs.Logger`.
                    """
                )
            ] = None
        ):
        super().__init__(name, log=log)
        self.url = url
        self._queue_process = queue_process
        self.queue_process = f"{self.name}:{queue_process}"
        self.client = redis_connect or aioredis.from_url(self.url, decode_responses=True, encoding=u'utf-8')
        self.redis_contrlib = AsyncRedisCommandQueue(redis=self.client, log=self.log)
        
        self.global_config = global_config or AsyncRedisGlobalConfig(name=self.name, redis_connect=self.client, log=self.log)
        
    async def add(self,
            uuid: Annotated[
                Union[UUID|str],
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ],
            task_status: Annotated[
                TaskStatusNewSchema,
                Doc(
                    """
                    Схема статуса новой задачи.
                    """
                )
            ]
        ) -> None:
        """Добавление задачи в хранилище.

        Args:
            uuid (UUID | str): UUID задачи.
            task_status (TaskStatusNewSchema): Схема статуса новой задачи.
        """
        
        uuid = str(uuid)
        await self.client.hset(f"{self.name}:{uuid}", mapping=task_status.__dict__)
        return
    
    async def get(self,
            uuid: UUID|str
        ) -> Task|None:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        loop = asyncio.get_running_loop()
        asyncio_atexit.register(self.stop, loop=loop)
        
        key = f"{self.name}:{uuid}"
        result = await self.client.hgetall(key)
        if not result:
            return None
        
        return Task(
            status=result["status"],
            uuid=uuid,
            priority=int(result["priority"]),
            task_name=result["task_name"],
            
            args=json.loads(result["args"]),
            kwargs=json.loads(result["kwargs"]),
            
            returning=json.loads(result["returning"]) if "returning" in result else None,
            traceback=str(result["traceback"]) if "traceback" in result else None,
            created_at=datetime.datetime.fromtimestamp(float(result["created_at"])),
            updated_at=datetime.datetime.fromtimestamp(float(result["updated_at"]))
        )
    
    async def get_all(self) -> list[Task]:
        """Получить все задачи.

        Returns:
            list[Task]: Массив задач.
        """
        pattern = f"{self.name}:*"
        
        result: list[Task] = []
        async for key in self.client.scan_iter(pattern):
            name, uuid, *_ = key.split(":")
            if uuid in [self._queue_process, "task_queue"]:
                continue
            if f"{name}:{uuid}".find(self.global_config.config_name) != -1:
                continue
            
            task = await self.get(uuid=uuid)
            result.append(task)
        
        return result
    
    async def update(self,
            **kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы обновления типа kwargs.
                    """
                )
            ]
        ) -> None:
        """Обновляет информацию о задаче.
        
        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
        """
        return await self.redis_contrlib.execute("hset", kwargs["name"], mapping=kwargs["mapping"])
        
    async def remove_finished_task(self,
            task_broker: Annotated[
                TaskPrioritySchema,
                Doc(
                    """
                    Схема приоритетной задачи.
                    """
                )
            ],
            model: Annotated[
                Union[TaskStatusNewSchema|TaskStatusErrorSchema],
                Doc(
                    """
                    Модель результата задачи.
                    """
                )
            ]
        ) -> None:
        """Обновляет данные задачи.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        await self.client.hset(f"{self.name}:{task_broker.uuid}", mapping=model.__dict__)
        await self.client.zrem(self.queue_process, f"{task_broker.name}:{task_broker.uuid}:{task_broker.priority}")
        return
    
    async def start(self):
        """Запускает хранилище."""
        if self.global_config:
            await self.global_config.start()
    
    async def stop(self):
        """Останавливает хранилище."""
        return await self.client.close()
    
    async def add_process(self,
            task_data: Annotated[
                str,
                Doc(
                    """
                    Данные задачи из брокера.
                    """
                )
            ],
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    """
                )
            ]
        ) -> None:
        """Добавляет задачу в список задач в процессе.

        Args:
            task_data (str): Данные задачи из брокера.
            priority (int): Приоритет задачи.
        """
        await self.client.zadd(self.queue_process, {task_data: priority})
        return
    
    async def _running_older_tasks(self, worker:"BaseWorker"):
        tasks = await self.client.zrange(self.queue_process, 0, -1)
        for task_data in tasks:
            task_name, uuid, priority = task_data.split(':')
            name_ = f"{self.name}:{uuid}"
            args, kwargs, created_at = await self.client.hget(name_, "args"), await self.client.hget(name_, "kwargs"), await self.client.hget(name_, "created_at")
            args, kwargs, created_at = json.loads(args) or (), json.loads(kwargs) or {}, float(created_at)
            
            await worker.add(name=task_name, uuid=uuid, priority=int(priority), created_at=created_at, args=args, kwargs=kwargs)
        return

    async def _delete_finished_tasks(self):
        pattern = f"{self.name}:"
        tasks: list[Task] = list(filter(lambda task: task.status != TaskStatusEnum.NEW.value, await self.get_all()))
        
        tasks_hash = [pattern + str(task.uuid) for task in tasks]
        tasks_queue = [f"{task.task_name}:{task.uuid}:{task.priority}" for task in tasks]
        
        if tasks_queue:
            await self.client.zrem(self.queue_process, *tasks_queue)
        if tasks_hash:
            await self.client.delete(*tasks_hash)
        return

import asyncio
from dataclasses import asdict, field, fields, make_dataclass
import datetime
import asyncio_atexit
from typing import Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID, uuid4
from time import time
from typing import TYPE_CHECKING
import redis.asyncio as aioredis

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.storages.async_redis import AsyncRedisStorage

if TYPE_CHECKING:
    from qtasks.workers.base import BaseWorker
    from qtasks.storages.base import BaseStorage

from .base import BaseBroker
from qtasks.schemas.task import Task
from qtasks.schemas.task_status import TaskStatusCancelSchema, TaskStatusErrorSchema, TaskStatusNewSchema, TaskStatusProcessSchema
from qtasks.storages import AsyncRedisStorage

class AsyncRedisBroker(BaseBroker):
    """
    Брокер, слушающий Redis и добавляющий задачи в очередь.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import AsyncRedisBroker
    
    broker = AsyncRedisBroker(name="QueueTasks", url="redis://localhost:6379/2")
    
    app = QueueTasks(broker=broker)
    ```
    """
    
    def __init__(self,
            name: Annotated[
                str,
                Doc(
                    """
                    Имя проекта. Это имя также используется брокером.
                    
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
            ] = None,
            storage: Annotated[
                Optional["BaseStorage"],
                Doc(
                    """
                    Хранилище.
                    
                    По умолчанию: `AsyncRedisStorage`.
                    """
                )
            ] = None,
            queue_name: Annotated[
                str,
                Doc(
                    """
                    Имя массива очереди задач для Redis. Название обновляется на: `name:queue_name`.
                    
                    По умолчанию: `task_queue`.
                    """
                )
            ] = "task_queue",

            log: Annotated[
                Optional[Logger],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.logs.Logger`.
                    """
                )
            ] = None,
            config: Annotated[
                Optional[QueueConfig],
                Doc(
                    """
                    Конфиг.
                    
                    По умолчанию: `qtasks.configs.config.QueueConfig`.
                    """
                )
            ] = None
        ):
        super().__init__(name=name, log=log, config=config)
        self.url = url or "redis://localhost:6379/0"
        self.queue_name = f"{self.name}:{queue_name}"
        
        self.client = aioredis.ConnectionPool.from_url(self.url, decode_responses=True, encoding=u'utf-8')
        self.client = aioredis.Redis.from_pool(self.client)
        self.storage = storage or AsyncRedisStorage(name=name, url=self.url, redis_connect=self.client, log=self.log, config=self.config)
        self.running = False
        self.default_sleep = 0.01

    async def listen(self,
            worker: Annotated[
                "BaseWorker",
                Doc(
                    """
                    Класс воркера.
                    """
                )
            ]
        ):
        """Слушает очередь Redis и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        self.running = True

        while self.running:
            task_data = await self.client.lpop(self.queue_name)
            if not task_data:
                await asyncio.sleep(self.default_sleep)
                continue
            
            task_name, uuid, priority = task_data.split(':')
            
            await self.storage.add_process(task_data, priority)
            
            model_get = await self.get(uuid=uuid)
            args, kwargs, created_at = model_get.args or (), model_get.kwargs or {}, model_get.created_at.timestamp()
            self.log.info(f"Получена новая задача: {uuid}")
            await worker.add(name=task_name, uuid=uuid, priority=int(priority), args=args, kwargs=kwargs, created_at=created_at)  # Передаём задачу в AsyncWorker
                
                
    async def add(self,
            task_name: Annotated[
                str,
                Doc(
                    """
                    Имя задачи.
                    """
                )
            ],
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    
                    По умолчанию: `0`.
                    """
                )
            ] = 0,

            extra: dict = None,

            args: Annotated[
                tuple,
                Doc(
                    """
                    Аргументы задачи типа args.
                    """
                )
            ] = None,
            kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы задачи типа kwargs.
                    """
                )
            ] = None
        ) -> Task:
        """Добавляет задачу в брокер.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умоланию: 0.
            extra (dict, optional): Дополнительные параметры задачи.
            args (tuple, optional): Аргументы задачи типа args.
            kwargs (dict, optional): Аргументы задачи типа kwargs.

        Returns:
            Task: `schemas.task.Task`
        """
        loop = asyncio.get_running_loop()
        asyncio_atexit.register(self.stop, loop=loop)
        asyncio_atexit.register(self.storage.stop, loop=loop)
        
        
        args, kwargs = args or (), kwargs or {}
        uuid = str(uuid4())
        created_at = time()
        model = TaskStatusNewSchema(task_name=task_name, priority=priority, created_at=created_at, updated_at=created_at)
        model.set_json(args, kwargs)

        if extra:
            model = self._dynamic_model(model=model, extra=extra)
        
        await self.storage.add(uuid=uuid, task_status=model)
        await self.client.rpush(self.queue_name, f"{task_name}:{uuid}:{priority}")
        
        model = Task(status=TaskStatusEnum.NEW.value, task_name=task_name, uuid=uuid, priority=priority, args=args, kwargs=kwargs, created_at=created_at, updated_at=created_at)
        return model
    
    async def get(self,
            uuid: Annotated[
                Union[UUID|str],
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ]
        ) -> Task|None:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        if isinstance(uuid, str): uuid = UUID(uuid)
        return await self.storage.get(uuid=uuid)
    
    async def update(self,
            **kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы обновления для хранилища типа kwargs.
                    """
                )
            ]
        ) -> None:
        """Обновляет информацию о задаче.
        
        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
        """
        return await self.storage.update(**kwargs)
    
    async def start(self,
            worker: Annotated[
                "BaseWorker",
                Doc(
                    """
                    Класс Воркера.
                    """
                )
            ]
        ) -> None:
        """Запускает брокер.

        Args:
            worker (BaseWorker): Класс Воркера.
        """
        await self.storage.start()

        if self.config.delete_finished_tasks:
            await self.storage._delete_finished_tasks()
        
        if self.config.running_older_tasks:
            await self.storage._running_older_tasks(worker)
        
        await self.listen(worker)

    async def stop(self):
        """Останавливает брокер."""
        self.running = False
        await self.client.aclose()

    
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
                Union[TaskStatusProcessSchema|TaskStatusErrorSchema|TaskStatusCancelSchema],
                Doc(
                    """
                    Модель результата задачи.
                    """
                )
            ]
        ) -> None:
        """Обновляет данные хранилища через функцию `self.storage.remove_finished_task`.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        await self.storage.remove_finished_task(task_broker, model)
        return
    
    async def _plugin_trigger(self, name: str, *args, **kwargs):
        """
        Вызвать триггер плагина.

        Args:
            name (str): Имя триггера.
            *args: Позиционные аргументы для триггера.
            **kwargs: Именованные аргументы для триггера.
        """
        results = []
        for plugin in self.plugins.get(name, []) + self.plugins.get("Globals", []):
            result = await plugin.trigger(name=name, *args, **kwargs)
            if result is not None:
                results.append(result)
        return results

    async def flush_all(self) -> None:
        """Удалить все данные."""
        await self.storage.flush_all()
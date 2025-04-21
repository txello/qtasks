try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
except ImportError:
    raise ImportError("Install with `pip install qtasks[kafka]` to use this broker.")

import asyncio
from typing import Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID, uuid4
from time import time
from typing import TYPE_CHECKING

from qtasks.enums.task_status import TaskStatusEnum

from .base import BaseBroker
from qtasks.schemas.task_exec import TaskPrioritySchema

if TYPE_CHECKING:
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker

from qtasks.schemas.task import Task
from qtasks.schemas.task_status import TaskStatusErrorSchema, TaskStatusNewSchema

class AsyncKafkaBroker(BaseBroker):
    """
    Брокер, слушающий Kafka и добавляющий задачи в очередь.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import AsyncKafkaBroker
    
    broker = AsyncKafkaBroker(name="QueueTasks", url="localhost:9092")
    
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
                    URL для подключения к Kafka.
                    
                    По умолчанию: `localhost:9092`.
                    """
                )
            ] = "localhost:9092",
            storage: Annotated[
                Optional["BaseStorage"],
                Doc(
                    """
                    Хранилище.
                    
                    По умолчанию: `AsyncRedisStorage`.
                    """
                )
            ] = None,
            topic: Annotated[
                str,
                Doc(
                    """
                    Топик Kafka.
                    
                    По умолчанию: `task_queue`.
                    """
                )
            ] = "task_queue"
        ):
        super().__init__(name=name, storage=storage)
        self.url = url
        self.topic = f"{self.name}_{topic}"
        
        self.consumer = AIOKafkaConsumer(
            self.topic,
            loop=asyncio.get_event_loop(),
            bootstrap_servers=self.url,
            group_id=f"{self.name}_group"
        )
        self.producer = AIOKafkaProducer(
            loop=asyncio.get_event_loop(),
            bootstrap_servers=self.url
        )
        self.running = False
    
    async def listen(self, worker: "BaseWorker"):
        """Слушает Kafka и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        await self._consumer_start()
        self.running = True
        try:
            async for msg in self.consumer:
                task_data = msg.value.decode("utf-8")
                task_name, uuid, priority = task_data.split(":")
                model_get = await self.get(uuid=uuid)
                args, kwargs, created_at = model_get.args or (), model_get.kwargs or {}, model_get.created_at.timestamp()
                print(f"[Broker] Получена новая задача: {uuid}")
                await worker.add(name=task_name, uuid=uuid, priority=int(priority), args=args, kwargs=kwargs, created_at=created_at)
        finally:
            await self.consumer.stop()
    
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
            *args: Annotated[
                tuple,
                Doc(
                    """
                    Аргументы задачи типа args.
                    """
                )
            ],
            **kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы задачи типа kwargs.
                    """
                )
            ]
        ) -> Task:
        """Добавляет задачу в брокер.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умоланию: 0.
            args (tuple, optional): Аргументы задачи типа args.
            kwargs (dict, optional): Аргументы задачи типа kwargs.

        Returns:
            Task: `schemas.task.Task`
        """
        uuid = uuid4()
        created_at = time()
        model = TaskStatusNewSchema(task_name=task_name, priority=priority, created_at=created_at, updated_at=created_at)
        model.set_json(args, kwargs)
        await self.storage.add(uuid=uuid, task_status=model)
        
        task_data = f"{task_name}:{uuid}:{priority}"
        await self._producer_start()
        await self.producer.send_and_wait(self.topic, task_data.encode("utf-8"))
        await self.producer.stop()
        
        return Task(status=TaskStatusEnum.NEW.value, task_name=task_name, uuid=uuid, priority=priority, args=args, kwargs=kwargs, created_at=created_at, updated_at=created_at)
    
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
        if self.config.delete_finished_tasks:
            await self.storage._delete_finished_tasks()
        
        if self.config.running_older_tasks:
            await self.storage._running_older_tasks(worker)
        
        await self.storage.start()
        await self.listen(worker)
    
    async def stop(self):
        """Останавливает брокер."""
        self.running = False
        await self.consumer.stop()
        await self.producer.stop()
    
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
        """Обновляет данные хранилища через функцию `self.storage.remove_finished_task`.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        await self.storage.remove_finished_task(task_broker, model)
    
    async def _consumer_start(self):
        """Запускает Kafka Consumer."""
        loop = asyncio.get_running_loop()
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.url,
            loop=loop
        )
        await self.consumer.start()
        
    async def _producer_start(self):
        """Запускает Kafka Producer."""
        loop = asyncio.get_running_loop()
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.url,
            loop=loop,
        )
        await self.producer.start()
        
    async def _plugin_trigger(self, name: str, *args, **kwargs):
        """Триггер плагина

        Args:
            name (str): Имя триггера.
            args (tuple, optional): Аргументы триггера типа args.
            kwargs (dict, optional): Аргументы триггера типа kwargs.
        """
        for plugin in self.plugins.values():
            await plugin.trigger(name=name, *args, **kwargs)
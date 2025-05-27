import json
from typing import TYPE_CHECKING, Optional, Union

from qtasks.configs.config_observer import ConfigObserver
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger
from qtasks.schemas.task_exec import TaskPrioritySchema

try:
    import aio_pika
except ImportError:
    raise ImportError("Install with `pip install qtasks[rabbitmq]` to use this broker.")

from typing_extensions import Annotated, Doc
from uuid import UUID, uuid4
from time import time
from .base import BaseBroker
from qtasks.schemas.task import Task
from qtasks.schemas.task_status import TaskStatusErrorSchema, TaskStatusNewSchema, TaskStatusSuccessSchema
from qtasks.storages import AsyncRedisStorage

if TYPE_CHECKING:
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker

class AsyncRabbitMQBroker(BaseBroker):
    """
    Брокер, слушающий RabbitMQ и добавляющий задачи в очередь.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import AsyncRabbitMQBroker
    
    broker = AsyncRabbitMQBroker(name="QueueTasks", url="amqp://guest:guest@localhost/")
    
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
                    URL для подключения к RabbitMQ.
                    
                    По умолчанию: `amqp://guest:guest@localhost/`.
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
                    Имя очереди задач для RabbitMQ. Название обновляется на: `name:queue_name`
                    
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
                Optional[ConfigObserver],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.configs.config_observer.ConfigObserver`.
                    """
                )
            ] = None
        ):
        super().__init__(name=name, log=log)
        self.url = url or "amqp://guest:guest@localhost/"
        self.queue_name = f"{self.name}:{queue_name}"
        self.storage = storage or AsyncRedisStorage(name=self.name, log=self.log, config=self.config)
        
        self.connection = None
        self.channel = None
        self.running = False

    async def connect(self):
        """Подключение к RabbitMQ асинхронно."""
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        
        self.queue = await self.channel.declare_queue(self.queue_name, durable=True)

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
        """Слушает очередь RabbitMQ и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        if not self.channel:
            await self.connect()
        
        async with self.queue.iterator() as queue_iter:
            self.running = True
            async for message in queue_iter:
                async with message.process():
                    task_data = json.loads(message.body)
                    await self.storage.add_process(f'{task_data["task_name"]}:{task_data["uuid"]}:{task_data["priority"]}', task_data["priority"])
                    self.log.info(f"Получена новая задача: {task_data['uuid']}")
                    
                    await worker.add(
                        name=task_data["task_name"],
                        uuid=task_data["uuid"],
                        priority=task_data["priority"],
                        args=task_data["args"],
                        kwargs=task_data["kwargs"],
                        created_at=task_data["created_at"]
                    )
                if not self.running:
                    break

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
        if not self.channel:
            await self.connect()

        uuid = str(uuid4())
        created_at = time()
        model = TaskStatusNewSchema(task_name=task_name, priority=priority, created_at=created_at, updated_at=created_at)
        model.set_json(args, kwargs)
        
        await self.storage.add(uuid=uuid, task_status=model)
        
        task_data = {
            "uuid": uuid,
            "task_name": task_name,
            "priority": priority,
            "args": args,
            "kwargs": kwargs,
            "created_at": created_at
        }
        
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(task_data).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key=self.queue_name
        )
        
        
        return Task(
            status=TaskStatusEnum.NEW.value, task_name=task_name, uuid=uuid,
            priority=priority, args=args, kwargs=kwargs,
            created_at=created_at, updated_at=created_at
        )

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
        if self.connection:
            await self.connection.close()
            self.connection = None
            self.channel = None

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
                Union[TaskStatusSuccessSchema|TaskStatusErrorSchema],
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
        return await self.storage.remove_finished_task(task_broker, model)
    
    async def _running_older_tasks(self, worker):
        return await self.storage._running_older_tasks(worker)

    async def _plugin_trigger(self, name: str, *args, **kwargs):
        """Триггер плагина

        Args:
            name (str): Имя триггера.
            args (tuple, optional): Аргументы триггера типа args.
            kwargs (dict, optional): Аргументы триггера типа kwargs.
        """
        for plugin in self.plugins.values():
            await plugin.trigger(name=name, *args, **kwargs)
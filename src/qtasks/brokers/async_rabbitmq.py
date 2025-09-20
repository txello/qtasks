"""Async RabbitMQ Broker."""

import json
from typing import TYPE_CHECKING, Optional, Union

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.async_events import AsyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
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
from qtasks.schemas.task_status import (
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusSuccessSchema,
)
from qtasks.storages import AsyncRedisStorage

if TYPE_CHECKING:
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker
    from qtasks.events.base import BaseEvents


class AsyncRabbitMQBroker(BaseBroker, AsyncPluginMixin):
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
            str,
            Doc(
                """
                    URL для подключения к RabbitMQ.

                    По умолчанию: `amqp://guest:guest@localhost/`.
                    """
            ),
        ] = None,
        storage: Annotated[
            Optional["BaseStorage"],
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
                    Имя очереди задач для RabbitMQ. Название обновляется на: `name:queue_name`

                    По умолчанию: `task_queue`.
                    """
            ),
        ] = "task_queue",
        log: Annotated[
            Optional[Logger],
            Doc(
                """
                    Логгер.

                    По умолчанию: `qtasks.logs.Logger`.
                    """
            ),
        ] = None,
        config: Annotated[
            Optional[QueueConfig],
            Doc(
                """
                    Конфиг.

                    По умолчанию: `qtasks.configs.config.QueueConfig`.
                    """
            ),
        ] = None,
        events: Annotated[
            Optional["BaseEvents"],
            Doc(
                """
                    События.

                    По умолчанию: `qtasks.events.AsyncEvents`.
                    """
            ),
        ] = None,
    ):
        """Инициализация AsyncRabbitMQBroker.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "QueueTasks".
            url (str, optional): URL для подключения к RabbitMQ. По умолчанию: None.
            storage (BaseStorage, optional): Хранилище. По умолчанию: None.
            queue_name (str, optional): Имя очереди RabbitMQ. По умолчанию: "task_queue".
            log (Logger, optional): Логгер. По умолчанию: None.
            config (QueueConfig, optional): Конфиг. По умолчанию: None.
            events (BaseEvents, optional): События. По умолчанию: `qtasks.events.AsyncEvents`.
        """
        super().__init__(name=name, log=log, config=config, events=events)
        self.url = url or "amqp://guest:guest@localhost/"
        self.queue_name = f"{self.name}:{queue_name}"
        self.events = self.events or AsyncEvents()

        self.storage = storage or AsyncRedisStorage(
            name=self.name, log=self.log, config=self.config
        )

        self.connection = None
        self.channel = None
        self.running = False

    async def connect(self):
        """Подключение к RabbitMQ асинхронно."""
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        self.queue = await self.channel.declare_queue(self.queue_name, durable=True)

    async def listen(
        self,
        worker: Annotated[
            "BaseWorker",
            Doc(
                """
                    Класс воркера.
                    """
            ),
        ],
    ):
        """Слушает очередь RabbitMQ и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        await self._plugin_trigger("broker_listen_start", broker=self, worker=worker)
        if not self.channel:
            await self.connect()

        async with self.queue.iterator() as queue_iter:
            self.running = True
            async for message in queue_iter:
                async with message.process():
                    task_data = json.loads(message.body)
                    task_name, uuid, priority = task_data["task_name"], task_data["uuid"], task_data["priority"]
                    args, kwargs = task_data.get("args", ()), task_data.get("kwargs", {})
                    created_at = task_data.get("created_at", 0)

                    await self.storage.add_process(
                        f'{task_data["task_name"]}:{task_data["uuid"]}:{task_data["priority"]}',
                        task_data["priority"],
                    )
                    self.log.info(f"Получена новая задача: {task_data['uuid']}")
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
                        return_last=True
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
                        created_at=created_at
                    )
                if not self.running:
                    break

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
            dict,
            Doc(
                """
                    Дополнительные параметры задачи.
                    """
            ),
        ] = None,
        args: Annotated[
            tuple,
            Doc(
                """
                    Аргументы задачи типа args.
                    """
            ),
        ] = None,
        kwargs: Annotated[
            dict,
            Doc(
                """
                    Аргументы задачи типа kwargs.
                    """
            ),
        ] = None,
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
        args, kwargs = args or (), kwargs or {}
        if not self.channel:
            await self.connect()

        uuid = str(uuid4())
        created_at = time()

        model = TaskStatusNewSchema(
            task_name=task_name,
            priority=priority,
            created_at=created_at,
            updated_at=created_at,
            args=args,
            kwargs=kwargs
        )

        if extra:
            model = self._dynamic_model(model=model, extra=extra)

        new_model = await self._plugin_trigger(
            "broker_add_before",
            broker=self,
            storage=self.storage,
            model=model,
            return_last=True
        )
        if new_model:
            model = new_model.get("model", model)

        await self.storage.add(uuid=uuid, task_status=model)

        task_data = {
            "uuid": uuid,
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
            "broker_add_after",
            broker=self,
            storage=self.storage,
            model=model
        )

        return Task(
            status=TaskStatusEnum.NEW.value,
            task_name=task_name,
            uuid=uuid,
            priority=priority,
            args=args,
            kwargs=kwargs,
            created_at=created_at,
            updated_at=created_at,
        )

    async def get(
        self,
        uuid: Annotated[
            Union[UUID, str],
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
    ) -> Union[Task, None]:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        if isinstance(uuid, str):
            uuid = UUID(uuid)
        task = await self.storage.get(uuid=uuid)
        new_task = await self._plugin_trigger("broker_get", broker=self, task=task, return_last=True)
        if new_task:
            task = new_task.get("task", task)
        return task

    async def update(
        self,
        **kwargs: Annotated[
            dict,
            Doc(
                """
                    Аргументы обновления для хранилища типа kwargs.
                    """
            ),
        ],
    ) -> None:
        """Обновляет информацию о задаче.

        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
        """
        new_kw = await self._plugin_trigger("broker_update", broker=self, kw=kwargs, return_last=True)
        if new_kw:
            kwargs = new_kw.get("kw", kwargs)
        return await self.storage.update(**kwargs)

    async def start(
        self,
        worker: Annotated[
            "BaseWorker",
            Doc(
                """
                    Класс Воркера.
                    """
            ),
        ],
    ) -> None:
        """Запускает брокер.

        Args:
            worker (BaseWorker): Класс Воркера.
        """
        await self._plugin_trigger("broker_start", broker=self, worker=worker)
        await self.storage.start()

        if self.config.delete_finished_tasks:
            await self.storage._delete_finished_tasks()

        if self.config.running_older_tasks:
            await self.storage._running_older_tasks(worker)

        await self.listen(worker)

    async def stop(self):
        """Останавливает брокер."""
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
            Doc(
                """
                    Схема приоритетной задачи.
                    """
            ),
        ],
        model: Annotated[
            Union[TaskStatusSuccessSchema, TaskStatusErrorSchema],
            Doc(
                """
                    Модель результата задачи.
                    """
            ),
        ],
    ) -> None:
        """Обновляет данные хранилища через функцию `self.storage.remove_finished_task`.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        new_model = await self._plugin_trigger(
            "broker_remove_finished_task",
            broker=self,
            storage=self.storage,
            model=model,
            return_last=True
        )
        if new_model:
            model = new_model.get("model", model)

        return await self.storage.remove_finished_task(task_broker, model)

    async def _running_older_tasks(self, worker):
        await self._plugin_trigger("broker_running_older_tasks", broker=self, worker=worker)
        return await self.storage._running_older_tasks(worker)

    async def flush_all(self) -> None:
        """Удалить все данные."""
        await self._plugin_trigger("broker_flush_all", broker=self)
        await self.storage.flush_all()

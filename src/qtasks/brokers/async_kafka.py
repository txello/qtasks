"""Async Kafka Broker."""

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

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.storages.sync_redis import SyncRedisStorage

from .base import BaseBroker
from qtasks.schemas.task_exec import TaskPrioritySchema

if TYPE_CHECKING:
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker

from qtasks.schemas.task import Task
from qtasks.schemas.task_status import (
    TaskStatusCancelSchema,
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusProcessSchema,
)


class AsyncKafkaBroker(BaseBroker, AsyncPluginMixin):
    """
    Брокер, слушающий Kafka и добавляющий задачи в очередь.

    ## Пример

    ```python
    from qtasks.asyncio import QueueTasks
    from qtasks.brokers import AsyncKafkaBroker

    broker = AsyncKafkaBroker(name="QueueTasks", url="localhost:9092")

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
                    URL для подключения к Kafka.

                    По умолчанию: `localhost:9092`.
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
        topic: Annotated[
            str,
            Doc(
                """
                    Топик Kafka.

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
    ):
        """Инициализация AsyncKafkaBroker.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "QueueTasks".
            url (str, optional): URL для подключения к Kafka. По умолчанию: None.
            storage (BaseStorage, optional): Хранилище. По умолчанию: None.
            topic (str, optional): Топик Kafka. По умолчанию: "task_queue".
            log (Logger, optional): Логгер. По умолчанию: None.
            config (QueueConfig, optional): Конфиг. По умолчанию: None.
        """
        super().__init__(name=name, log=log, config=config)
        self.url = url or "localhost:9092"
        self.topic = f"{self.name}_{topic}"

        self.consumer = AIOKafkaConsumer(
            self.topic,
            loop=asyncio.get_event_loop(),
            bootstrap_servers=self.url,
            group_id=f"{self.name}_group",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: m.decode("utf-8"),
        )
        self.producer = AIOKafkaProducer(
            loop=asyncio.get_event_loop(),
            bootstrap_servers=self.url,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: m.decode("utf-8"),
        )

        self.storage = storage or SyncRedisStorage(
            name=self.name, log=self.log, config=config
        )

        self.running = False

    async def listen(self, worker: "BaseWorker"):
        """Слушает Kafka и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        await self._plugin_trigger("broker_listen_start", broker=self, worker=worker)
        await self._consumer_start()
        self.running = True
        try:
            async for msg in self.consumer:
                task_data = msg.value
                task_name, uuid, priority = task_data.split(":")
                model_get = await self.get(uuid=uuid)
                args, kwargs, created_at = (
                    model_get.args or (),
                    model_get.kwargs or {},
                    model_get.created_at.timestamp(),
                )
                self.log.info(f"Получена новая задача: {uuid}")
                new_args = await self._plugin_trigger(
                    "broker_add_worker",
                    broker=self,
                    worker=worker,

                    task_name=task_name,
                    uuid=uuid,
                    priority=int(priority),
                    args=args,
                    kwargs=kwargs,
                    created_at=created_at,
                    return_last=True
                )
                if new_args:
                    task_name = new_args.get("task_name", task_name)
                    uuid = new_args.get("uuid", uuid)
                    priority = new_args.get("priority", priority)
                    args = new_args.get("args", args)
                    kwargs = new_args.get("kwargs", kwargs)
                    created_at = new_args.get("created_at", created_at)

                await worker.add(
                    name=task_name,
                    uuid=uuid,
                    priority=int(priority),
                    args=args,
                    kwargs=kwargs,
                    created_at=created_at,
                )
        finally:
            await self.consumer.stop()

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

        uuid = str(uuid4())
        created_at = time()
        model = TaskStatusNewSchema(
            task_name=task_name,
            priority=priority,
            created_at=created_at,
            updated_at=created_at,
        )
        model.set_json(args, kwargs)

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
            model = new_model

        await self.storage.add(uuid=uuid, task_status=model)

        task_data = f"{task_name}:{uuid}:{priority}"
        await self._producer_start()
        await self.producer.send_and_wait(self.topic, task_data)
        await self.producer.stop()

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
            Union[UUID | str],
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
    ) -> Task | None:
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
            task = new_task
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
            kwargs = new_kw
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
        await self.consumer.stop()
        await self.producer.stop()

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
            Union[
                TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema
            ],
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
            model = new_model

        await self.storage.remove_finished_task(task_broker, model)

    async def _running_older_tasks(self, worker):
        await self._plugin_trigger("broker_running_older_tasks", broker=self, worker=worker)
        return await self.storage._running_older_tasks(worker)

    async def _consumer_start(self):
        """Запускает Kafka Consumer."""
        loop = asyncio.get_running_loop()
        self.consumer = AIOKafkaConsumer(
            self.topic, bootstrap_servers=self.url, loop=loop
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

    async def flush_all(self) -> None:
        """Удалить все данные."""
        await self._plugin_trigger("broker_flush_all", broker=self)
        await self.storage.flush_all()

"""Async Kafka Broker."""

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
except ImportError as exc:
    raise ImportError("Install with `pip install qtasks[kafka]` to use this broker.") from exc

import asyncio
from datetime import datetime
from time import time
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional
from uuid import UUID, uuid4

from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.async_events import AsyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.storages.sync_redis import SyncRedisStorage

from .base import BaseBroker

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker

from qtasks.schemas.task import Task
from qtasks.schemas.task_status import (
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusSuccessSchema,
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
        ] = "localhost:9092",
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
            Optional["BaseEvents"],
            Doc(
                """
                    События.

                    По умолчанию: `qtasks.events.AsyncEvents`.
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
            events (BaseEvents, optional): События. По умолчанию: `qtasks.events.AsyncEvents`.
        """
        self.url = url

        storage = storage or SyncRedisStorage(
            name=name, log=log, config=config, events=events
        )
        super().__init__(
            name=name, log=log, config=config, events=events, storage=storage
        )

        self.storage: BaseStorage[Literal[True]]

        self.topic = f"{self.name}_{topic}"
        self.events = self.events or AsyncEvents()

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

        self.running = False

    async def listen(
        self,
        worker: Annotated[
            "BaseWorker[Literal[True]]",
            Doc(
                """
                    Класс воркера.
                    """
            ),
        ],
    ):
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

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc(
                """
                    Аргументы задачи типа kwargs.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ) -> Task:
        """Добавляет задачу в брокер.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умоланию: 0.
            extra (dict, optional): Дополнительные параметры задачи. По умолчанию: `None`.
            args (tuple, optional): Аргументы задачи типа args. По умолчанию: `None`.
            kwargs (dict, optional): Аргументы задачи типа kwargs. По умолчанию: `None`.

        Returns:
            Task: `schemas.task.Task`
        """
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
            "broker_add_before",
            broker=self,
            storage=self.storage,
            model=model,
            return_last=True,
        )
        if new_model:
            model = new_model.get("model", model)

        await self.storage.add(uuid=uuid, task_status=model)

        task_data = f"{task_name}:{uuid_str}:{priority}"
        await self._producer_start()
        await self.producer.send_and_wait(self.topic, task_data)
        await self.producer.stop()

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
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
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
        """Обновляет информацию о задаче.

        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
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
            TaskStatusSuccessSchema | TaskStatusErrorSchema,
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
            model (TaskStatusSuccessSchema | TaskStatusErrorSchema): Модель результата задачи.
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

    async def _running_older_tasks(self, worker):
        await self._plugin_trigger(
            "broker_running_older_tasks", broker=self, worker=worker
        )
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

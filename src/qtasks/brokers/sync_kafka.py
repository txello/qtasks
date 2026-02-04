"""Sync Kafka Broker."""
from __future__ import annotations

try:
    from kafka import KafkaConsumer, KafkaProducer
except ImportError as exc:
    raise ImportError("Install with `pip install qtasks[kafka]` to use this broker.") from exc

from datetime import datetime
from time import time
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional
from uuid import UUID, uuid4

from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.sync_events import SyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin
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


class SyncKafkaBroker(BaseBroker, SyncPluginMixin):
    """
    A broker that listens to Kafka and adds tasks to the queue.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import SyncKafkaBroker

    broker = SyncKafkaBroker(name="QueueTasks", url="localhost:9092")

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
            Optional[BaseStorage],
            Doc(
                """
                    Хранилище.

                    По умолчанию: `SyncRedisStorage`.
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
            Optional[BaseEvents],
            Doc(
                """
                    События.

                    По умолчанию: `qtasks.events.SyncEvents`.
                    """
            ),
        ] = None,
    ):
        """
        Initializing SyncKafkaBroker.

        Args:
            name (str, optional): Project name. Default: `QueueTasks`.
            url (str, optional): URL to connect to Kafka. Default: `None`.
            storage (BaseStorage, optional): Storage. Default: `None`.
            topic (str, optional): Kafka topic. Default: `task_queue`.
            log (Logger, optional): Logger. Default: `None`.
            config (QueueConfig, optional): Config. Default: `None`.
            events (BaseEvents, optional): Events. Default: `qtasks.events.SyncEvents`.
        """
        self.url = url
        storage = storage or SyncRedisStorage(
            name=name, log=log, config=config, events=events
        )
        super().__init__(
            name=name, log=log, config=config, events=events, storage=storage
        )

        self.storage: BaseStorage[Literal[False]]

        self.events = self.events or SyncEvents()
        self.topic = f"{self.name}_{topic}"

        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.url,
            group_id=f"{self.name}_group",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: m.decode("utf-8"),
        )
        self.producer = KafkaProducer(
            bootstrap_servers=self.url,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: m.decode("utf-8"),
        )

        self.running = False

    def listen(
        self,
        worker: Annotated[
            BaseWorker[Literal[False]],
            Doc(
                """
                    Класс воркера.
                    """
            ),
        ],
    ):
        """
        Listens to Kafka and transfers tasks to the worker.

        Args:
            worker (BaseWorker): Worker class.
        """
        self._plugin_trigger("broker_listen_start", broker=self, worker=worker)
        self.running = True
        for msg in self.consumer:
            if not self.running:
                break
            task_data = msg.value
            task_name, uuid_str, priority = task_data.split(":")
            uuid = UUID(uuid_str)
            model_get = self.get(uuid=uuid)
            if model_get is None:
                if self.log:
                    self.log.warning(f"Задача {uuid} не найдена в хранилище.")
                continue
            args, kwargs, created_at = (
                model_get.args or (),
                model_get.kwargs or {},
                model_get.created_at.timestamp(),
            )
            if self.log:
                self.log.info(f"Получена новая задача: {uuid}")
            new_args = self._plugin_trigger(
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

            worker.add(
                name=task_name,
                uuid=uuid,
                priority=int(priority),
                args=args,
                kwargs=kwargs,
                created_at=created_at,
            )

    def add(
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
            priority (int, optional): Task priority. Default: `0`.
            extra (dict, optional): Additional task parameters. Default: `None`.
            args (tuple, optional): Task arguments of type args. Default: `()`.
            kwargs (dict, optional): Task arguments of type kwargs. Default: `{}`.

        Returns:
            Task: `schemas.task.Task`

        Raises:
            ValueError: Incorrect task status.
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

        new_model = self._plugin_trigger(
            "broker_add_before",
            broker=self,
            storage=self.storage,
            model=model,
            return_last=True,
        )
        if new_model:
            model = new_model.get("model", model)

        self.storage.add(uuid=uuid, task_status=model)

        task_data = f"{task_name}:{uuid_str}:{priority}"
        self.producer.send(self.topic, task_data)
        self.producer.flush()

        self._plugin_trigger(
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

    def get(
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
        task = self.storage.get(uuid=uuid)
        new_task = self._plugin_trigger(
            "broker_get", broker=self, task=task, return_last=True
        )
        if new_task:
            task = new_task.get("task", task)
        return task

    def update(
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
        new_kw = self._plugin_trigger(
            "broker_update", broker=self, kw=kwargs, return_last=True
        )
        if new_kw:
            kwargs = new_kw.get("kw", kwargs)
        return self.storage.update(**kwargs)

    def start(
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
        self._plugin_trigger("broker_start", broker=self, worker=worker)
        self.storage.start()

        if self.config.delete_finished_tasks:
            self.storage._delete_finished_tasks()

        if self.config.running_older_tasks:
            self.storage._running_older_tasks(worker)

        self.listen(worker)

    def stop(self):
        """The broker stops."""
        self._plugin_trigger("broker_stop", broker=self)
        self.running = False
        self.consumer.stop()
        self.producer.stop()

    def remove_finished_task(
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
        new_model = self._plugin_trigger(
            "broker_remove_finished_task",
            broker=self,
            storage=self.storage,
            model=model,
            return_last=True,
        )
        if new_model:
            model = new_model.get("model", model)

        self.storage.remove_finished_task(task_broker, model)

    def _running_older_tasks(self, worker):
        self._plugin_trigger("broker_running_older_tasks", broker=self, worker=worker)
        return self.storage._running_older_tasks(worker)

    def flush_all(self) -> None:
        """Delete all data."""
        self._plugin_trigger("broker_flush_all", broker=self)
        self.storage.flush_all()

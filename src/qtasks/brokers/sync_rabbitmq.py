"""Sync RabbitMQ Broker."""
from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Optional

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.sync_events import SyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.schemas.task_exec import TaskPrioritySchema

try:
    import pika
    from pika.adapters.blocking_connection import BlockingChannel
except ImportError as exc:
    raise ImportError("Install with `pip install qtasks[rabbitmq]` to use this broker.") from exc

from time import time
from typing import Annotated
from uuid import UUID, uuid4

from typing_extensions import Doc

from qtasks.schemas.task import Task
from qtasks.schemas.task_status import (
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusSuccessSchema,
)
from qtasks.storages import SyncRedisStorage

from .base import BaseBroker

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker


class SyncRabbitMQBroker(BaseBroker, SyncPluginMixin):
    """
    A broker that listens to RabbitMQ and adds tasks to the queue.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import SyncRabbitMQBroker

    broker = SyncRabbitMQBroker(name="QueueTasks", url="amqp://guest:guest@localhost/")

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
        ] = "amqp://guest:guest@localhost/",
        storage: Annotated[
            Optional[BaseStorage],
            Doc(
                """
                    Хранилище.

                    По умолчанию: `SyncRedisStorage`.
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
        Initializing SyncRabbitMQBroker.

        Args:
            name (str, optional): Project name. Default: `QueueTasks`.
            url (str, optional): URL to connect to RabbitMQ. Default: `None`.
            storage (BaseStorage, optional): Storage. Default: `None`.
            queue_name (str, optional): RabbitMQ queue name. Default: `task_queue`.
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

        self.queue_name = f"{self.name}:{queue_name}"
        self.events = self.events or SyncEvents()

        self.connection = None
        self.channel = None  # type: ignore
        self.running = False

    def connect(self):
        """Connection to RabbitMQ is synchronous."""
        self.connection = pika.BlockingConnection(pika.URLParameters(self.url))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

        self.queue = self.channel.queue_declare(self.queue_name, durable=True)

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
        Listens to the RabbitMQ queue and transfers tasks to the worker.

        Args:
            worker (BaseWorker): Worker class.
        """
        self._plugin_trigger("broker_listen_start", broker=self, worker=worker)
        if not self.channel:
            self.connect()

        def callback(ch, method, properties, body):
            task_data = json.loads(body)
            task_name, uuid, priority = (
                task_data["task_name"],
                task_data["uuid"],
                task_data["priority"],
            )
            args, kwargs = task_data.get("args", ()), task_data.get("kwargs", {})
            created_at = task_data.get("created_at", 0)

            self.storage.add_process(
                f'{task_data["task_name"]}:{task_data["uuid"]}:{task_data["priority"]}',
                task_data["priority"],
            )
            if self.log:
                self.log.info(f"Получена новая задача: {task_data['uuid']}")
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
                priority=priority,
                args=args,
                kwargs=kwargs,
                created_at=created_at,
            )

        if not isinstance(self.channel, BlockingChannel):
            raise RuntimeError("self.channel не объявлен. Сервер не запущен!")
        self.channel: BlockingChannel

        self.channel.basic_consume(
            queue=self.queue_name, on_message_callback=callback, auto_ack=True
        )
        self.running = True
        self.channel.start_consuming()

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
        """
        Adds a task to the broker.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. Default: `0`.
            extra (dict, optional): Additional task parameters. Default: `None`.
            args (tuple, optional): Task arguments of type args. Default: `None`.
            kwargs (dict, optional): Task arguments of type kwargs. Default: `None`.

        Returns:
            Task: `schemas.task.Task`

        Raises:
            RuntimeError: self.channel is not declared. The server is not running!
        """
        args, kwargs = args or (), kwargs or {}
        if not self.channel:
            self.connect()
        if not isinstance(self.channel, BlockingChannel):
            raise RuntimeError("self.channel не объявлен. Сервер не запущен!")
        self.channel: BlockingChannel

        uuid = uuid4()
        uuid_str = uuid
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

        task_data = {
            "uuid": uuid_str,
            "task_name": task_name,
            "priority": priority,
            "args": args,
            "kwargs": kwargs,
            "created_at": created_at,
        }

        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue_name,
            body=json.dumps(task_data).encode(),
            properties=pika.BasicProperties(
                delivery_mode=2,
            ),
        )

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
        if self.connection:
            self.connection.close()
            self.connection = None
            self.channel = None  # type: ignore
        self.storage.stop()

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

"""Sync RabbitMQ Broker."""

from datetime import datetime
import json
from typing import TYPE_CHECKING, Literal, Optional, Union


from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.sync_events import SyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.schemas.task_exec import TaskPrioritySchema

try:
    import pika
    from pika.adapters.blocking_connection import BlockingChannel
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
from qtasks.storages import SyncRedisStorage

if TYPE_CHECKING:
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker
    from qtasks.events.base import BaseEvents


class SyncRabbitMQBroker(BaseBroker, SyncPluginMixin):
    """
    Брокер, слушающий RabbitMQ и добавляющий задачи в очередь.

    ## Пример

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
            Optional["BaseStorage"],
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

                    По умолчанию: `qtasks.events.SyncEvents`.
                    """
            ),
        ] = None,
    ):
        """Инициализация SyncRabbitMQBroker.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "QueueTasks".
            url (str, optional): URL для подключения к RabbitMQ. По умолчанию: None.
            storage (BaseStorage, optional): Хранилище. По умолчанию: None.
            queue_name (str, optional): Имя очереди RabbitMQ. По умолчанию: "task_queue".
            log (Logger, optional): Логгер. По умолчанию: None.
            config (QueueConfig, optional): Конфиг. По умолчанию: None.
            events (BaseEvents, optional): События. По умолчанию: `qtasks.events.SyncEvents`.
        """
        self.url = url
        storage = storage or SyncRedisStorage(
            name=name, log=log, config=config, events=events
        )
        super().__init__(
            name=name, log=log, config=config, events=events, storage=storage
        )

        self.storage: "BaseStorage[Literal[False]]"

        self.queue_name = f"{self.name}:{queue_name}"
        self.events = self.events or SyncEvents()

        self.connection = None
        self.channel = None  # type: ignore
        self.running = False

    def connect(self):
        """Подключение к RabbitMQ синхронно."""
        self.connection = pika.BlockingConnection(pika.URLParameters(self.url))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

        self.queue = self.channel.queue_declare(self.queue_name, durable=True)

    def listen(
        self,
        worker: Annotated[
            "BaseWorker[Literal[False]]",
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
            Optional[dict],
            Doc(
                """
                    Дополнительные параметры задачи.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        args: Annotated[
            Optional[tuple],
            Doc(
                """
                    Аргументы задачи типа args.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        kwargs: Annotated[
            Optional[dict],
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
            priority (int, optional): Приоритет задачи. По умолчанию: `0`.
            extra (dict, optional): Дополнительные параметры задачи. По умолчанию: `None`.
            args (tuple, optional): Аргументы задачи типа args. По умолчанию: `None`.
            kwargs (dict, optional): Аргументы задачи типа kwargs. По умолчанию: `None`.

        Returns:
            Task: `schemas.task.Task`

        Raises:
            RuntimeError: self.channel не объявлен. Сервер не запущен!
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
        new_kw = self._plugin_trigger(
            "broker_update", broker=self, kw=kwargs, return_last=True
        )
        if new_kw:
            kwargs = new_kw.get("kw", kwargs)
        return self.storage.update(**kwargs)

    def start(
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
        self._plugin_trigger("broker_start", broker=self, worker=worker)
        self.storage.start()

        if self.config.delete_finished_tasks:
            self.storage._delete_finished_tasks()

        if self.config.running_older_tasks:
            self.storage._running_older_tasks(worker)

        self.listen(worker)

    def stop(self):
        """Останавливает брокер."""
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
            model (TaskStatusSuccessSchema | TaskStatusErrorSchema): Модель результата задачи.
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
        """Удалить все данные."""
        self._plugin_trigger("broker_flush_all", broker=self)
        self.storage.flush_all()

"""Sync Redis Broker."""

import redis
from typing import Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID, uuid4
from time import time, sleep
from typing import TYPE_CHECKING

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.storages import SyncRedisStorage

if TYPE_CHECKING:
    from qtasks.workers.base import BaseWorker
    from qtasks.storages.base import BaseStorage

from .base import BaseBroker
from qtasks.schemas.task import Task
from qtasks.schemas.task_status import (
    TaskStatusCancelSchema,
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusProcessSchema,
)


class SyncRedisBroker(BaseBroker, SyncPluginMixin):
    """
    Брокер, слушающий Redis и добавляющий задачи в очередь.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import SyncRedisBroker

    broker = SyncRedisBroker(name="QueueTasks", url="redis://localhost:6379/2")

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
                    URL для подключения к Redis.

                    По умолчанию: `redis://localhost:6379/0`.
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
                    Имя массива очереди задач для Redis. Название обновляется на: `name:queue_name`

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
        """Инициализация SyncRedisBroker.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "QueueTasks".
            url (str, optional): URL для подключения к Redis. По умолчанию: None.
            storage (BaseStorage, optional): Хранилище. По умолчанию: None.
            queue_name (str, optional): Имя массива очереди задач для Redis. По умолчанию: "task_queue".
            log (Logger, optional): Логгер. По умолчанию: None.
            config (QueueConfig, optional): Конфиг. По умолчанию: None.
        """
        super().__init__(name=name, log=log, config=config)
        self.url = url or "redis://localhost:6379/0"
        self.queue_name = f"{self.name}:{queue_name}"

        self.client = redis.Redis.from_url(
            self.url, decode_responses=True, encoding="utf-8"
        )
        self.storage = storage or SyncRedisStorage(
            name=name,
            url=self.url,
            redis_connect=self.client,
            log=self.log,
            config=self.config,
        )

        self.running = False
        self.default_sleep = 0.01

    def listen(
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
        """Слушает очередь Redis и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        self._plugin_trigger("broker_listen_start", broker=self, worker=worker)
        self.running = True

        while self.running:
            task_data = self.client.lpop(self.queue_name)
            if not task_data:
                sleep(self.default_sleep)
                continue

            task_name, uuid, priority = task_data.split(":")

            self.storage.add_process(task_data, priority)

            model_get = self.get(uuid=uuid)
            args, kwargs, created_at = (
                model_get.args or (),
                model_get.kwargs or {},
                model_get.created_at.timestamp(),
            )
            self.log.info(f"Получена новая задача: {uuid}")
            new_args = self._plugin_trigger(
                "broker_add_worker",
                broker=self,
                worker=worker,

                task_name=task_name,
                uuid=uuid,
                priority=int(priority),
                args=args,
                kwargs=kwargs,
                created_at=created_at
            )
            if new_args:
                new_args = new_args[-1]
                task_name = new_args.get("task_name", task_name)
                uuid = new_args.get("uuid", uuid)
                priority = new_args.get("priority", priority)
                args = new_args.get("args", args)
                kwargs = new_args.get("kwargs", kwargs)
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
        extra: dict = None,
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

        new_model = self._plugin_trigger(
            "broker_add_before",
            broker=self,
            storage=self.storage,
            model=model
        )
        if new_model:
            model = new_model[-1]

        self.storage.add(uuid=uuid, task_status=model)
        self.client.rpush(self.queue_name, f"{task_name}:{uuid}:{priority}")

        self._plugin_trigger(
            "broker_add_after",
            broker=self,
            storage=self.storage,
            model=model
        )

        model = Task(
            status=TaskStatusEnum.NEW.value,
            task_name=task_name,
            uuid=uuid,
            priority=priority,
            args=args,
            kwargs=kwargs,
            created_at=created_at,
            updated_at=created_at,
        )
        return model

    def get(
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
        task = self.storage.get(uuid=uuid)
        new_task = self._plugin_trigger("broker_get", broker=self, task=task)
        if new_task:
            task = new_task[-1]
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
        new_kw = self._plugin_trigger("broker_update", broker=self, kw=kwargs)
        if new_kw:
            kwargs = new_kw[-1]
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
        self.client.close()

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
        new_model = self._plugin_trigger(
            "broker_remove_finished_task",
            broker=self,
            storage=self.storage,
            model=model
        )
        if new_model:
            model = new_model[-1]

        self.storage.remove_finished_task(task_broker, model)

    def _running_older_tasks(self, worker):
        self._plugin_trigger("broker_running_older_tasks", broker=self, worker=worker)
        return self.storage._running_older_tasks(worker)

    def flush_all(self) -> None:
        """Удалить все данные."""
        self._plugin_trigger("broker_flush_all", broker=self)
        self.storage.flush_all()

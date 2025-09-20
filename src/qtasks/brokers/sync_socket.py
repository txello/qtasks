"""Sync Socket Broker."""

import contextlib
import socket
import threading
import json
import atexit
from queue import Queue, Empty
from dataclasses import asdict
from typing import Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID, uuid4
from time import time
from typing import TYPE_CHECKING


from .base import BaseBroker
from qtasks.events.sync_events import SyncEvents
from qtasks.storages.sync_redis import SyncRedisStorage
from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.schemas.task import Task
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import (
    TaskStatusCancelSchema,
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusProcessSchema,
)

if TYPE_CHECKING:
    from qtasks.workers.base import BaseWorker
    from qtasks.storages.base import BaseStorage
    from qtasks.events.base import BaseEvents


class SyncSocketBroker(BaseBroker, SyncPluginMixin):
    """
    Брокер, слушающий сокеты и добавляющий задачи в очередь.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import SyncSocketBroker

    broker = SyncSocketBroker(name="QueueTasks", url="127.0.0.1")

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
                    URL для подключения к сокету.

                    По умолчанию: `127.0.0.1`.
                    """
            ),
        ] = None,
        port: Annotated[
            int,
            Doc(
                """
                    Порт для подключения к сокету.

                    По умолчанию: `6379`.
                    """
            ),
        ] = 6379,
        storage: Annotated[
            Optional["BaseStorage"],
            Doc(
                """
                    Хранилище.

                    По умолчанию: `AsyncRedisStorage`.
                    """
            ),
        ] = None,
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
        """Инициализация SyncSocketBroker.

        Args:
            name (str, optional): Имя проекта. По умолчанию: `QueueTasks`.
            url (str, optional): URL для подключения к сокету. По умолчанию: `AsyncRedisStorage`.
            port (int, optional): Порт для подключения к сокету. По умолчанию: `8765`.
            storage (BaseStorage, optional): Хранилище. По умолчанию: `None`.
            log (Logger, optional): Логгер. По умолчанию: `None`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `None`.
            events (BaseEvents, optional): События. По умолчанию: `qtasks.events.AsyncEvents`.
        """
        super().__init__(name=name, log=log, config=config, events=events)
        self.url = url or "127.0.0.1"
        self.port = port
        self.events = self.events or SyncEvents()

        self.client = None
        self.storage = storage or SyncRedisStorage(
            name=name,
            log=self.log,
            config=self.config,
        )
        self.default_sleep = 0.01
        self.running = False

        self.queue = Queue()
        self._serve_task = None
        self._listen_task = None

    def handle_connection(self, reader, writer):
        """Обрабатывает входящее соединение.

        Args:
            reader: Читатель для входящих данных.
            writer: Писатель для исходящих данных.
        """
        conn = reader
        try:
            data = conn.recv(4096)
            if not data:
                return
            message = json.loads(data.decode())
            task_name = message["task_name"]
            uuid = message["uuid"]
            priority = message["priority"]
            args = message.get("args", ())
            kwargs = message.get("kwargs", {})
            created_at = message["created_at"]

            self.storage.add(
                uuid=uuid,
                task_status=TaskStatusNewSchema(
                    task_name=task_name,
                    priority=priority,
                    args=args,
                    kwargs=kwargs,
                    created_at=created_at,
                    updated_at=created_at,
                ),
            )

            self.queue.put((task_name, uuid, priority))
            conn.sendall(b"OK")
        finally:
            with contextlib.suppress(Exception):
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()

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
        """Слушает очередь сокета и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        self._plugin_trigger("broker_listen_start", broker=self, worker=worker)
        self.running = True

        while self.running:
            try:
                item = self.queue.get(timeout=0.1)
            except Empty:
                continue
            if item is None:
                break

            task_name, uuid, priority = item
            task_data = self.get(uuid)
            args, kwargs, created_at = task_data.args, task_data.kwargs, task_data.created_at

            self.storage.add_process(f"{task_name}:{uuid}:{priority}", priority)

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
        atexit.register(self.stop)
        atexit.register(self.storage.stop)

        args, kwargs = args or (), kwargs or {}
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

        new_model = self._plugin_trigger(
            "broker_add_before",
            broker=self,
            storage=self.storage,
            model=model
        )
        if new_model:
            model = new_model.get("model", model)

        with socket.create_connection((self.url, self.port)) as s:
            payload = asdict(model)
            payload.update({"uuid": uuid})
            s.sendall(json.dumps(payload).encode())
            try:
                s.settimeout(2.0)
                _ = s.recv(1024)
            except Exception:
                pass

        self._plugin_trigger(
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
        new_task = self._plugin_trigger("broker_get", broker=self, task=task, return_last=True)
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
        new_kw = self._plugin_trigger("broker_update", broker=self, kw=kwargs, return_last=True)
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

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client.bind((self.url, self.port))
        self.client.listen(128)
        self.running = True

        self._listen_task = threading.Thread(
            target=self.listen, args=(worker,), name="broker-listen", daemon=True
        )
        self._listen_task.start()

        def _serve():
            while self.running:
                try:
                    conn, _addr = self.client.accept()
                except OSError:
                    break
                try:
                    self.handle_connection(conn, conn)
                except Exception:
                    with contextlib.suppress(Exception):
                        conn.close()

        self._serve_task = threading.Thread(target=_serve, name="broker-serve", daemon=True)
        self._serve_task.start()

        try:
            while self._serve_task.is_alive():
                self._serve_task.join(timeout=0.5)
        except KeyboardInterrupt:
            pass

    def stop(self):
        """Останавливает брокер."""
        self._plugin_trigger("broker_stop", broker=self)
        self.running = False

        with contextlib.suppress(Exception):
            self.queue.put_nowait(None)

        if self.client:
            with contextlib.suppress(Exception):
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()

            self.client = None

        if self._serve_task and self._serve_task.is_alive():
            with contextlib.suppress(Exception):
                self._serve_task.join(timeout=2.0)

        if self._listen_task and self._listen_task.is_alive():
            with contextlib.suppress(Exception):
                self._listen_task.join(timeout=2.0)

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
                TaskStatusProcessSchema, TaskStatusErrorSchema, TaskStatusCancelSchema
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
            model=model,
            return_last=True
        )
        if new_model:
            model = new_model.get("model", model)

        self.storage.remove_finished_task(task_broker, model)
        return

    def _running_older_tasks(self, worker):
        self._plugin_trigger("broker_running_older_tasks", broker=self, worker=worker)
        return self.storage._running_older_tasks(worker)

    def flush_all(self) -> None:
        """Удалить все данные."""
        self._plugin_trigger("broker_flush_all", broker=self)
        self.storage.flush_all()

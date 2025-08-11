"""Async Socket Broker."""

import asyncio
from dataclasses import asdict
import json
import asyncio_atexit
from typing import Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID, uuid4
from time import time
from typing import TYPE_CHECKING

from qtasks.events.async_events import AsyncEvents

from .base import BaseBroker
from qtasks.storages.async_redis import AsyncRedisStorage
from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin
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


class AsyncSocketBroker(BaseBroker, AsyncPluginMixin):
    """
    Брокер, слушающий сокеты и добавляющий задачи в очередь.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import AsyncSocketBroker

    broker = AsyncSocketBroker(name="QueueTasks", url="127.0.0.1")

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
        """Инициализация AsyncSocketBroker.

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
        self.events = self.events or AsyncEvents()

        self.client = None
        self.storage = storage or AsyncRedisStorage(
            name=name,
            log=self.log,
            config=self.config,
        )
        self.default_sleep = 0.01
        self.running = False

        self.queue = asyncio.Queue()
        self._serve_task: asyncio.Task | None = None
        self._listen_task: asyncio.Task | None = None

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Обрабатывает входящее соединение.

        Args:
            reader (asyncio.StreamReader): Читатель для входящих данных.
            writer (asyncio.StreamWriter): Писатель для исходящих данных.
        """
        try:
            data = await reader.read(4096)
            message = json.loads(data.decode())
            task_name = message["task_name"]
            uuid = message["uuid"]
            priority = message["priority"]
            args = message.get("args", ())
            kwargs = message.get("kwargs", {})
            created_at = message["created_at"]

            await self.storage.add(
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

            await self.queue.put((task_name, uuid, priority))
            writer.write(b"OK")
            await writer.drain()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

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
        """Слушает очередь сокета и передаёт задачи воркеру.

        Args:
            worker (BaseWorker): Класс воркера.
        """
        await self._plugin_trigger("broker_listen_start", broker=self, worker=worker)
        self.running = True

        while self.running:
            try:
                item = await self.queue.get()
            except asyncio.CancelledError:
                break
            if item is None:
                break

            task_name, uuid, priority = item
            task_data = await self.get(uuid)
            args, kwargs, created_at = task_data.args, task_data.kwargs, task_data.created_at

            await self.storage.add_process(f"{task_name}:{uuid}:{priority}", priority)

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
        loop = asyncio.get_running_loop()
        asyncio_atexit.register(self.stop, loop=loop)
        asyncio_atexit.register(self.storage.stop, loop=loop)

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

        new_model = await self._plugin_trigger(
            "broker_add_before",
            broker=self,
            storage=self.storage,
            model=model
        )
        if new_model:
            model = new_model

        await self.storage.add(uuid=uuid, task_status=model)
        reader, writer = await asyncio.open_connection(self.url, self.port)
        payload = asdict(model)
        payload.update({"uuid": uuid})
        writer.write(json.dumps(payload).encode())
        await writer.drain()
        try:
            writer.close()
        except Exception:
            pass

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

        self.client = await asyncio.start_server(self.handle_connection, self.url, self.port)

        self._listen_task = asyncio.create_task(self.listen(worker), name="broker-listen")
        self._serve_task = asyncio.create_task(self.client.serve_forever(), name="broker-serve")
        try:
            await self._serve_task
        except asyncio.CancelledError:
            pass

    async def stop(self):
        """Останавливает брокер."""
        await self._plugin_trigger("broker_stop", broker=self)
        self.running = False

        if self._listen_task and not self._listen_task.done():
            self.queue.put_nowait(None)

        if self.client:
            self.client.close()
            try:
                await self.client.wait_closed()
            except Exception:
                pass

        if self._serve_task and not self._serve_task.done():
            self._serve_task.cancel()
            try:
                await self._serve_task
            except asyncio.CancelledError:
                pass

        if self._listen_task and not self._listen_task.done():
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

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
        return

    async def _running_older_tasks(self, worker):
        await self._plugin_trigger("broker_running_older_tasks", broker=self, worker=worker)
        return await self.storage._running_older_tasks(worker)

    async def flush_all(self) -> None:
        """Удалить все данные."""
        await self._plugin_trigger("broker_flush_all", broker=self)
        await self.storage.flush_all()

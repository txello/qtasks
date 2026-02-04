"""Sync Socket Broker."""
from __future__ import annotations

import atexit
import contextlib
import json
import socket
import threading
from dataclasses import asdict
from datetime import datetime
from queue import Empty, Queue
from time import time
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional
from uuid import UUID, uuid4

from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.sync_events import SyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin
from qtasks.schemas.task import Task
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import (
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusSuccessSchema,
)
from qtasks.storages.sync_redis import SyncRedisStorage

from .base import BaseBroker

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker


class SyncSocketBroker(BaseBroker, SyncPluginMixin):
    """
    A broker that listens to sockets and adds tasks to the queue.

    ## Example

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
            Doc("""
                    Project name. This name is also used by the broker.

                    Default: `QueueTasks`.
                    """),
        ] = "QueueTasks",
        url: Annotated[
            str,
            Doc("""
                    URL to connect to the socket.

                    Default: `127.0.0.1`.
                    """),
        ] = "127.0.0.1",
        port: Annotated[
            int,
            Doc("""
                    Port for connecting to a socket.

                    Default: `6379`.
                    """),
        ] = 6379,
        storage: Annotated[
            Optional[BaseStorage],
            Doc("""
                    Storage.

                    Default: `AsyncRedisStorage`.
                    """),
        ] = None,
        log: Annotated[
            Logger | None,
            Doc("""
                    Logger.

                    Default: `qtasks.logs.Logger`.
                    """),
        ] = None,
        config: Annotated[
            QueueConfig | None,
            Doc("""
                    Config.

                    Default: `qtasks.configs.config.QueueConfig`.
                    """),
        ] = None,
        events: Annotated[
            Optional[BaseEvents],
            Doc("""
                    Events.

                    Default: `qtasks.events.AsyncEvents`.
                    """),
        ] = None,
    ):
        """
        Initializing SyncSocketBroker.

        Args:
            name (str, optional): Project name. Default: `QueueTasks`.
            url (str, optional): URL to connect to the socket. Default: `127.0.0.1`.
            port (int, optional): Port to connect to the socket. Default: `6379`.
            storage (BaseStorage, optional): Storage. Default: `None`.
            log (Logger, optional): Logger. Default: `None`.
            config (QueueConfig, optional): Config. Default: `None`.
            events (BaseEvents, optional): Events. Default: `qtasks.events.SyncEvents`.
        """
        self.url = url
        self.port = port
        storage = storage or SyncRedisStorage(
            name=name, log=log, config=config, events=events
        )
        super().__init__(
            name=name, log=log, config=config, events=events, storage=storage
        )

        self.storage: BaseStorage[Literal[False]]

        self.events = self.events or SyncEvents()

        self.client = None
        self.default_sleep = 0.01
        self.running = False

        self.queue = Queue()
        self._serve_task = None
        self._listen_task = None

    def handle_connection(self, reader, writer):
        """
        Handles an incoming connection.

        Args:
            reader: Reader for incoming data.
            writer: Writer for outgoing data.
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
            BaseWorker[Literal[False]],
            Doc("""
                    Worker class.
                    """),
        ],
    ):
        """
        Listens to the socket queue and transfers tasks to the worker.

        Args:
            worker (BaseWorker): Worker class.

        Raises:
            KeyError: Task not found.
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
            model_get = self.get(uuid=uuid)
            if not model_get:
                raise KeyError(f"Task not found: {uuid}")

            args, kwargs, created_at = (
                model_get.args or (),
                model_get.kwargs or {},
                model_get.created_at.timestamp(),
            )

            self.storage.add_process(f"{task_name}:{uuid}:{priority}", priority)

            if self.log:
                self.log.info(f"Received new task: {uuid}")
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
            Doc("""
                    Task name.
                    """),
        ],
        priority: Annotated[
            int,
            Doc("""
                    Task priority.

                    Default: `0`.
                    """),
        ] = 0,
        extra: Annotated[
            dict | None,
            Doc("""
                    Additional task parameters.

                    Default: `None`.
                    """),
        ] = None,
        args: Annotated[
            tuple | None,
            Doc("""
                    Task arguments of type args.

                    Default: `()`.
                    """),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc("""
                    Task arguments of type kwargs.

                    Default: `{}`.
                    """),
        ] = None,
    ) -> Task:
        """
        Adds a task to the broker.

        Args:
            task_name (str): The name of the task.
            priority (int, optional): Task priority. By default: 0.
            extra (dict, optional): Additional task parameters. Default: `None`.
            args (tuple, optional): Task arguments of type args. Default: `()`.
            kwargs (dict, optional): Task arguments of type kwargs. Default: `{}`.

        Returns:
            Task: `schemas.task.Task`

        Raises:
            ValueError: Invalid task status.
        """
        atexit.register(self.stop)
        atexit.register(self.storage.stop)

        args, kwargs = args or (), kwargs or {}
        uuid = uuid4()
        uuid_str = str(uuid)
        created_at = time()
        model = TaskStatusNewSchema(
            task_name=task_name,
            priority=priority,
            created_at=created_at,
            updated_at=created_at,
            args=json.dumps(args),
            kwargs=json.dumps(kwargs),
        )

        if extra:
            model = self._dynamic_model(model=model, extra=extra)

        new_model = self._plugin_trigger(
            "broker_add_before", broker=self, storage=self.storage, model=model
        )
        if new_model:
            model = new_model.get("model", model)

        with socket.create_connection((self.url, self.port)) as s:
            payload = asdict(model)
            payload.update({"uuid": uuid_str})
            s.sendall(json.dumps(payload).encode())
            try:
                s.settimeout(2.0)
                _ = s.recv(1024)
            except Exception:
                pass

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
            Doc("""
                    UUID of the task.
                    """),
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
            Doc("""
                    Update arguments for storage type kwargs.
                    """),
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
            Doc("""
                    Worker class.
                    """),
        ],
    ) -> None:
        """
        Launches the broker.

        Args:
            worker (BaseWorker): Worker class.

        Raises:
            RuntimeError: self.client is not initialized.
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
            if not self.client:
                raise RuntimeError("self.client is not initialized.")

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

        self._serve_task = threading.Thread(
            target=_serve, name="broker-serve", daemon=True
        )
        self._serve_task.start()

        try:
            while self._serve_task.is_alive():
                self._serve_task.join(timeout=0.5)
        except KeyboardInterrupt:
            pass

    def stop(self):
        """The broker stops."""
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
            Doc("""
                    Priority task diagram.
                    """),
        ],
        model: Annotated[
            TaskStatusSuccessSchema | TaskStatusErrorSchema,
            Doc("""
                    Model of the task result.
                    """),
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
        return

    def _running_older_tasks(self, worker):
        self._plugin_trigger("broker_running_older_tasks", broker=self, worker=worker)
        return self.storage._running_older_tasks(worker)

    def flush_all(self) -> None:
        """Delete all data."""
        self._plugin_trigger("broker_flush_all", broker=self)
        self.storage.flush_all()

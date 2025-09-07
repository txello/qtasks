"""Sync Redis storage."""

import json
import time
from typing import List, Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID
import redis
from typing import TYPE_CHECKING

from qtasks.configs.config import QueueConfig
from qtasks.contrib.redis.sync_queue_client import SyncRedisCommandQueue
from qtasks.configs.sync_redisglobalconfig import SyncRedisGlobalConfig
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.events.sync_events import SyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin

from .base import BaseStorage
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import (
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusSuccessSchema,
)

if TYPE_CHECKING:
    from qtasks.configs.base import BaseGlobalConfig
    from qtasks.workers.base import BaseWorker
    from qtasks.schemas.task import Task
    from qtasks.events.base import BaseEvents


class SyncRedisStorage(BaseStorage, SyncPluginMixin):
    """
    Хранилище, работающий с Redis, сохраняя информацию о задачах.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import SyncRedisBroker
    from qtasks.storages import SyncRedisStorage

    storage = SyncRedisStorage(name="QueueTasks")
    broker = SyncRedisBroker(name="QueueTasks", storage=storage)

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
        ] = "redis://localhost:6379/0",
        queue_process: Annotated[
            str,
            Doc(
                """
                    Имя канала для задач в процессе.

                    По умолчанию: `task_process`.
                    """
            ),
        ] = "task_process",
        redis_connect: Annotated[
            Optional[redis.Redis],
            Doc(
                """
                    Внешний класс подключения к Redis.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        global_config: Annotated[
            Optional["BaseGlobalConfig"],
            Doc(
                """
                    Глобальный конфиг.

                    По умолчанию: `None`.
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

                    По умолчанию: `qtasks.events.SyncEvents`.
                    """
            ),
        ] = None,
    ):
        """Инициализация хранилища.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "QueueTasks".
            url (str, optional): URL для подключения к Redis. По умолчанию: "redis://localhost:6379/0".
            queue_process (str, optional): Имя канала для задач в процессе. По умолчанию: "task_process".
            redis_connect (redis.Redis, optional): Внешний класс подключения к Redis. По умолчанию: None.
            global_config (BaseGlobalConfig, optional): Глобальный конфиг. По умолчанию: None.
            log (Logger, optional): Логгер. По умолчанию: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `qtasks.configs.config.QueueConfig`.
            events (BaseEvents, optional): События. По умолчанию: `qtasks.events.SyncEvents`.
        """
        super().__init__(name=name, log=log, config=config, events=events)
        self.url = url
        self._queue_process = queue_process
        self.queue_process = f"{self.name}:{queue_process}"
        self.events = self.events or SyncEvents()
        self.client = redis_connect or redis.Redis.from_url(
            self.url, decode_responses=True, encoding="utf-8"
        )
        self.redis_contrib = SyncRedisCommandQueue(redis=self.client, log=self.log)

        self.global_config = global_config or SyncRedisGlobalConfig(
            name=self.name, redis_connect=self.client, log=self.log, config=self.config
        )

    def add(
        self,
        uuid: Annotated[
            Union[UUID, str],
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
        task_status: Annotated[
            TaskStatusNewSchema,
            Doc(
                """
                    Схема статуса новой задачи.
                    """
            ),
        ],
    ) -> None:
        """Добавление задачи в хранилище.

        Args:
            uuid (UUID | str): UUID задачи.
            task_status (TaskStatusNewSchema): Схема статуса новой задачи.
        """
        uuid = str(uuid)

        new_data = self._plugin_trigger("storage_add", storage=self, uuid=uuid, task_status=task_status, return_last=True)
        if new_data:
            uuid = new_data.get("uuid", uuid)
            task_status = new_data.get("task_status", task_status)

        self.client.hset(f"{self.name}:{uuid}", mapping=task_status.__dict__)
        return

    def get(self, uuid: Union[UUID, str]) -> Union["Task", None]:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        key = f"{self.name}:{uuid}"
        result = self.client.hgetall(key)
        if not result:
            return None

        result = self._build_task(uuid=uuid, result=result)
        new_result = self._plugin_trigger("storage_get", storage=self, result=result, return_last=True)
        if new_result:
            result = new_result.get("result", result)
        return result

    def get_all(self) -> List["Task"]:
        """Получить все задачи.

        Returns:
            List[Task]: Массив задач.
        """
        pattern = f"{self.name}:*"
        results: List["Task"] = []
        for key in self.client.scan_iter(pattern):
            try:
                _, uuid = key.split(":")
                if uuid in [self._queue_process, "task_queue"]:
                    continue
                task = self.get(uuid=uuid)
                if task:
                    results.append(task)
            except Exception:
                continue

        new_results = self._plugin_trigger("storage_get_all", storage=self, results=results, return_last=True)
        if new_results:
            results = new_results.get("results", results)

        return results

    def update(
        self,
        **kwargs: Annotated[
            dict,
            Doc(
                """
                    Аргументы обновления типа kwargs.
                    """
            ),
        ],
    ) -> None:
        """Обновляет информацию о задаче.

        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
        """
        new_kw = self._plugin_trigger("storage_update", storage=self, kw=kwargs, return_last=True)
        if new_kw:
            kwargs = new_kw.get("kw", kwargs)

        return self.redis_contrib.execute(
            "hset", kwargs["name"], mapping=kwargs["mapping"]
        )

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
        """Обновляет данные завершенной задачи.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusSuccessSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        if model.status == TaskStatusEnum.SUCCESS.value and not isinstance(
            model.returning, (bytes, str, int, float)
        ):
            trace = "Invalid input of type: 'NoneType'. Convert to a bytes, string, int or float first."
            model = TaskStatusErrorSchema(
                task_name=task_broker.name,
                priority=task_broker.priority,
                traceback=trace,
                created_at=task_broker.created_at,
                updated_at=time.time(),
            )
            self.log.warning(f"Задача {task_broker.uuid} завершена с ошибкой:\n{trace}")

        self.redis_contrib.execute(
            "hset", f"{self.name}:{task_broker.uuid}", mapping=model.__dict__
        )
        self.redis_contrib.execute(
            "zrem",
            self.queue_process,
            f"{task_broker.name}:{task_broker.uuid}:{task_broker.priority}",
        )

        self._plugin_trigger(
            "storage_remove_finished_task", storage=self, task_broker=task_broker, model=model
        )
        return

    def start(self):
        """Запускает хранилище."""
        self._plugin_trigger("storage_start", storage=self)
        if self.global_config:
            self.global_config.start()

    def stop(self) -> None:
        """Останавливает хранилище."""
        self._plugin_trigger("storage_stop", storage=self)
        self.client.close()

    def add_process(
        self,
        task_data: Annotated[
            str,
            Doc(
                """
                    Данные задачи из брокера.
                    """
            ),
        ],
        priority: Annotated[
            int,
            Doc(
                """
                    Приоритет задачи.
                    """
            ),
        ],
    ) -> None:
        """Добавляет задачу в список задач в процессе.

        Args:
            task_data (str): Данные задачи из брокера.
            priority (int): Приоритет задачи.
        """
        new_data = self._plugin_trigger("storage_add_process", storage=self, return_last=True)
        if new_data:
            task_data = new_data.get("task_data", task_data)
            priority = new_data.get("priority", priority)

        self.client.zadd(self.queue_process, {task_data: priority})
        return

    def _running_older_tasks(self, worker: "BaseWorker") -> None:
        tasks = self.client.zrange(self.queue_process, 0, -1)
        for task_data in tasks:
            task_name, uuid, priority = task_data.split(":")
            name_ = f"{self.name}:{uuid}"
            args, kwargs, created_at = (
                self.client.hget(name_, "args"),
                self.client.hget(name_, "kwargs"),
                self.client.hget(name_, "created_at"),
            )
            args, kwargs, created_at = (
                json.loads(args) or (),
                json.loads(kwargs) or {},
                float(created_at),
            )
            new_data = self._plugin_trigger("storage_running_older_tasks", storage=self, worker=worker, return_last=True)
            if new_data:
                task_name = new_data.get("task_name", task_name)
                uuid = new_data.get("uuid", uuid)
                priority = new_data.get("priority", priority)
                created_at = new_data.get("created_at", created_at)
                args = new_data.get("args", args)
                kwargs = new_data.get("kw", kwargs)

            worker.add(
                name=task_name,
                uuid=uuid,
                priority=int(priority),
                created_at=created_at,
                args=args,
                kwargs=kwargs,
            )

    def _delete_finished_tasks(self):
        self._plugin_trigger("storage_delete_finished_tasks", storage=self)
        pattern = f"{self.name}:"
        try:
            tasks: List["Task"] = list(
                filter(
                    lambda task: task.status != TaskStatusEnum.NEW.value, self.get_all()
                )
            )

            tasks_hash = [pattern + str(task.uuid) for task in tasks]
            tasks_queue = [
                f"{task.task_name}:{task.uuid}:{task.priority}" for task in tasks
            ]

            if tasks_queue:
                self.client.zrem(self.queue_process, *tasks_queue)
            if tasks_hash:
                self.client.delete(*tasks_hash)
        except BaseException:
            pass
        return

    def flush_all(self) -> None:
        """Удалить все данные."""
        self._plugin_trigger("storage_flush_all", storage=self)

        pipe = self.client.pipeline()

        pattern = f"{self.name}:*"
        for key in self.client.scan_iter(pattern):
            self.client.delete(key)
        pipe.execute()
        return

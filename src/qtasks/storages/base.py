"""Base storage class."""
from __future__ import annotations

import datetime
import json
from abc import ABC, abstractmethod
from collections.abc import Awaitable
from dataclasses import field, fields, make_dataclass
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Literal,
    Optional,
    overload,
)
from uuid import UUID

from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.schemas.task import Task
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import (
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusSuccessSchema,
)
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.configs.base import BaseGlobalConfig
    from qtasks.events.base import BaseEvents
    from qtasks.plugins.base import BasePlugin
    from qtasks.workers.base import BaseWorker


class BaseStorage(Generic[TAsyncFlag], ABC):
    """
    `BaseStorage` - Абстрактный класс, который является фундаментом для Хранилищ.

    ## Пример

    ```python
    from qtasks.storages.base import BaseStorage

    class MyStorage(BaseStorage):
        def __init__(self, name: str = None):
            super().__init__(name=name)
            pass
    ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Имя проекта. Это имя можно использовать для тегов для Storage.

                    По умолчанию: `QueueTasks`.
                    """
            ),
        ] = "QueueTasks",
        global_config: Annotated[
            Optional[BaseGlobalConfig[TAsyncFlag]],
            Doc(
                """
                    Глобальный конфиг.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
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

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ):
        """Инициализация базового хранилища.

        Args:
            name (str, optional): Имя проекта. По умолчанию: `QueueTasks`.
            global_config (BaseGlobalConfig, optional): Глобальный конфиг. По умолчанию: `None`.
            log (Logger, optional): Логгер. По умолчанию: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `qtasks.configs.config.QueueConfig`.
            events (BaseEvents, optional): События. По умолчанию: `None`.
        """
        self.name = name
        self.global_config: BaseGlobalConfig[TAsyncFlag] | None = global_config

        self.config = config or QueueConfig()
        self.log = (
            log.with_subname("Storage")
            if log
            else Logger(
                name=self.name or "QueueTasks",
                subname="Storage",
                default_level=self.config.logs_default_level_server,
                format=self.config.logs_format,
            )
        )
        self.events = events

        self.client = None
        self.plugins: dict[str, list[BasePlugin]] = {}

        self.init_plugins()

    @overload
    def add(
        self: BaseStorage[Literal[False]],
        uuid: Annotated[
            UUID | str,
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
    ) -> None: ...

    @overload
    async def add(
        self: BaseStorage[Literal[True]],
        uuid: Annotated[
            UUID | str,
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
    ) -> None: ...

    @abstractmethod
    def add(
        self,
        uuid: Annotated[
            UUID | str,
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
    ) -> None | Awaitable[None]:
        """Добавление задачи в хранилище.

        Args:
            uuid (UUID | str): UUID задачи.
            task_status (TaskStatusNewSchema): Схема статуса новой задачи.
        """
        pass

    @overload
    def get(
        self: BaseStorage[Literal[False]],
        uuid: Annotated[
            UUID | str,
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
    ) -> Task | None: ...

    @overload
    async def get(
        self: BaseStorage[Literal[True]],
        uuid: Annotated[
            UUID | str,
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
    ) -> Task | None: ...

    @abstractmethod
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
    ) -> Task | None | Awaitable[Task | None]:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        pass

    @overload
    def get_all(self: BaseStorage[Literal[False]]) -> list[Task]: ...

    @overload
    async def get_all(self: BaseStorage[Literal[True]]) -> list[Task]: ...

    @abstractmethod
    def get_all(self) -> list[Task] | Awaitable[list[Task]]:
        """Получить все задачи.

        Returns:
            List[Task]: Массив задач.
        """
        pass

    @overload
    def update(
        self: BaseStorage[Literal[False]],
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Аргументы обновления типа kwargs.
                    """
            ),
        ],
    ) -> None: ...

    @overload
    async def update(
        self: BaseStorage[Literal[True]],
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Аргументы обновления типа kwargs.
                    """
            ),
        ],
    ) -> None: ...

    @abstractmethod
    def update(
        self,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Аргументы обновления типа kwargs.
                    """
            ),
        ],
    ) -> None | Awaitable[None]:
        """Обновляет информацию о задаче.

        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
        """
        pass

    @overload
    def start(self: BaseStorage[Literal[False]]) -> None: ...

    @overload
    async def start(self: BaseStorage[Literal[True]]) -> None: ...

    @abstractmethod
    def start(self) -> None | Awaitable[None]:
        """Запускает хранилище. Эта функция задействуется основным экземпляром `QueueTasks` после запуске функции `run_forever`."""
        pass

    @overload
    def stop(self: BaseStorage[Literal[False]]) -> None: ...

    @overload
    async def stop(self: BaseStorage[Literal[True]]) -> None: ...

    @abstractmethod
    def stop(self) -> None | Awaitable[None]:
        """Останавливает хранилище. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever`."""
        pass

    @overload
    def add_process(
        self: BaseStorage[Literal[False]],
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
    ) -> None: ...

    @overload
    async def add_process(
        self: BaseStorage[Literal[True]],
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
    ) -> None: ...

    @abstractmethod
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
    ) -> None | Awaitable[None]:
        """Добавляет задачу в список задач в процессе.

        Args:
            task_data (str): Данные задачи из брокера.
            priority (int): Приоритет задачи.
        """
        pass

    def add_plugin(
        self,
        plugin: Annotated[
            BasePlugin,
            Doc(
                """
                    Плагин.
                    """
            ),
        ],
        trigger_names: Annotated[
            list[str] | None,
            Doc(
                """
                    Имя триггеров для плагина.

                    По умолчанию: По умолчанию: будет добавлен в `Globals`.
                    """
            ),
        ] = None,
    ) -> None:
        """Добавить плагин в класс.

        Args:
            plugin (BasePlugin): Плагин
            trigger_names (List[str], optional): Имя триггеров для плагина. По умолчанию: будет добавлен в `Globals`.
        """
        trigger_names = trigger_names or ["Globals"]

        for name in trigger_names:
            if name not in self.plugins:
                self.plugins.update({name: [plugin]})
            else:
                self.plugins[name].append(plugin)
        return

    @overload
    def remove_finished_task(
        self: BaseStorage[Literal[False]],
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
    ) -> None: ...

    @overload
    async def remove_finished_task(
        self: BaseStorage[Literal[True]],
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
    ) -> None: ...

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
    ) -> None | Awaitable[None]:
        """Обновляет данные хранилища через функцию `self.storage.remove_finished_task`.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        pass

    @overload
    def _delete_finished_tasks(self: BaseStorage[Literal[False]]) -> None: ...

    @overload
    async def _delete_finished_tasks(self: BaseStorage[Literal[True]]) -> None: ...

    def _delete_finished_tasks(self) -> None | Awaitable[None]:
        """Удаляет все завершенные задачи."""
        pass

    @overload
    def _running_older_tasks(
        self: BaseStorage[Literal[False]], worker: BaseWorker
    ) -> None: ...

    @overload
    async def _running_older_tasks(
        self: BaseStorage[Literal[True]], worker: BaseWorker
    ) -> None: ...

    def _running_older_tasks(
        self, worker: BaseWorker
    ) -> None | Awaitable[None]:
        """Удаляет все старые задачи.

        Args:
            worker (BaseWorker): Компонент Worker.
        """
        pass

    def update_config(
        self,
        config: Annotated[
            QueueConfig,
            Doc(
                """
                    Конфиг.
                    """
            ),
        ],
    ) -> None:
        """Обновляет конфиг брокера.

        Args:
            config (QueueConfig): Конфиг.
        """
        self.config = config
        return

    @overload
    def flush_all(self: BaseStorage[Literal[False]]) -> None: ...

    @overload
    async def flush_all(self: BaseStorage[Literal[True]]) -> None: ...

    def flush_all(self) -> None | Awaitable[None]:
        """Удалить все данные."""
        pass

    def _build_task(self, uuid, result: dict) -> Task:
        # Сначала собираем стандартные аргументы Task
        base_kwargs = dict(
            status=result["status"],
            uuid=uuid,
            priority=int(result["priority"]),
            task_name=result["task_name"],
            args=json.loads(result["args"]),
            kwargs=json.loads(result["kwargs"]),
            created_at=datetime.datetime.fromtimestamp(float(result["created_at"])),
            updated_at=datetime.datetime.fromtimestamp(float(result["updated_at"])),
        )
        if "returning" in result:
            base_kwargs["returning"] = json.loads(result["returning"])
        if "traceback" in result:
            base_kwargs["traceback"] = result["traceback"]

        # Вычисляем имена стандартных полей
        task_field_names = {f.name for f in fields(Task)}

        # Ищем дополнительные ключи
        extra_fields = []
        extra_values = {}

        for key, value in result.items():
            if key not in task_field_names:
                # Типизация примитивная — можно улучшить
                field_type = self._infer_type(value)
                extra_fields.append((key, field_type, field(default=None)))

                # Можно привести значение к типу
                if field_type is bool:
                    extra_values[key] = value.lower() == "true"
                elif field_type is int:
                    extra_values[key] = int(value)
                elif field_type is float:
                    extra_values[key] = float(value)
                else:
                    extra_values[key] = value

        # Создаем новый dataclass с дополнительными полями
        if extra_fields:
            NewTask = make_dataclass("Task", extra_fields, bases=(Task,))
        else:
            NewTask = Task

        # Объединяем все аргументы
        task = NewTask(**base_kwargs, **extra_values)
        return task

    def _infer_type(self, value: str):
        """Пытается определить реальный тип из строки."""
        if value.lower() in {"true", "false"}:
            return bool
        try:
            int(value)
            return int
        except ValueError:
            pass
        try:
            float(value)
            return float
        except ValueError:
            pass
        return str

    def init_plugins(self):
        """Инициализация плагинов."""
        pass

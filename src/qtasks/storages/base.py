"""Base storage class."""

from abc import ABC, abstractmethod
from dataclasses import field, fields, make_dataclass
import datetime
import json
from typing import Awaitable, Dict, Generic, List, Literal, Optional, Union, overload
from typing_extensions import Annotated, Doc
from uuid import UUID
from typing import TYPE_CHECKING

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
    from qtasks.plugins.base import BasePlugin
    from qtasks.events.base import BaseEvents
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
            Optional["BaseGlobalConfig[TAsyncFlag]"],
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
        self.global_config: Optional["BaseGlobalConfig[TAsyncFlag]"] = global_config

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
        self.plugins: Dict[str, List["BasePlugin"]] = {}

        self.init_plugins()

    @overload
    def add(
        self: "BaseStorage[Literal[False]]",
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
    ) -> None: ...

    @overload
    async def add(
        self: "BaseStorage[Literal[True]]",
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
    ) -> None: ...

    @abstractmethod
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
    ) -> Union[None, Awaitable[None]]:
        """Добавление задачи в хранилище.

        Args:
            uuid (UUID | str): UUID задачи.
            task_status (TaskStatusNewSchema): Схема статуса новой задачи.
        """
        pass

    @overload
    def get(
        self: "BaseStorage[Literal[False]]",
        uuid: Annotated[
            Union[UUID, str],
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
    ) -> Union[Task, None]: ...

    @overload
    async def get(
        self: "BaseStorage[Literal[True]]",
        uuid: Annotated[
            Union[UUID, str],
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
    ) -> Union[Task, None]: ...

    @abstractmethod
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
    ) -> Union[Optional[Task], Awaitable[Optional[Task]]]:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        pass

    @overload
    def get_all(self: "BaseStorage[Literal[False]]") -> List[Task]: ...

    @overload
    async def get_all(self: "BaseStorage[Literal[True]]") -> List[Task]: ...

    @abstractmethod
    def get_all(self) -> Union[List[Task], Awaitable[List[Task]]]:
        """Получить все задачи.

        Returns:
            List[Task]: Массив задач.
        """
        pass

    @overload
    def update(
        self: "BaseStorage[Literal[False]]",
        **kwargs: Annotated[
            dict,
            Doc(
                """
                    Аргументы обновления типа kwargs.
                    """
            ),
        ],
    ) -> None: ...

    @overload
    async def update(
        self: "BaseStorage[Literal[True]]",
        **kwargs: Annotated[
            dict,
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
            dict,
            Doc(
                """
                    Аргументы обновления типа kwargs.
                    """
            ),
        ],
    ) -> Union[None, Awaitable[None]]:
        """Обновляет информацию о задаче.

        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
        """
        pass

    @overload
    def start(self: "BaseStorage[Literal[False]]") -> None: ...

    @overload
    async def start(self: "BaseStorage[Literal[True]]") -> None: ...

    @abstractmethod
    def start(self) -> Union[None, Awaitable[None]]:
        """Запускает хранилище. Эта функция задействуется основным экземпляром `QueueTasks` после запуске функции `run_forever`."""
        pass

    @overload
    def stop(self: "BaseStorage[Literal[False]]") -> None: ...

    @overload
    async def stop(self: "BaseStorage[Literal[True]]") -> None: ...

    @abstractmethod
    def stop(self) -> Union[None, Awaitable[None]]:
        """Останавливает хранилище. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever`."""
        pass

    @overload
    def add_process(
        self: "BaseStorage[Literal[False]]",
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
        self: "BaseStorage[Literal[True]]",
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
    ) -> Union[None, Awaitable[None]]:
        """Добавляет задачу в список задач в процессе.

        Args:
            task_data (str): Данные задачи из брокера.
            priority (int): Приоритет задачи.
        """
        pass

    def add_plugin(
        self,
        plugin: Annotated[
            "BasePlugin",
            Doc(
                """
                    Плагин.
                    """
            ),
        ],
        trigger_names: Annotated[
            Optional[List[str]],
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
        self: "BaseStorage[Literal[False]]",
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
    ) -> None: ...

    @overload
    async def remove_finished_task(
        self: "BaseStorage[Literal[True]]",
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
            Union[TaskStatusSuccessSchema, TaskStatusErrorSchema],
            Doc(
                """
                    Модель результата задачи.
                    """
            ),
        ],
    ) -> Union[None, Awaitable[None]]:
        """Обновляет данные хранилища через функцию `self.storage.remove_finished_task`.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        pass

    @overload
    def _delete_finished_tasks(self: "BaseStorage[Literal[False]]") -> None: ...

    @overload
    async def _delete_finished_tasks(self: "BaseStorage[Literal[True]]") -> None: ...

    def _delete_finished_tasks(self) -> Union[None, Awaitable[None]]:
        """Удаляет все завершенные задачи."""
        pass

    @overload
    def _running_older_tasks(
        self: "BaseStorage[Literal[False]]", worker: "BaseWorker"
    ) -> None: ...

    @overload
    async def _running_older_tasks(
        self: "BaseStorage[Literal[True]]", worker: "BaseWorker"
    ) -> None: ...

    def _running_older_tasks(
        self, worker: "BaseWorker"
    ) -> Union[None, Awaitable[None]]:
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
    def flush_all(self: "BaseStorage[Literal[False]]") -> None: ...

    @overload
    async def flush_all(self: "BaseStorage[Literal[True]]") -> None: ...

    def flush_all(self) -> Union[None, Awaitable[None]]:
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

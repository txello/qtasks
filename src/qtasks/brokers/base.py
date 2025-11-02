"""Base Broker."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from dataclasses import asdict, field, fields, make_dataclass
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
    TaskStatusCancelSchema,
    TaskStatusErrorSchema,
    TaskStatusNewSchema,
    TaskStatusProcessSchema,
    TaskStatusSuccessSchema,
)
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents
    from qtasks.plugins.base import BasePlugin
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker


class BaseBroker(Generic[TAsyncFlag], ABC):
    """
    `BaseBroker` - Абстрактный класс, который является фундаментом для Брокеров.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers.base import BaseBroker

    class MyBroker(BaseBroker):
        def __init__(self, name: str = None, storage: BaseStorage = None):
            super().__init__(name=name, storage=storage)
            pass
    ```
    """

    def __init__(
        self,
        storage: Annotated[
            BaseStorage[TAsyncFlag],
            Doc(
                """
                    Хранилище `qtasks.storages.base.BaseStorage`.

                    По умолчанию: `None`.
                    """
            ),
        ],
        name: Annotated[
            str | None,
            Doc(
                """
                    Имя проекта. Это имя можно использовать для тегов для Брокеров.

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
        """Инициализация BaseBroker.

        Args:
            name (str, optional): Имя проекта. По умолчанию: `None`.
            storage (BaseStorage, optional): Хранилище. По умолчанию: `None`.
            log (Logger, optional): Логгер. По умолчанию: `None`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `None`.
            events (BaseEvents, optional): События. По умолчанию: `None`.
        """
        self.name = name
        self.config = config or QueueConfig()
        self.log = (
            log.with_subname("Broker")
            if log
            else Logger(
                name=self.name or "QueueTasks",
                subname="Broker",
                default_level=self.config.logs_default_level_server,
                format=self.config.logs_format,
            )
        )
        self.events = events

        self.storage = storage

        self.plugins: dict[str, list[BasePlugin]] = {}

        self.init_plugins()

    @overload
    def add(
        self: BaseBroker[Literal[False]],
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
                    """
            ),
        ] = None,
        args: Annotated[
            tuple | None,
            Doc(
                """
                    Аргументы задачи типа args.
                    """
            ),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc(
                """
                    Аргументы задачи типа kwargs.
                    """
            ),
        ] = None,
    ) -> Task: ...

    @overload
    async def add(
        self: BaseBroker[Literal[True]],
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
                    """
            ),
        ] = None,
        args: Annotated[
            tuple | None,
            Doc(
                """
                    Аргументы задачи типа args.
                    """
            ),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc(
                """
                    Аргументы задачи типа kwargs.
                    """
            ),
        ] = None,
    ) -> Task: ...

    @abstractmethod
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
                    """
            ),
        ] = None,
        args: Annotated[
            tuple | None,
            Doc(
                """
                    Аргументы задачи типа args.
                    """
            ),
        ] = None,
        kwargs: Annotated[
            dict | None,
            Doc(
                """
                    Аргументы задачи типа kwargs.
                    """
            ),
        ] = None,
    ) -> Task | Awaitable[Task]:
        """Добавление задачи в брокер.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умоланию: 0.
            extra (dict, optional): Дополнительные параметры задачи.
            args (tuple, optional): Аргументы задачи типа args.
            kwargs (dict, optional): Аргументы задачи типа kwargs.

        Returns:
            Task: `schemas.task.Task`
        """
        pass

    @overload
    def get(
        self: BaseBroker[Literal[False]],
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
        self: BaseBroker[Literal[True]],
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
    def update(
        self: BaseBroker[Literal[False]],
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Аргументы обновления для хранилища типа kwargs.
                    """
            ),
        ],
    ) -> None: ...

    @overload
    async def update(
        self: BaseBroker[Literal[True]],
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    Аргументы обновления для хранилища типа kwargs.
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
                    Аргументы обновления для хранилища типа kwargs.
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
    def start(
        self: BaseBroker[Literal[False]],
        worker: Annotated[
            Optional[BaseWorker],
            Doc(
                """
                    Класс Воркера.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ) -> None: ...

    @overload
    async def start(
        self: BaseBroker[Literal[True]],
        worker: Annotated[
            Optional[BaseWorker],
            Doc(
                """
                    Класс Воркера.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ) -> None: ...

    @abstractmethod
    def start(
        self,
        worker: Annotated[
            Optional[BaseWorker],
            Doc(
                """
                    Класс Воркера.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ) -> None | Awaitable[None]:
        """Запуск Брокера. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever`.

        Args:
            worker (BaseWorker, optional): класс Воркера. По умолчанию: `None`.
        """
        pass

    @overload
    def stop(
        self: BaseBroker[Literal[False]],
    ) -> None: ...

    @overload
    async def stop(
        self: BaseBroker[Literal[True]],
    ) -> None: ...

    @abstractmethod
    def stop(self) -> None | Awaitable[None]:
        """Останавливает брокер. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever`."""
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
    def flush_all(self: BaseBroker[Literal[False]]) -> None: ...

    @overload
    async def flush_all(self: BaseBroker[Literal[True]]) -> None: ...

    def flush_all(self) -> None | Awaitable[None]:
        """Удалить все данные."""
        pass

    def init_plugins(self):
        """Инициализация плагинов."""
        pass

    @overload
    def remove_finished_task(
        self: BaseBroker[Literal[False]],
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc(
                """
                    Схема приоритетной задачи.
                    """
            ),
        ],
        model: Annotated[
            TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema,
            Doc(
                """
                    Модель результата задачи.
                    """
            ),
        ],
    ) -> None: ...

    @overload
    async def remove_finished_task(
        self: BaseBroker[Literal[True]],
        task_broker: Annotated[
            TaskPrioritySchema,
            Doc(
                """
                    Схема приоритетной задачи.
                    """
            ),
        ],
        model: Annotated[
            TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema,
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
            TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema,
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
            model (TaskStatusSuccessSchema | TaskStatusProcessSchema | TaskStatusErrorSchema | TaskStatusCancelSchema): Модель результата задачи.
        """
        pass

    def _dynamic_model(
        self,
        model: Annotated[
            TaskStatusNewSchema,
            Doc(
                """
                    Модель задачи.
                    """
            ),
        ],
        extra: Annotated[
            dict,
            Doc(
                """
                    Дополнительные поля.
                    """
            ),
        ],
    ):
        # Вычисляем имена стандартных полей
        task_field_names = {f.name for f in fields(TaskStatusNewSchema)}

        # Ищем дополнительные ключи
        extra_fields = []
        extra_values = {}

        for key, value in extra.items():
            if key not in task_field_names:
                # Типизация примитивная — можно улучшить
                field_type = type(value)
                extra_fields.append((key, field_type, field(default=None)))
                extra_values[key] = value

        # Создаем новый dataclass с дополнительными полями
        if extra_fields:
            NewTask = make_dataclass(
                "TaskStatusNewSchema", extra_fields, bases=(TaskStatusNewSchema,)
            )
        else:
            NewTask = TaskStatusNewSchema

        # Объединяем все аргументы
        return NewTask(**asdict(model), **extra_values)

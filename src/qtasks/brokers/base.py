"""Base Broker."""

from abc import ABC, abstractmethod
from dataclasses import asdict, field, fields, make_dataclass
from typing import Dict, List, Optional, Union
from uuid import UUID
from typing_extensions import Annotated, Doc
from typing import TYPE_CHECKING

from qtasks.logs import Logger
from qtasks.schemas.task import Task
from qtasks.configs.config import QueueConfig
from qtasks.schemas.task_status import TaskStatusNewSchema

if TYPE_CHECKING:
    from qtasks.storages.base import BaseStorage
    from qtasks.workers.base import BaseWorker
    from qtasks.plugins.base import BasePlugin


class BaseBroker(ABC):
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
        name: Annotated[
            Optional[str],
            Doc(
                """
                    Имя проекта. Это имя можно использовать для тегов для Брокеров.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        storage: Annotated[
            Optional["BaseStorage"],
            Doc(
                """
                    Хранилище `qtasks.storages.base.BaseStorage`.

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
    ):
        """Инициализация BaseBroker.

        Args:
            name (str, optional): Имя проекта. По умолчанию: `None`.
            storage (BaseStorage, optional): Хранилище. По умолчанию: `None`.
            log (Logger, optional): Логгер. По умолчанию: `None`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `None`.
        """
        self.name = name
        self.config = config or QueueConfig()
        self.storage = storage
        self.log = (
            log.with_subname("Broker")
            if log
            else Logger(
                name=self.name,
                subname="Broker",
                default_level=self.config.logs_default_level_server,
                format=self.config.logs_format,
            )
        )
        self.plugins: Dict[str, List["BasePlugin"]] = {}

        self.init_plugins()

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
            dict,
            Doc(
                """
                    Дополнительные параметры задачи.
                    """
            ),
        ] = None,
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
    ) -> Union[Task, None]:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def start(
        self,
        worker: Annotated[
            "BaseWorker",
            Doc(
                """
                    Класс Воркера.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ) -> None:
        """Запуск Брокера. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever`.

        Args:
            worker (BaseWorker, optional): класс Воркера. По умолчанию: `None`.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
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

    def flush_all(self) -> None:
        """Удалить все данные."""
        pass

    def init_plugins(self):
        """Инициализация плагинов."""
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

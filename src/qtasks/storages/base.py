from abc import ABC, abstractmethod
from typing import Optional, Union
from typing_extensions import Annotated, Doc
from uuid import UUID
from typing import TYPE_CHECKING

from qtasks.configs.config import QueueConfig
from qtasks.configs.config_observer import ConfigObserver
from qtasks.logs import Logger
from qtasks.schemas.task import Task
from qtasks.schemas.task_exec import TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusErrorSchema, TaskStatusNewSchema, TaskStatusSuccessSchema

if TYPE_CHECKING:
    from qtasks.configs.base import BaseGlobalConfig
    from qtasks.plugins.base import BasePlugin


class BaseStorage(ABC):
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
    
    def __init__(self,
            name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя проекта. Это имя можно использовать для тегов для Storage.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            global_config: Annotated[
                Optional["BaseGlobalConfig"],
                Doc(
                    """
                    Глобальный конфиг.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,

            log: Annotated[
                Optional[Logger],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.logs.Logger`.
                    """
                )
            ] = None,
            config: Annotated[
                Optional[ConfigObserver],
                Doc(
                    """
                    Логгер.
                    
                    По умолчанию: `qtasks.configs.config_observer.ConfigObserver`.
                    """
                )
            ] = None
        ):
        self.name = name
        self.client = None
        self.global_config: "BaseGlobalConfig"|None = global_config

        self.config = config or ConfigObserver(QueueConfig())
        self.log = log.with_subname("Storage") if log else Logger(name=self.name, subname="Storage", default_level=self.config.logs_default_level, format=self.config.logs_format)
        self.plugins: dict[str, "BasePlugin"] = {}
        pass
    
    @abstractmethod
    def add(self,
            uuid: Annotated[
                Union[UUID|str],
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ],
            task_status: Annotated[
                TaskStatusNewSchema,
                Doc(
                    """
                    Схема статуса новой задачи.
                    """
                )
            ]
        ) -> None:
        """Добавление задачи в хранилище.

        Args:
            uuid (UUID | str): UUID задачи.
            task_status (TaskStatusNewSchema): Схема статуса новой задачи.
        """
        pass
    
    @abstractmethod
    def get(self,
            uuid: Annotated[
                Union[UUID|str],
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ]
        ) -> Task|None:
        """Получение информации о задаче.

        Args:
            uuid (UUID|str): UUID задачи.

        Returns:
            Task|None: Если есть информация о задаче, возвращает `schemas.task.Task`, иначе `None`.
        """
        pass
    
    @abstractmethod
    def get_all(self) -> list[Task]:
        """Получить все задачи.

        Returns:
            list[Task]: Массив задач.
        """
        pass
    
    @abstractmethod
    def update(self,
            **kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы обновления типа kwargs.
                    """
                )
            ]
        ) -> None:
        """Обновляет информацию о задаче.
        
        Args:
            kwargs (dict, optional): данные задачи типа kwargs.
        """
        pass
    
    @abstractmethod
    def start(self):
        """Запускает хранилище. Эта функция задействуется основным экземпляром `QueueTasks` после запуске функции `run_forever`."""
        pass
    
    @abstractmethod
    def stop(self):
        """Останавливает хранилище. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever`."""
        pass
    
    def add_plugin(self, plugin: "BasePlugin", name: Optional[str] = None) -> None:
        """
        Добавить плагин.

        Args:
            plugin (Type[BasePlugin]): Класс плагина.
            name (str, optional): Имя плагина. По умолчанию: `None`.
        """
        self.plugins.update({str(plugin.name or name): plugin})
        
    def remove_finished_task(self,
            task_broker: Annotated[
                TaskPrioritySchema,
                Doc(
                    """
                    Схема приоритетной задачи.
                    """
                )
            ],
            model: Annotated[
                Union[TaskStatusNewSchema|TaskStatusErrorSchema],
                Doc(
                    """
                    Модель результата задачи.
                    """
                )
            ]
        ) -> None:
        """Обновляет данные хранилища через функцию `self.storage.remove_finished_task`.

        Args:
            task_broker (TaskPrioritySchema): Схема приоритетной задачи.
            model (TaskStatusNewSchema | TaskStatusErrorSchema): Модель результата задачи.
        """
        pass
    
    def _delete_finished_tasks(self, **kwargs) -> None:
        pass
    
    def _running_older_tasks(self, **kwargs) -> None:
        pass
    
    def update_config(self,
            config: Annotated[
                QueueConfig,
                Doc(
                    """
                    Конфиг.
                    """
                )
            ]
        ) -> None:
        """Обновляет конфиг брокера.

        Args:
            config (QueueConfig): Конфиг.
        """
        self.config = config
        return
    
    def flush_all(self):
        pass
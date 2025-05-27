from abc import ABC, abstractmethod
from typing import Optional, Type, Union
from uuid import UUID
from typing_extensions import Annotated, Doc
from typing import TYPE_CHECKING

from qtasks.logs import Logger
from qtasks.schemas.task import Task
from qtasks.configs.config import QueueConfig

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
    
    def __init__(self,
            name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя проекта. Это имя можно использовать для тегов для Брокеров.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            storage: Annotated[
                Optional["BaseStorage"],
                Doc(
                    """
                    Хранилище `qtasks.storages.base.BaseStorage`.
                    
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
            ] = None
        ):
        self.name = name
        self.client = None
        self.config = QueueConfig()
        self.storage = storage
        self.log = log.with_subname("Broker") if log else Logger(name=self.name, subname="Broker", default_level=self.config.logs_default_level, format=self.config.logs_format)
        self.plugins: dict[str, "BasePlugin"] = {}
        pass
    
    @abstractmethod
    def add(self,
            task_name: Annotated[
                str,
                Doc(
                    """
                    Имя задачи.
                    """
                )
            ],
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    
                    По умолчанию: `0`.
                    """
                )
            ] = 0,
            *args: Annotated[
                tuple,
                Doc(
                    """
                    Аргументы задачи типа args.
                    """
                )
            ],
            **kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы задачи типа kwargs.
                    """
                )
            ]
        ):
        """Добавление задачи в брокер.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умоланию: 0.
            args (tuple, optional): Аргументы задачи типа args.
            kwargs (dict, optional): Аргументы задачи типа kwargs.

        Returns:
            Task: `schemas.task.Task`
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
    def update(self,
            **kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы обновления для хранилища типа kwargs.
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
    def start(self,
            worker: Annotated[
                "BaseWorker",
                Doc(
                    """
                    Класс Воркера.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None
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
    
    def include_plugin(self, 
            plugin: Annotated[
                "BasePlugin",
                Doc(
                    """
                    Плагин.
                    """
                )
            ],
            name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя плагина.
                    
                    По умолчанию: `plugin.name`.
                    """
                )
            ] = None
            ) -> None:
        """Добавить плагин в класс.

        Args:
            plugin (BasePlugin): Плагин
            name (str, optional): Имя плагина. По умолчанию: `plugin.name`.
        """
        self.plugins.update({str(name or plugin.name): plugin})
        
    def _plugin_trigger(self, name: str, *args, **kwargs):
        """Триггер плагина

        Args:
            name (str): Имя триггера.
            args (tuple, optional): Аргументы триггера типа args.
            kwargs (dict, optional): Аргументы триггера типа kwargs.
        """
        for plugin in self.plugins.values():
            plugin.trigger(name=name, *args, **kwargs)
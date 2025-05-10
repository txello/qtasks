from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Type
from uuid import UUID
from typing_extensions import Annotated, Doc

from qtasks.configs.config import QueueConfig
from qtasks.schemas.inits import InitsExecSchema

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.plugins.base import BasePlugin


class BaseWorker(ABC):
    """
    `BaseWorker` - Абстрактный класс, который является фундаментом для Воркеров.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.workers.base import BaseWorker
    
    class MyWorker(BaseWorker):
        def __init__(self, name: str = None, broker: BaseBroker = None):
            super().__init__(name=name, broker=broker)
            pass
    ```
    """
    
    def __init__(self,
            name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя проекта. Это имя может быть использовано Воркером.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            broker: Annotated[
                Optional["BaseBroker"],
                Doc(
                    """
                    Брокер `qtasks.brokers.base.BaseBroker`.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None
        ):
        self.name = name
        self.broker = broker
        self.config = QueueConfig()
        self.init_worker_running: list[InitsExecSchema] = []
        self.init_task_running: list[InitsExecSchema] = []
        self.init_task_stoping: list[InitsExecSchema] = []
        self.init_worker_stoping: list[InitsExecSchema] = []
        self.plugins: dict[str, "BasePlugin"] = {}
        
        self.num_workers = 0
    
    @abstractmethod
    def add(self,
            name: Annotated[
                str,
                Doc(
                    """
                    Имя задачи.
                    """
                )
            ],
            uuid: Annotated[
                UUID,
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ],
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    """
                )
            ],
            created_at: Annotated[
                float,
                Doc(
                    """
                    Создание задачи в формате timestamp.
                    """
                )
            ],
            args: Annotated[
                tuple,
                Doc(
                    """
                    Аргументы задачи типа args.
                    """
                )
            ],
            kwargs: Annotated[
                dict,
                Doc(
                    """
                    Аргументы задачи типа kwargs.
                    """
                )
            ]
        ) -> None:
        """Добавление задачи в очередь.

        Args:
            name (str): Имя задачи.
            uuid (UUID): UUID задачи.
            priority (int): Приоритет задачи.
            created_at (float): Создание задачи в формате timestamp.
            args (tuple): Аргументы задачи типа args.
            kwargs (dict): Аргументы задачи типа kwargs.
        """
        pass
    
    @abstractmethod
    def start(self,
            num_workers: Annotated[
                Optional[int],
                Doc(
                    """
                    Количество воркеров.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None
        ):
        """Запускает несколько обработчиков задач. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever`.

        Args:
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
        """
        pass
    
    @abstractmethod
    def stop(self):
        """Останавливает воркеры. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever`."""
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
    
    def add_plugin(self, plugin: "BasePlugin", name: Optional[str] = None) -> None:
        """
        Добавить плагин.

        Args:
            plugin (Type[BasePlugin]): Класс плагина.
            name (str, optional): Имя плагина. По умолчанию: `None`.
        """
        self.plugins.update({str(plugin.name or name): plugin})
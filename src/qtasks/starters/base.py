from abc import ABC, abstractmethod
from qtasks.configs.config_observer import ConfigObserver
from qtasks.logs import Logger
from typing import TYPE_CHECKING, Optional, Type
from typing_extensions import Annotated, Doc


from qtasks.schemas.inits import InitsExecSchema
from qtasks.configs.config import QueueConfig

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.workers.base import BaseWorker
    from qtasks.plugins.base import BasePlugin


class BaseStarter(ABC):
    """
    `BaseStarter` - Абстрактный класс, который является фундаментом для Стартеров.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.starters.base import BaseStarter
    
    class MyStarter(BaseStarter):
        def __init__(self, name: str = None, broker = None, worker = None):
            super().__init__(name=name, broker = None, worker = None)
            pass
    ```
    """
    
    def __init__(self,
            name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя проекта. Это имя можно использовать для тегов для Стартеров.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            broker: Annotated[
                Optional["BaseBroker"],
                Doc(
                    """
                    Брокер.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            worker: Annotated[
                Optional["BaseWorker"],
                Doc(
                    """
                    Воркер.
                    
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
        self.config = config or ConfigObserver(QueueConfig())
        self.log = log.with_subname("Starter") if log else Logger(name=self.name, subname="Starter", default_level=self.config.logs_default_level, format=self.config.logs_format)
        
        self.broker = broker
        self.worker = worker
        
        self._inits: dict[str, list[InitsExecSchema]] = {
            "init_starting":[],
            "init_stoping":[]
        }
        
        self.plugins: dict[str, "BasePlugin"] = {}
        
    @abstractmethod
    def start(self) -> None:
        """Запуск Стартера. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever`."""
    
    @abstractmethod
    def stop(self):
        """Останавливает Стартер. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever`."""
        pass
    
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
        self.plugins.update({str(plugin.name or name): plugin})

    def update_configs(self,
            config: Annotated[
                QueueConfig,
                Doc(
                    """
                    Конфиг.
                    """
                )
            ]
        ):
        """Обновить конфиги всем компонентам.

        Args:
            config (QueueConfig): Конфиг.
        """
        self.log.debug("Конфиг обновлён")
        if self.worker:
            self.worker.update_config(config)
        if self.broker:
            self.broker.update_config(config)
            if self.broker.storage:
                self.broker.storage.update_config(config)
                if self.broker.storage.global_config:
                    self.broker.storage.global_config.update_config(config)
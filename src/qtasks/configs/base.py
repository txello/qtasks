from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional
from typing_extensions import Annotated, Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin


class BaseGlobalConfig(ABC):
    """
    `BaseGlobalConfig` - Абстрактный класс, который является фундаментом для Глобального Конфига.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.configs.base import BaseGlobalConfig
    
    class MyGlobalConfig(BaseGlobalConfig):
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
                    Имя проекта. Это имя можно использовать для тегов для GlobalConfig.
                    
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
                Optional[QueueConfig],
                Doc(
                    """
                    Конфиг.
                    
                    По умолчанию: `qtasks.configs.config.QueueConfig`.
                    """
                )
            ] = None
        ):
        self.name = name
        self.client = None
        self.config = config or QueueConfig()
        
        self.log = log.with_subname("GlobalConfig") if log else Logger(name=self.name, subname="GlobalConfig", default_level=self.config.logs_default_level, format=self.config.logs_format)
        self.plugins: dict[str, "BasePlugin"] = {}
        pass
    
    @abstractmethod
    def set(self, **kwargs) -> None:
        """Добавить новое значение.

        Args:
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.
        """
        pass
    
    @abstractmethod
    def get(self, key: str, name: str) -> Any:
        """Получить значение.

        Args:
            key (str): Ключ.
            name (str): Имя.

        Returns:
            Any: Значение.
        """
        pass
    
    @abstractmethod
    def get_all(self, key: str) -> dict[Any] | list[Any] | tuple[Any]:
        """Получить все значения.

        Args:
            key (str): Ключ.

        Returns:
            dict[Any] | list[Any] | tuple[Any]: Значения.
        """
        pass
    
    @abstractmethod
    def get_match(self, match: str) -> Any | dict[Any] | list[Any] | tuple[Any]:
        """Получить значения по паттерну.

        Args:
            match (str): Паттерн.

        Returns:
            Any | dict[Any] | list[Any] | tuple[Any]: Значение или Значения.
        """
        pass
    
    @abstractmethod
    def start(self
        ) -> None:
        """Запуск Брокера. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever."""
        
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Останавливает Глобальный Конфиг. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever."""
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
        self.plugins.update({str(plugin.name or name): plugin})
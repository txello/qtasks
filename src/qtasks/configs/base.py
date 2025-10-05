"""Base Configurations."""

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Union,
    overload,
)
from typing_extensions import Annotated, Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.plugins.base import BasePlugin
    from qtasks.events.base import BaseEvents


class BaseGlobalConfig(Generic[TAsyncFlag], ABC):
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

    def __init__(
        self,
        name: Annotated[
            Optional[str],
            Doc(
                """
                    Имя проекта. Это имя можно использовать для тегов для GlobalConfig.

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
        """Инициализация контекста.

        Args:
            name (str, optional): Имя проекта. По умолчанию: `None`.
            log (Logger, optional): Логгер. По умолчанию: `None`.
            config (QueueConfig, optional): Конфигурация. По умолчанию: `None`.
            events (BaseEvents, optional): События. По умолчанию: `None`.
        """
        self.name = name
        self.config_name: Optional[str] = None

        self.config = config or QueueConfig()
        self.log = (
            log.with_subname("GlobalConfig")
            if log
            else Logger(
                name=self.name or "QueueTasks",
                subname="GlobalConfig",
                default_level=self.config.logs_default_level_server,
                format=self.config.logs_format,
            )
        )
        self.events = events
        self.client = None
        self.plugins: Dict[str, List["BasePlugin"]] = {}

        self.init_plugins()

    @overload
    def set(self: "BaseGlobalConfig[Literal[False]]", **kwargs) -> None: ...

    @overload
    async def set(self: "BaseGlobalConfig[Literal[True]]", **kwargs) -> None: ...

    @abstractmethod
    def set(self, **kwargs) -> Union[None, Awaitable[None]]:
        """Добавить новое значение.

        Args:
            kwargs (dict, optional): kwags задачи. По умолчанию `{}`.
        """
        pass

    @overload
    def get(self: "BaseGlobalConfig[Literal[False]]", key: str, name: str) -> Any: ...

    @overload
    async def get(
        self: "BaseGlobalConfig[Literal[True]]", key: str, name: str
    ) -> Any: ...

    @abstractmethod
    def get(self, key: str, name: str) -> Union[Any, Awaitable[Any]]:
        """Получить значение.

        Args:
            key (str): Ключ.
            name (str): Имя.

        Returns:
            Any: Значение.
        """
        pass

    @overload
    def get_all(
        self: "BaseGlobalConfig[Literal[False]]", key: str
    ) -> Union[dict, list, tuple]: ...

    @overload
    async def get_all(
        self: "BaseGlobalConfig[Literal[True]]", key: str
    ) -> Union[dict, list, tuple]: ...

    @abstractmethod
    def get_all(
        self, key: str
    ) -> Union[Union[dict, list, tuple], Awaitable[Union[dict, list, tuple]]]:
        """Получить все значения.

        Args:
            key (str): Ключ.

        Returns:
            Dict[str, Any] | List[Any] | Tuple[Any]: Значения.
        """
        pass

    @overload
    def get_match(self: "BaseGlobalConfig[Literal[False]]", match: str) -> Any: ...

    @overload
    async def get_match(self: "BaseGlobalConfig[Literal[True]]", match: str) -> Any: ...

    @abstractmethod
    def get_match(
        self, match: str
    ) -> Union[Union[dict, list, tuple], Awaitable[Union[dict, list, tuple]]]:
        """Получить значения по паттерну.

        Args:
            match (str): Паттерн.

        Returns:
            Any | Dict[str, Any] | List[Any] | Tuple[Any]: Значение или Значения.
        """
        pass

    @overload
    def start(self: "BaseGlobalConfig[Literal[False]]") -> None: ...

    @overload
    async def start(self: "BaseGlobalConfig[Literal[True]]") -> None: ...

    @abstractmethod
    def start(self) -> Union[None, Awaitable[None]]:
        """Запуск Брокера. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever."""
        pass

    @overload
    def stop(self: "BaseGlobalConfig[Literal[False]]") -> None: ...

    @overload
    async def stop(self: "BaseGlobalConfig[Literal[True]]") -> None: ...

    @abstractmethod
    def stop(self) -> Union[None, Awaitable[None]]:
        """Останавливает Глобальный Конфиг. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever."""
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

    def init_plugins(self):
        """Инициализация плагинов."""
        pass

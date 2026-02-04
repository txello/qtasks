"""Base Configurations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Literal,
    Optional,
    overload,
)

from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.logs import Logger
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.events.base import BaseEvents
    from qtasks.plugins.base import BasePlugin


class BaseGlobalConfig(Generic[TAsyncFlag], ABC):
    """
    `BaseGlobalConfig` - An abstract class that is the foundation for the Global Config.

    ## Example

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
            str | None,
            Doc("""
                    Project name. This name can be used for tags for GlobalConfig.

                    Default: `None`.
                    """),
        ] = None,
        log: Annotated[
            Logger | None,
            Doc("""
                    Logger.

                    Default: `qtasks.logs.Logger`.
                    """),
        ] = None,
        config: Annotated[
            QueueConfig | None,
            Doc("""
                    Config.

                    Default: `qtasks.configs.config.QueueConfig`.
                    """),
        ] = None,
        events: Annotated[
            Optional[BaseEvents],
            Doc("""
                    Events.

                    Default: `None`.
                    """),
        ] = None,
    ):
        """
        Initializing the context.

        Args:
            name (str, optional): Project name. Default: `None`.
            log (Logger, optional): Logger. Default: `None`.
            config (QueueConfig, optional): Configuration. Default: `None`.
            events (BaseEvents, optional): Events. Default: `None`.
        """
        self.name = name
        self.config_name: str | None = None

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
        self.plugins: dict[str, list[BasePlugin]] = {}

        self.init_plugins()

    @overload
    def set(self: BaseGlobalConfig[Literal[False]], **kwargs) -> None: ...

    @overload
    async def set(self: BaseGlobalConfig[Literal[True]], **kwargs) -> None: ...

    @abstractmethod
    def set(self, **kwargs) -> None | Awaitable[None]:
        """
        Add new value.

        Args:
            kwargs (dict, optional): kwags tasks. Defaults to `{}`.
        """
        pass

    @overload
    def get(self: BaseGlobalConfig[Literal[False]], key: str, name: str) -> Any: ...

    @overload
    async def get(
        self: BaseGlobalConfig[Literal[True]], key: str, name: str
    ) -> Any: ...

    @abstractmethod
    def get(self, key: str, name: str) -> Any | Awaitable[Any]:
        """
        Get value.

        Args:
            key (str): Key.
            name (str): Name.

        Returns:
            Any: Value.
        """
        pass

    @overload
    def get_all(
        self: BaseGlobalConfig[Literal[False]], key: str
    ) -> dict | list | tuple: ...

    @overload
    async def get_all(
        self: BaseGlobalConfig[Literal[True]], key: str
    ) -> dict | list | tuple: ...

    @abstractmethod
    def get_all(
        self, key: str
    ) -> dict | list | tuple | Awaitable[dict | list | tuple]:
        """
        Get all values.

        Args:
            key (str): Key.

        Returns:
            Dict[str, Any] | List[Any] | Tuple[Any]: Values.
        """
        pass

    @overload
    def get_match(self: BaseGlobalConfig[Literal[False]], match: str) -> Any: ...

    @overload
    async def get_match(self: BaseGlobalConfig[Literal[True]], match: str) -> Any: ...

    @abstractmethod
    def get_match(
        self, match: str
    ) -> dict | list | tuple | Awaitable[dict | list | tuple]:
        """
        Get values by pattern.

        Args:
            match (str): Pattern.

        Returns:
            Any | Dict[str, Any] | List[Any] | Tuple[Any]: Value or Values.
        """
        pass

    @overload
    def start(self: BaseGlobalConfig[Literal[False]]) -> None: ...

    @overload
    async def start(self: BaseGlobalConfig[Literal[True]]) -> None: ...

    @abstractmethod
    def start(self) -> None | Awaitable[None]:
        """Launching the Broker. This function is enabled by the main instance of `QueueTasks` via `run_forever."""
        pass

    @overload
    def stop(self: BaseGlobalConfig[Literal[False]]) -> None: ...

    @overload
    async def stop(self: BaseGlobalConfig[Literal[True]]) -> None: ...

    @abstractmethod
    def stop(self) -> None | Awaitable[None]:
        """Stops Global Config. This function is invoked by the main instance of `QueueTasks` after the `run_forever' function completes."""
        pass

    def update_config(
        self,
        config: Annotated[
            QueueConfig,
            Doc("""
                    Config.
                    """),
        ],
    ) -> None:
        """
        Updates the broker config.

        Args:
            config (QueueConfig): Config.
        """
        self.config = config
        return

    def add_plugin(
        self,
        plugin: Annotated[
            BasePlugin,
            Doc("""
                    Plugin.
                    """),
        ],
        trigger_names: Annotated[
            list[str] | None,
            Doc("""
                    The name of the triggers for the plugin.

                    Default: Default: will be added to `Globals`.
                    """),
        ] = None,
    ) -> None:
        """
        Add a plugin to the class.

        Args:
            plugin (BasePlugin): Plugin
            trigger_names (List[str], optional): The name of the triggers for the plugin. Default: will be added to `Globals`.
        """
        trigger_names = trigger_names or ["Globals"]

        for name in trigger_names:
            if name not in self.plugins:
                self.plugins.update({name: [plugin]})
            else:
                self.plugins[name].append(plugin)
        return

    def init_plugins(self):
        """Initializing plugins."""
        pass

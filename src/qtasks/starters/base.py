"""Base starter."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import (
    TYPE_CHECKING,
    Annotated,
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
    from qtasks.brokers.base import BaseBroker
    from qtasks.events.base import BaseEvents
    from qtasks.plugins.base import BasePlugin
    from qtasks.workers.base import BaseWorker


class BaseStarter(Generic[TAsyncFlag], ABC):
    """
    `BaseStarter` - An abstract class that is the foundation for Starters.
    
        ## Example
    
        ```python
        from qtasks import QueueTasks
        from qtasks.starters.base import BaseStarter
    
        class MyStarter(BaseStarter):
            def __init__(self, name: str = None, broker = None, worker = None):
                super().__init__(name=name, broker = None, worker = None)
                pass
        ```
    """

    def __init__(
        self,
        name: Annotated[
            str | None,
            Doc(
                """
                    Имя проекта. Это имя можно использовать для тегов для Стартеров.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        broker: Annotated[
            Optional[BaseBroker],
            Doc(
                """
                    Брокер.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        worker: Annotated[
            Optional[BaseWorker],
            Doc(
                """
                    Воркер.

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
        """
        Basic starter initialization.
        
                Args:
                    name (str, optional): Project name. Default: None.
                    broker (BaseBroker, optional): Broker. Default: None.
                    worker (BaseWorker, optional): Worker. Default: None.
                    log (Logger, optional): Logger. Default: `qtasks.logs.Logger`.
                    config (QueueConfig, optional): Config. Default: `qtasks.configs.config.QueueConfig`.
                    events (BaseEvents, optional): Events. Default: `None`.
        """
        self.name = name
        self.config = config or QueueConfig()
        self.log = (
            log.with_subname("Starter")
            if log
            else Logger(
                name=self.name or "QueueTasks",
                subname="Starter",
                default_level=self.config.logs_default_level_server,
                format=self.config.logs_format,
            )
        )
        self.events = events

        self.broker = broker
        self.worker = worker

        self.plugins: dict[str, list[BasePlugin]] = {}

        self.init_plugins()

    @overload
    def start(self: BaseStarter[Literal[False]], *args, **kwargs) -> None: ...

    @overload
    def start(self: BaseStarter[Literal[True]], *args, **kwargs) -> None: ...

    @abstractmethod
    def start(self, *args, **kwargs) -> None:
        """Starter launch. This function is enabled by the main `QueueTasks` instance via `run_forever`."""
        pass

    @overload
    def stop(self: BaseStarter[Literal[False]]) -> None: ...

    @overload
    async def stop(self: BaseStarter[Literal[True]]) -> None: ...

    @abstractmethod
    def stop(self) -> None | Awaitable[None]:
        """Stops the Starter. This function is invoked by the main `QueueTasks` instance after the `run_forever` function completes."""
        pass

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

    def update_configs(
        self,
        config: Annotated[
            QueueConfig,
            Doc(
                """
                    Конфиг.
                    """
            ),
        ],
    ):
        """
        Update configs for all components.
        
                Args:
                    config (QueueConfig): Config.
        """
        self.log.debug("Конфиг обновлен")
        if self.worker:
            self.worker.update_config(config)
        if self.broker:
            self.broker.update_config(config)
            if self.broker.storage:
                self.broker.storage.update_config(config)
                if self.broker.storage.global_config:
                    self.broker.storage.global_config.update_config(config)

    def init_plugins(self):
        """Initializing plugins."""
        pass

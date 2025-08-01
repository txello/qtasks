"""Base starter."""

from abc import ABC, abstractmethod
from qtasks.logs import Logger
from typing import TYPE_CHECKING, Dict, List, Optional
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

    def __init__(
        self,
        name: Annotated[
            Optional[str],
            Doc(
                """
                    Имя проекта. Это имя можно использовать для тегов для Стартеров.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        broker: Annotated[
            Optional["BaseBroker"],
            Doc(
                """
                    Брокер.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        worker: Annotated[
            Optional["BaseWorker"],
            Doc(
                """
                    Воркер.

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
        """Инициализация базового стартера.

        Args:
            name (str, optional): Имя проекта. По умолчанию: None.
            broker (BaseBroker, optional): Брокер. По умолчанию: None.
            worker (BaseWorker, optional): Воркер. По умолчанию: None.
            log (Logger, optional): Логгер. По умолчанию: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `qtasks.configs.config.QueueConfig`.
        """
        self.name = name
        self.config = config or QueueConfig()
        self.log = (
            log.with_subname("Starter")
            if log
            else Logger(
                name=self.name,
                subname="Starter",
                default_level=self.config.logs_default_level_server,
                format=self.config.logs_format,
            )
        )

        self.broker = broker
        self.worker = worker

        self._inits: Dict[str, List[InitsExecSchema]] = {
            "init_starting": [],
            "init_stoping": [],
        }

        self.plugins: Dict[str, List["BasePlugin"]] = {}

        self.init_plugins()

    @abstractmethod
    def start(self) -> None:
        """Запуск Стартера. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever`."""

    @abstractmethod
    def stop(self):
        """Останавливает Стартер. Эта функция задействуется основным экземпляром `QueueTasks` после завершения функции `run_forever`."""
        pass

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
        """Обновить конфиги всем компонентам.

        Args:
            config (QueueConfig): Конфиг.
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
        """Инициализация плагинов."""
        pass

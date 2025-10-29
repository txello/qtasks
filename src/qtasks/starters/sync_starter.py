"""Sync Starter."""

from typing import TYPE_CHECKING, Annotated, Literal, Optional

from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.events.sync_events import SyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import SyncPluginMixin

from .base import BaseStarter

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.events.base import BaseEvents
    from qtasks.plugins.base import BasePlugin
    from qtasks.workers.base import BaseWorker


class SyncStarter(BaseStarter[Literal[False]], SyncPluginMixin):
    """
    Стартер, запускающий Компоненты.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import SyncRedisBroker
    from qtasks.workers import SyncWorker
    from qtasks.starters import SyncStarter

    broker = SyncRedisBroker(name="QueueTasks", url="redis://localhost:6379/2")
    worker = SyncWorker(name="QueueTasks", broker=broker)

    app = QueueTasks(worker=worker, broker=broker)

    starter = SyncStarter(name="QueueTasks", worker=worker, broker=broker)
    app.run_forever(starter=starter)
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
            Optional["BaseEvents"],
            Doc(
                """
                    События.

                    По умолчанию: `qtasks.events.SyncEvents`.
                    """
            ),
        ] = None,
    ):
        """Инициализация асинхронного стартера.

        Args:
            name (str, optional): Имя проекта. По умолчанию: None.
            broker (BaseBroker, optional): Брокер. По умолчанию: None.
            worker (BaseWorker, optional): Воркер. По умолчанию: None.
            log (Logger, optional): Логгер. По умолчанию: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Конфиг. По умолчанию: `qtasks.configs.config.QueueConfig`.
            events (BaseEvents, optional): События. По умолчанию: `qtasks.events.SyncEvents`.
        """
        super().__init__(
            name=name,
            broker=broker,
            worker=worker,
            log=log,
            config=config,
            events=events,
        )
        self.events: BaseEvents[Literal[False]] = self.events or SyncEvents()
        self.worker: BaseWorker[Literal[False]]
        self.broker: BaseBroker[Literal[False]]

        self._started_plugins: set[BasePlugin] = set()

    def start(
        self,
        num_workers: Annotated[
            int,
            Doc(
                """
                    Количество запущенных воркеров.

                    По умолчанию: `4`.
                    """
            ),
        ] = 4,
        reset_config: Annotated[
            bool,
            Doc(
                """
                    Обновить config у воркера и брокера.

                    По умолчанию: `True`.
                    """
            ),
        ] = True,
        plugins: Annotated[
            dict[str, list["BasePlugin"]] | None,
            Doc(
                """
                    Плагины для воркера и брокера.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ) -> None:
        """Запуск Стартера. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever`.

        Args:
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
            reset_config (bool, optional): Обновить config у воркера и брокера. По умолчанию: True.
            plugins (Dict[str, BasePlugin] | None, optional): Плагины. По умолчанию: None.
        """
        if self.log:
            self.log.info("Запуск QueueTasks...")

        if plugins:
            self.plugins.update(plugins)

        if reset_config:
            self.update_configs(self.config)

        try:
            self._start(num_workers=num_workers)
        except KeyboardInterrupt:
            self.stop()

    def _start(self, num_workers=4):
        """Запуск Стартера синхронно.

        Args:
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
        """
        self._plugin_trigger("starter_start", starter=self)
        for plugin in [i for y in self.plugins.values() for i in y]:
            if plugin not in self._started_plugins:
                self._started_plugins.add(plugin)
                plugin.start()

        self.events.fire(
            "starting", starter=self, worker=self.worker, broker=self.broker
        )

        self.worker.start(num_workers)
        self.broker.start(self.worker)

        try:
            while True:
                pass  # Бесконечный цикл выполнения
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Останавливает все компоненты."""
        if self.log:
            self.log.info("Остановка QueueTasks...")
        self._plugin_trigger("starter_stop", starter=self)

        if self.broker:
            self.broker.stop()
        if self.worker:
            self.worker.stop()
        if self.broker.storage:
            self.broker.storage.stop()
        if self.broker.storage.global_config:
            self.broker.storage.global_config.stop()

        self.events.fire(
            "stopping", starter=self, worker=self.worker, broker=self.broker
        )

        for model_plugin in [i for y in self.plugins.values() for i in y]:
            model_plugin.stop()

        for plugin in self._started_plugins:
            plugin.stop()
        self._started_plugins.clear()

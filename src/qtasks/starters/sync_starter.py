"""Sync Starter."""
from __future__ import annotations

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
    Starter that starts the Components.

    ## Example

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
            Doc("""
                    Project name. This name can be used for tags for Starters.

                    Default: `None`.
                    """),
        ] = None,
        broker: Annotated[
            Optional[BaseBroker],
            Doc("""
                    Broker.

                    Default: `None`.
                    """),
        ] = None,
        worker: Annotated[
            Optional[BaseWorker],
            Doc("""
                    Worker.

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

                    Default: `qtasks.events.SyncEvents`.
                    """),
        ] = None,
    ):
        """
        Initialization of an synchronous starter.

        Args:
            name (str, optional): Project name. Default: None.
            broker (BaseBroker, optional): Broker. Default: None.
            worker (BaseWorker, optional): Worker. Default: None.
            log (Logger, optional): Logger. Default: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Config. Default: `qtasks.configs.config.QueueConfig`.
            events (BaseEvents, optional): Events. Default: `qtasks.events.SyncEvents`.
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
            Doc("""
                    Number of running workers.

                    Default: `4`.
                    """),
        ] = 4,
        reset_config: Annotated[
            bool,
            Doc("""
                    Update the config of the worker and broker.

                    Default: `True`.
                    """),
        ] = True,
        plugins: Annotated[
            dict[str, list[BasePlugin]] | None,
            Doc("""
                    Plugins for worker and broker.

                    Default: `None`.
                    """),
        ] = None,
    ) -> None:
        """Starter launch. This function is enabled by the main `QueueTasks` instance via `run_forever`.

        Args:
            num_workers (int, optional): Number of workers. Default: 4.
            reset_config (bool, optional): Update the config of the worker and broker. Default: True.
            plugins (Dict[str, BasePlugin] | None, optional): Plugins. Default: None.
        """
        if self.log:
            self.log.info("Starting QueueTasks...")

        if plugins:
            self.plugins.update(plugins)

        if reset_config:
            self.update_configs(self.config)

        try:
            self._start(num_workers=num_workers)
        except KeyboardInterrupt:
            self.stop()

    def _start(self, num_workers=4):
        """Starter starts synchronously.

        Args:
            num_workers (int, optional): Number of workers. Default: 4.
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
                pass
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stops all components."""
        if self.log:
            self.log.info("Stopping QueueTasks...")
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

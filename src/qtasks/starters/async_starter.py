"""Async Starter."""
from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Annotated, Literal, Optional

from typing_extensions import Doc

from qtasks.configs.config import QueueConfig
from qtasks.events.async_events import AsyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin

from .base import BaseStarter

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.events.base import BaseEvents
    from qtasks.plugins.base import BasePlugin
    from qtasks.workers.base import BaseWorker


class AsyncStarter(BaseStarter[Literal[True]], AsyncPluginMixin):
    """
    Starter that starts the Components.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.brokers import AsyncRedisBroker
    from qtasks.workers import AsyncWorker
    from qtasks.starters import AsyncStarter

    broker = AsyncRedisBroker(name="QueueTasks", url="redis://localhost:6379/2")
    worker = AsyncWorker(name="QueueTasks", broker=broker)

    app = QueueTasks(worker=worker, broker=broker)

    starter = AsyncStarter(name="QueueTasks", worker=worker, broker=broker)
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

                    Default: `qtasks.events.AsyncEvents`.
                    """),
        ] = None,
    ):
        """
        Initialization of an asynchronous starter.

        Args:
            name (str, optional): Project name. Default: None.
            broker (BaseBroker, optional): Broker. Default: None.
            worker (BaseWorker, optional): Worker. Default: None.
            log (Logger, optional): Logger. Default: `qtasks.logs.Logger`.
            config (QueueConfig, optional): Config. Default: `qtasks.configs.config.QueueConfig`.
            events (BaseEvents, optional): Events. Default: `qtasks.events.AsyncEvents`.
        """
        super().__init__(
            name=name,
            broker=broker,
            worker=worker,
            log=log,
            config=config,
            events=events,
        )
        self.events: BaseEvents[Literal[True]] = self.events or AsyncEvents()
        self.worker: BaseWorker[Literal[True]]
        self.broker: BaseBroker[Literal[True]]

        self._global_loop: asyncio.AbstractEventLoop | None = None
        self._started_plugins: set[BasePlugin] = set()

    def start(
        self,
        loop: Annotated[
            asyncio.AbstractEventLoop | None,
            Doc("""
                    Asynchronous loop.

                    Default: `None`.
                    """),
        ] = None,
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
        """
        Starter launch. This function is enabled by the main `QueueTasks` instance via `run_forever`.

        Args:
            loop (asyncio.AbstractEventLoop, optional): Asynchronous loop. Default: None.
            num_workers (int, optional): Number of workers. Default: 4.
            reset_config (bool, optional): Update the config of the worker and broker. Default: True.
            plugins (Dict[str, List[BasePlugin]] | None, optional): Plugins. Default: None.
        """
        if self.log:
            self.log.info("Starting QueueTasks...")

        if plugins:
            self.plugins.update(plugins)

        if reset_config:
            self.update_configs(self.config)

        if loop:
            self._global_loop = loop
        else:
            try:
                self._global_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._global_loop)
            except RuntimeError:
                self._global_loop = asyncio.get_event_loop()

        try:
            self._global_loop.run_until_complete(self._start(num_workers))
        except KeyboardInterrupt:
            with contextlib.suppress(RuntimeError, KeyboardInterrupt):
                self._global_loop.run_until_complete(self.stop())

    async def _start(self, num_workers=4):
        """
        Launching the Starter asynchronously.

        Args:
            num_workers (int, optional): Number of workers. Default: 4.
        """
        await self._plugin_trigger("starter_start", starter=self)
        for plugin in [i for y in self.plugins.values() for i in y]:
            if plugin not in self._started_plugins:
                plugin: BasePlugin[Literal[True]]
                self._started_plugins.add(plugin)
                await plugin.start()

        await self.events.fire(
            "starting", starter=self, worker=self.worker, broker=self.broker
        )

        worker_task = asyncio.create_task(self.worker.start(num_workers))
        broker_task = asyncio.create_task(self.broker.start(self.worker))

        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(broker_task, worker_task)

    async def stop(self):
        """Stops all components."""
        if self.log:
            self.log.info("Stopping QueueTasks...")
        await self._plugin_trigger("starter_stop", starter=self)

        if self.broker:
            await self.broker.stop()
        if self.worker:
            await self.worker.stop()
        if self.broker.storage:
            await self.broker.storage.stop()
        if self.broker.storage.global_config:
            await self.broker.storage.global_config.stop()

        if self._global_loop and self._global_loop.is_running():
            self._global_loop.stop()

        await self.events.fire(
            "stopping", starter=self, worker=self.worker, broker=self.broker
        )

        for model_plugin in [i for y in self.plugins.values() for i in y]:
            model_plugin: BasePlugin[Literal[True]]
            await model_plugin.stop()

        for plugin in self._started_plugins:
            plugin: BasePlugin[Literal[True]]
            await plugin.stop()
        self._started_plugins.clear()

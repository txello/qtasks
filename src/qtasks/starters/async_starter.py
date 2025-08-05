"""Async Starter."""

import asyncio
from typing import TYPE_CHECKING, Dict, Optional, Union
from typing_extensions import Annotated, Doc

from qtasks.configs.config import QueueConfig
from qtasks.events.async_events import AsyncEvents
from qtasks.logs import Logger
from qtasks.mixins.plugin import AsyncPluginMixin

from .base import BaseStarter

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.workers.base import BaseWorker
    from qtasks.plugins.base import BasePlugin
    from qtasks.events.base import BaseEvents


class AsyncStarter(BaseStarter, AsyncPluginMixin):
    """
    Стартер, запускающий Компоненты.

    ## Пример

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
        events: Annotated[
            Optional["BaseEvents"],
            Doc(
                """
                    События.

                    По умолчанию: `qtasks.events.AsyncEvents`.
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
            events (BaseEvents, optional): События. По умолчанию: `qtasks.events.AsyncEvents`.
        """
        super().__init__(
            name=name, broker=broker, worker=worker, log=log, config=config, events=events
        )
        self.events = self.events or AsyncEvents()

        self._global_loop: Union[asyncio.AbstractEventLoop, None] = None
        self._started_plugins: set[int] = set()

    def start(
        self,
        loop: Annotated[
            Optional[asyncio.AbstractEventLoop],
            Doc(
                """
                    Асинхронный loop.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
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
            Optional[Dict[str, "BasePlugin"]],
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
            loop (asyncio.AbstractEventLoop, optional): Асинхронный loop. По умолчанию: None.
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
            reset_config (bool, optional): Обновить config у воркера и брокера. По умолчанию: True.
            plugins (Dict[str, BasePlugin] | None, optional): Плагины. По умолчанию: None.
        """
        self.log.info("Запуск QueueTasks...")

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
            self._global_loop.run_until_complete(self.stop())

    async def _start(self, num_workers=4):
        """Запуск Стартера асинхронно.

        Args:
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
        """
        await self._plugin_trigger("starter_start", starter=self)
        for plugin in [i for y in self.plugins.values() for i in y]:
            if plugin not in self._started_plugins:
                self._started_plugins.add(plugin)
                await plugin.start()

        await self.events.fire("starting", starter=self, worker=self.worker, broker=self.broker)

        worker_task = asyncio.create_task(self.worker.start(num_workers))
        broker_task = asyncio.create_task(self.broker.start(self.worker))

        try:
            await asyncio.gather(broker_task, worker_task)
        except asyncio.CancelledError:
            pass

    async def stop(self):
        """Останавливает все компоненты."""
        self.log.info("Остановка QueueTasks...")
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

        await self.events.fire("stopping", starter=self, worker=self.worker, broker=self.broker)

        for model_plugin in [i for y in self.plugins.values() for i in y]:
            await model_plugin.stop()

        for plugin in self._started_plugins:
            await plugin.stop()
        self._started_plugins.clear()

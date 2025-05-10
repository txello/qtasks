import asyncio
from typing import TYPE_CHECKING, Optional
from typing_extensions import Annotated, Doc

from .base import BaseStarter

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.workers.base import BaseWorker
    from qtasks.plugins.base import BasePlugin


class AsyncStarter(BaseStarter):
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
            ] = None
        ):
        super().__init__(name=name, broker=broker, worker=worker)
        
        self._global_loop: asyncio.AbstractEventLoop | None = None

    def start(self,
            loop: Annotated[
                Optional[asyncio.AbstractEventLoop],
                Doc(
                    """
                    Асинхронный loop.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            num_workers: Annotated[
                int,
                Doc(
                    """
                    Количество запущенных воркеров.
                    
                    По умолчанию: `4`.
                    """
                )
            ] = 4,
            reset_config: Annotated[
                bool,
                Doc(
                    """
                    Обновить config у воркера и брокера.
                    
                    По умолчанию: `True`.
                    """
                )
            ] = True,
            plugins: Annotated[
                Optional[dict[str, "BasePlugin"]],
                Doc(
                    """
                    Плагины для воркера и брокера.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None
        ) -> None:
        """Запуск Стартера. Эта функция задействуется основным экземпляром `QueueTasks` через `run_forever`.

        Args:
            loop (asyncio.AbstractEventLoop, optional): Асинхронный loop. По умолчанию: None.
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
            reset_config (bool, optional): Обновить config у воркера и брокера. По умолчанию: True.
            plugins (dict[str, BasePlugin] | None, optional): Плагины. По умолчанию: None.
        """
        print("[QueueTasks] Запуск QueueTasks...")

        if plugins:
            self.plugins.update(plugins)
        
        if reset_config:
            self.worker.update_config(self.config)
            self.broker.update_config(self.config)

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
        for model_plugin in self.plugins.values():
            await model_plugin.start()
        
        for model in self._inits["init_starting"]:
            await model.func(worker=self.worker, broker=self.broker) if model.awaiting else model.func(worker=self.worker, broker=self.broker)

        broker_task = asyncio.create_task(self.broker.start(self.worker))
        worker_task = asyncio.create_task(self.worker.start(num_workers))

        try:
            await asyncio.gather(broker_task, worker_task)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def stop(self):
        """Останавливает все компоненты."""

        print("[QueueTasks] Остановка QueueTasks...")
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

        for model_init in self._inits["init_stoping"]:
            await model_init.func(worker=self.worker, broker=self.broker) if model_init.awaiting else model_init.func(worker=self.worker, broker=self.broker)

        for model_plugin in self.plugins.values():
            await model_plugin.stop()
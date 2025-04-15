from typing import TYPE_CHECKING, Optional
from typing_extensions import Annotated, Doc

from .base import BaseStarter

if TYPE_CHECKING:
    from qtasks.brokers.base import BaseBroker
    from qtasks.workers.base import BaseWorker
    from qtasks.plugins.base import BasePlugin


class SyncStarter(BaseStarter):
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
        
    def start(self,
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
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
            reset_config (bool, optional): Обновить config у воркера и брокера. По умолчанию: True.
            plugins (dict[str, BasePlugin] | None, optional): Плагины. По умолчанию: None.
        """
        print("[QueueTasks] Запуск QueueTasks...")
        
        self.plugins.update(plugins)
        
        if reset_config:
            self.worker.update_config(self.config)
            self.broker.update_config(self.config)
        
        try:
            self._start(num_workers=num_workers)
        except KeyboardInterrupt:
            self.stop()
        
    def _start(self, num_workers=4):
        """Запуск Стартера синхронно.

        Args:
            num_workers (int, optional): Количество воркеров. По умолчанию: 4.
        """
        for model in self._inits["init_starting"]:
            model.func(worker=self.worker, broker=self.broker)
        
        self.worker.start(num_workers)
        self.broker.start(self.worker)
        
        
        try:
            while True:
                pass  # Бесконечный цикл выполнения
        except KeyboardInterrupt:
            self.stop()
        
    def stop(self):
        """Останавливает все компоненты."""
        #print("[QueueTasks] Остановка QueueTasks...")
        
        self.broker.stop()
        self.worker.stop()
        self.broker.storage.stop()
        
        for model in self._inits["init_stoping"]:
                model.func(worker=self.worker, broker=self.broker)
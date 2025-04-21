from abc import ABC, abstractmethod
from typing_extensions import Annotated, Doc

from qtasks.configs.config import QueueConfig
from qtasks.qtasks import QueueTasks
from qtasks.schemas.test import TestConfig
from qtasks.tests.async_classes import AsyncTestBroker, AsyncTestGlobalConfig, AsyncTestStorage, AsyncTestWorker


class BaseTestCase(ABC):
    def __init__(self, app: QueueTasks, name: str|None = None):
        self.app = app
        
        self.name = name
        self.config = QueueConfig()
        self.test_config = TestConfig()
    
    @abstractmethod
    def start(self, **kwargs):
        pass
    
    @abstractmethod
    def stop(self, **kwargs):
        pass
    
    def update_config(self,
            config: Annotated[
                QueueConfig,
                Doc(
                    """
                    Конфиг.
                    """
                )
            ]
        ) -> None:
        """Обновляет конфиг брокера.

        Args:
            config (QueueConfig): Конфиг.
        """
        self.config = config
        return
    
    def settings(self, test_config: TestConfig = None):
        if test_config:
            self.test_config = test_config
        else:
            test_config = self.test_config
        
        global_config = None
        storage = None
        
        if not test_config.global_config:
            global_config = AsyncTestGlobalConfig(name=self.name)
        
        if not test_config.storage:
            storage = AsyncTestStorage(name=self.name, global_config=global_config)
        
        if not test_config.broker:
            self.app.broker = AsyncTestBroker(name=self.name, storage=storage)
        
        if not test_config.worker:
            self.app.worker = AsyncTestWorker(name=self.name, broker=self.app.broker)
        
        if not test_config.plugins:
            self.app.plugins.clear()
            self.app.broker.plugins.clear()
            self.app.broker.storage.plugins.clear()
            self.app.broker.storage.global_config.plugins.clear()
            self.app.worker.plugins.clear()
            if self.app.starter:
                self.app.starter.plugins.clear()
        
        return
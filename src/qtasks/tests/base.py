from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from typing_extensions import Annotated, Doc

from qtasks.configs.config import QueueConfig
from qtasks.schemas.test import TestConfig
from qtasks.tests.async_classes import AsyncTestBroker, AsyncTestGlobalConfig, AsyncTestStorage, AsyncTestWorker

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks


class BaseTestCase(ABC):
    """
    `BaseTestCase` - Абстрактный класс, который является фундаментом для TestCase.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.tests.base import BaseTestCase
    
    class MyTestCase(BaseTestCase):
        def __init__(self, app: QueueTasks, name: str|None = None):
            super().__init__(app=app, name=name)
            pass
    ```
    """
    
    def __init__(self,
            app: Annotated[
                "QueueTasks",
                Doc(
                    """
                    Основной экземпляр.
                    """
                )
            ],
            name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя проекта. Это имя может быть использовано для тестовых компонентов.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
        ):
        self.app = app
        
        self.name = name
        self.config = QueueConfig()
        self.test_config = TestConfig()
    
    @abstractmethod
    def start(self, **kwargs):
        """Запускает кейс тестирования."""
        pass
    
    @abstractmethod
    def stop(self, **kwargs):
        """Останавливает кейс тестирования."""
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
    
    def settings(self, test_config: TestConfig = None) -> None:
        """Настройки тестирования.

        Args:
            test_config (TestConfig, optional): Конфиг тестирования. По умолчанию: `TestConfig()`.
        """
        
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

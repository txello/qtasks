"""Base test case."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Generic, Literal, Optional, Union, overload
from typing_extensions import Annotated, Doc

from qtasks.configs.config import QueueConfig
from qtasks.schemas.test import TestConfig
from qtasks.tests.async_classes import (
    AsyncTestBroker,
    AsyncTestGlobalConfig,
    AsyncTestStorage,
    AsyncTestWorker,
)
from qtasks.tests.sync_classes import (
    SyncTestBroker,
    SyncTestGlobalConfig,
    SyncTestStorage,
    SyncTestWorker,
)
from qtasks.types.typing import TAsyncFlag

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks
    from qtasks.asyncio.qtasks import QueueTasks as aioQueueTasks


class BaseTestCase(Generic[TAsyncFlag], ABC):
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

    def __init__(
        self,
        app: Annotated[
            Union["QueueTasks", "aioQueueTasks"],
            Doc(
                """
                    Основной экземпляр.
                    """
            ),
        ],
        name: Annotated[
            Optional[str],
            Doc(
                """
                    Имя проекта. Это имя может быть использовано для тестовых компонентов.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ):
        """Инициализация тестового кейса."""
        self.app = app

        self.name = name
        self.config = QueueConfig()
        self.test_config = TestConfig()

    @overload
    def start(self: "BaseTestCase[Literal[False]]", **kwargs) -> None:
        """Запускает кейс тестирования."""
        pass

    @overload
    async def start(self: "BaseTestCase[Literal[True]]", **kwargs) -> None:
        """Запускает кейс тестирования."""
        pass

    @abstractmethod
    def start(self, **kwargs) -> Union[None, Awaitable[None]]:
        """Запускает кейс тестирования."""
        pass

    @overload
    def stop(self: "BaseTestCase[Literal[False]]", **kwargs) -> None:
        """Запускает кейс тестирования."""
        pass

    @overload
    async def stop(self: "BaseTestCase[Literal[True]]", **kwargs) -> None:
        """Запускает кейс тестирования."""
        pass

    @abstractmethod
    def stop(self, **kwargs) -> Union[None, Awaitable[None]]:
        """Останавливает кейс тестирования."""
        pass

    def update_config(
        self,
        config: Annotated[
            QueueConfig,
            Doc(
                """
                    Конфиг.
                    """
            ),
        ],
    ) -> None:
        """Обновляет конфиг брокера.

        Args:
            config (QueueConfig): Конфиг.
        """
        self.config = config
        return

    def settings(
        self, test_config: Optional[TestConfig] = None, awaiting: Optional[bool] = False
    ) -> None:
        """Настройки тестирования.

        Args:
            test_config (TestConfig, optional): Конфиг тестирования. По умолчанию: `TestConfig()`.
            awaiting (bool, optional): Использовать Async компоненты. По умолчанию: `False`.
        """
        if test_config:
            self.test_config = test_config
        else:
            test_config = self.test_config

        global_config = None
        storage = None

        if not test_config.global_config:
            global_config = (
                AsyncTestGlobalConfig(name=self.name)
                if awaiting
                else SyncTestGlobalConfig(name=self.name)
            )

        if not test_config.storage:
            storage = (
                AsyncTestStorage(name=self.name, global_config=global_config)
                if awaiting
                else SyncTestStorage(name=self.name, global_config=global_config)
            )

        if not test_config.broker:
            self.app.broker = (
                AsyncTestBroker(name=self.name, storage=storage)
                if awaiting
                else SyncTestBroker(name=self.name, storage=storage)
            )

        if not test_config.worker:
            self.app.worker = AsyncTestWorker(name=self.name, broker=self.app.broker) if awaiting else SyncTestWorker(name=self.name, broker=self.app.broker)  # type: ignore

        if not test_config.plugins:
            self.app.plugins.clear()
            self.app.broker.plugins.clear()
            self.app.broker.storage.plugins.clear()
            if self.app.broker.storage.global_config:
                self.app.broker.storage.global_config.plugins.clear()
            self.app.worker.plugins.clear()
            if self.app.starter:
                self.app.starter.plugins.clear()

        return

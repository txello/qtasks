"""Async test classes."""

from typing import Literal, Optional
from qtasks.brokers.base import BaseBroker
from qtasks.configs.base import BaseGlobalConfig
from qtasks.storages.base import BaseStorage
from qtasks.workers.base import BaseWorker


class AsyncTestGlobalConfig(BaseGlobalConfig):
    def __init__(self, name=None):
        super().__init__(name=name)

    async def set(self, **kwargs):
        pass

    async def get(self, name):
        pass

    async def get_all(self):
        pass

    async def get_match(self, match):
        pass

    async def start(self):
        pass

    async def stop(self):
        pass


class AsyncTestStorage(BaseStorage):
    def __init__(
        self,
        name: Optional[str] = None,
        global_config: Optional["BaseGlobalConfig[Literal[True]]"] = None,
    ):
        global_config = global_config or AsyncTestGlobalConfig()
        super().__init__(name=name or "QueueTasks", global_config=global_config)

    async def add(self, uuid, task_status):
        pass

    async def get(self, uuid):
        pass

    async def get_all(self):
        pass

    async def update(self, **kwargs):
        pass

    async def start(self):
        pass

    async def stop(self):
        pass

    async def add_process(self):
        pass


class AsyncTestBroker(BaseBroker):
    def __init__(
        self,
        name: Optional[str] = None,
        storage: Optional["BaseStorage[Literal[True]]"] = None,
    ):
        storage = storage = AsyncTestStorage(name=name)
        super().__init__(name=name, storage=storage)
        pass

    async def add(self, task_name, priority=0, *args, **kwargs):
        pass

    async def start(self, worker=None):
        pass

    async def stop(self):
        pass

    async def get(self, uuid):
        pass

    async def update(self, **kwargs):
        pass


class AsyncTestWorker(BaseWorker):
    def __init__(self, name=None, broker: Optional["BaseBroker[Literal[True]]"] = None):
        super().__init__(name=name or "QueueTasks", broker=broker)

    async def add(self, task_name, priority=0, *args, **kwargs):
        pass

    async def start(self, worker=None):
        pass

    async def stop(self):
        pass

    async def get(self, uuid):
        pass

    async def update(self, **kwargs):
        pass

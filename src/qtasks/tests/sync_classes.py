"""Sync test classes."""

from typing import Literal, Optional

from qtasks.brokers.base import BaseBroker
from qtasks.configs.base import BaseGlobalConfig
from qtasks.storages.base import BaseStorage
from qtasks.workers.base import BaseWorker


class SyncTestGlobalConfig(BaseGlobalConfig):
    def __init__(self, name=None):
        super().__init__(name=name)

    def set(self, **kwargs):
        pass

    def get(self, name):
        pass

    def get_all(self):
        pass

    def get_match(self, match):
        pass

    def start(self):
        pass

    def stop(self):
        pass


class SyncTestStorage(BaseStorage):
    def __init__(
        self,
        name: str | None = None,
        global_config: Optional["BaseGlobalConfig[Literal[True]]"] = None,
    ):
        global_config = global_config or SyncTestGlobalConfig()
        super().__init__(name=name or "QueueTasks", global_config=global_config)

    def add(self, uuid, task_status):
        pass

    def get(self, uuid):
        pass

    def get_all(self):
        pass

    def update(self, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def add_process(self):
        pass


class SyncTestBroker(BaseBroker):
    def __init__(
        self,
        name: str | None = None,
        storage: Optional["BaseStorage[Literal[True]]"] = None,
    ):
        storage = storage = SyncTestStorage(name=name)
        super().__init__(name=name, storage=storage)
        pass

    def add(self, task_name, priority=0, *args, **kwargs):
        pass

    def start(self, worker=None):
        pass

    def stop(self):
        pass

    def get(self, uuid):
        pass

    def update(self, **kwargs):
        pass


class SyncTestWorker(BaseWorker):
    def __init__(self, name=None, broker: Optional["BaseBroker[Literal[True]]"] = None):
        super().__init__(name=name or "QueueTasks", broker=broker)

    def add(self, task_name, priority=0, *args, **kwargs):
        pass

    def start(self, worker=None):
        pass

    def stop(self):
        pass

    def get(self, uuid):
        pass

    def update(self, **kwargs):
        pass

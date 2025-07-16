"""test classes."""

from qtasks.brokers.base import BaseBroker
from qtasks.configs.base import BaseGlobalConfig
from qtasks.storages.base import BaseStorage
from qtasks.workers.base import BaseWorker


class SyncTestBroker(BaseBroker):
    def __init__(self, name=None, storage=None):
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
    def __init__(self, name=None, broker=None):
        super().__init__(name=name, broker=broker)

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


class SyncTestStorage(BaseStorage):
    def __init__(self, name=None, global_config=None):
        super().__init__(name=name, global_config=global_config)

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

import importlib
from typing import TYPE_CHECKING

_brokers = {
    "SyncRedisBroker": "qtasks.brokers.sync_redis",
    "AsyncRedisBroker": "qtasks.brokers.async_redis",
    "SyncRabbitMQBroker": "qtasks.brokers.sync_rabbitmq",
    "AsyncRabbitMQBroker": "qtasks.brokers.async_rabbitmq",
    "SyncKafkaBroker": "qtasks.brokers.sync_kafka",
    "AsyncKafkaBroker": "qtasks.brokers.async_kafka",
}


def __getattr__(name: str):
    if name in _brokers:
        module_path = _brokers[name]
        module = importlib.import_module(module_path)
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


if TYPE_CHECKING:
    from .sync_redis import SyncRedisBroker
    from .async_redis import AsyncRedisBroker
    from .sync_rabbitmq import SyncRabbitMQBroker
    from .async_rabbitmq import AsyncRabbitMQBroker
    from .sync_kafka import SyncKafkaBroker
    from .async_kafka import AsyncKafkaBroker

"""Init Brokers."""

import importlib
from typing import TYPE_CHECKING

_brokers = {
    "SyncRedisBroker": "qtasks.brokers.sync_redis",
    "AsyncRedisBroker": "qtasks.brokers.async_redis",
    "SyncRabbitMQBroker": "qtasks.brokers.sync_rabbitmq",
    "AsyncRabbitMQBroker": "qtasks.brokers.async_rabbitmq",
    "SyncKafkaBroker": "qtasks.brokers.sync_kafka",
    "AsyncKafkaBroker": "qtasks.brokers.async_kafka",
    "AsyncSocketBroker": "qtasks.brokers.async_socket",
    "SyncSocketBroker": "qtasks.brokers.sync_socket",
}


def __getattr__(name: str):
    if name in _brokers:
        module_path = _brokers[name]
        module = importlib.import_module(module_path)
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


if TYPE_CHECKING:
    from .async_kafka import AsyncKafkaBroker
    from .async_rabbitmq import AsyncRabbitMQBroker
    from .async_redis import AsyncRedisBroker
    from .async_socket import AsyncSocketBroker
    from .sync_kafka import SyncKafkaBroker
    from .sync_rabbitmq import SyncRabbitMQBroker
    from .sync_redis import SyncRedisBroker
    from .sync_socket import SyncSocketBroker

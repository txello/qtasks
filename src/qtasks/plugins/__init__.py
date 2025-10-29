"""Init plugins."""

import importlib
from typing import TYPE_CHECKING

from .depends import AsyncDependsPlugin, Depends, SyncDependsPlugin
from .pydantic import AsyncPydanticWrapperPlugin, SyncPydanticWrapperPlugin
from .retries import AsyncRetryPlugin, SyncRetryPlugin
from .states import AsyncState, AsyncStatePlugin, SyncState, SyncStatePlugin
from .testing import AsyncTestPlugin, SyncTestPlugin

_plugins = {
    "SyncgRPCPlugin": "qtasks.plugins.grpc.sync_grpc",
    "AsyncgRPCPlugin": "qtasks.plugins.grpc.async_grpc"
}

def __getattr__(name: str):
    if name in _plugins:
        module_path = _plugins[name]
        module = importlib.import_module(module_path)
        return getattr(module, name)

if TYPE_CHECKING:
    from .grpc.async_grpc import AsyncgRPCPlugin
    from .grpc.sync_grpc import SyncgRPCPlugin

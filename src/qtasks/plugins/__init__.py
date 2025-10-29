"""Init plugins."""

import importlib
from typing import TYPE_CHECKING
from .retries import SyncRetryPlugin, AsyncRetryPlugin
from .pydantic import SyncPydanticWrapperPlugin, AsyncPydanticWrapperPlugin
from .testing import SyncTestPlugin, AsyncTestPlugin
from .depends import SyncDependsPlugin, AsyncDependsPlugin, Depends
from .states import SyncStatePlugin, AsyncStatePlugin, SyncState, AsyncState

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
    from .grpc.sync_grpc import SyncgRPCPlugin
    from .grpc.async_grpc import AsyncgRPCPlugin

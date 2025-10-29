"""Init gRPC services."""
from .sync_services import QTasksServiceServicer
from .sync_server import SyncQTasksGRPCServer

from .async_services import QTasksServiceServicer
from .async_server import AsyncQTasksGRPCServer

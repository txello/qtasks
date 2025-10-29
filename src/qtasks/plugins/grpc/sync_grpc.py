"""Sync gRPC plugin."""
from typing import Any, List, Optional, TYPE_CHECKING

from qtasks.plugins.base import BasePlugin
from qtasks.plugins.grpc.services.sync_server import SyncQTasksGRPCServer

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks


class SyncgRPCPlugin(BasePlugin):
    """Sync gRPC plugin."""

    def __init__(
        self,
        app: "QueueTasks",
        host: str = "0.0.0.0",
        port: int = 50051,
        *,
        max_concurrent_rpcs: Optional[int] = None,
        grpc_options: Optional[List[tuple[str, Any]]] = None,
    ) -> None:
        """Инициализация плагина gRPC.

        Args:
            app (QueueTasks): Приложение `QueueTasks`.
            host (str, optional): Хост gRPC-сервера. По умолчанию: `0.0.0.0`.
            port (int, optional): Порт gRPC-сервера. По умолчанию: `50051`.
            max_concurrent_rpcs (Optional[int], optional): Максимальное количество одновременно обрабатываемых RPC. По умолчанию: `None`.
            grpc_options (Optional[List[tuple[str, Any]]], optional): Дополнительные параметры gRPC. По умолчанию: `None`.
        """
        super().__init__()
        self.app = app
        self._server = SyncQTasksGRPCServer(
            app=app,
            host=host,
            port=port,
            max_concurrent_rpcs=max_concurrent_rpcs,
            grpc_options=grpc_options,
        )

    def start(self) -> None:
        """Запуск плагина gRPC."""
        self._server.start()

    def stop(self) -> None:
        """Остановка плагина gRPC."""
        self._server.stop()

    def trigger(self, *args, **kwargs) -> None:
        """Триггер плагина gRPC."""
        pass

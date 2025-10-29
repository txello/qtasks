"""Async gRPC plugin."""
from typing import TYPE_CHECKING, Any

from qtasks.plugins.base import BasePlugin
from qtasks.plugins.grpc.services.async_server import AsyncQTasksGRPCServer

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks


class AsyncgRPCPlugin(BasePlugin):
    """Async gRPC plugin."""

    def __init__(
        self,
        app: "QueueTasks",
        host: str = "0.0.0.0",
        port: int = 50051,
        *,
        max_concurrent_rpcs: int | None = None,
        grpc_options: list[tuple[str, Any]] | None = None,
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
        self._server = AsyncQTasksGRPCServer(
            app=app,
            host=host,
            port=port,
            max_concurrent_rpcs=max_concurrent_rpcs,
            grpc_options=grpc_options,
        )

    async def start(self) -> None:
        """Запуск плагина gRPC."""
        await self._server.start()

    async def stop(self) -> None:
        """Остановка плагина gRPC."""
        await self._server.stop()

    async def trigger(self, *args, **kwargs) -> None:
        """Триггер плагина gRPC."""
        pass

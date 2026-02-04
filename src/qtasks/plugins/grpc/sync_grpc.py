"""Sync gRPC plugin."""
from typing import TYPE_CHECKING, Any

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
        max_concurrent_rpcs: int | None = None,
        grpc_options: list[tuple[str, Any]] | None = None,
    ) -> None:
        """
        Initializing the gRPC plugin.
        
                Args:
                    app(QueueTasks): Application `QueueTasks`.
                    host (str, optional): Host of the gRPC server. Default: `0.0.0.0`.
                    port (int, optional): Port of the gRPC server. Default: `50051`.
                    max_concurrent_rpcs (Optional[int], optional): Maximum number of concurrent RPCs processed. Default: `None`.
                    grpc_options (Optional[List[tuple[str, Any]]], optional: Additional gRPC options. Default: `None`.
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
        """Launching the gRPC plugin."""
        self._server.start()

    def stop(self) -> None:
        """Stopping the gRPC plugin."""
        self._server.stop()

    def trigger(self, *args, **kwargs) -> None:
        """gRPC plugin trigger."""
        pass

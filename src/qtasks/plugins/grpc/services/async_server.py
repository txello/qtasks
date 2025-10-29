"""Async gRPC server."""
import asyncio
import contextlib
from typing import Any, List, Optional, TYPE_CHECKING

import grpc
from grpc_reflection.v1alpha import reflection
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from qtasks.plugins.grpc.core import qtasks_pb2, qtasks_pb2_grpc
from .async_services import QTasksServiceServicer

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks


class AsyncQTasksGRPCServer:
    """AsyncQTasksGRPCServer."""
    def __init__(
        self,
        app: "QueueTasks",
        host: str = "0.0.0.0",
        port: int = 50051,
        *,
        max_concurrent_rpcs: Optional[int] = None,
        grpc_options: Optional[List[tuple[str, Any]]] = None,
    ) -> None:
        self._app = app
        self._host = host
        self._port = int(port)
        self._addr = f"{host}:{port}"
        self._task: Optional[asyncio.Task] = None
        self._max_concurrent_rpcs = max_concurrent_rpcs
        self._grpc_options = grpc_options


    async def _create_server(self) -> None:
        self._server = grpc.aio.server(
            options=self._grpc_options or [
                ("grpc.max_send_message_length", 40 * 1024 * 1024),
                ("grpc.max_receive_message_length", 40 * 1024 * 1024),
            ],
            maximum_concurrent_rpcs=self._max_concurrent_rpcs,
        )

        # Сервис QTasks
        qtasks_pb2_grpc.add_QTasksServiceServicer_to_server(
            QTasksServiceServicer(self._app), self._server
        )

        # Health
        self._health = health.HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(self._health, self._server)

        # Reflection
        service_names = (
            qtasks_pb2.DESCRIPTOR.services_by_name["QTasksService"].full_name,
            health.SERVICE_NAME,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(service_names, self._server)

        self._server.add_insecure_port(self._addr)

    async def _serve(self) -> None:
        await self._create_server()
        await self._server.start()
        print("Сервер gRPC запущен")
        self._health.set("", health_pb2.HealthCheckResponse.SERVING)
        try:
            await self._server.wait_for_termination()
        finally:
            pass

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._serve(), name="qtasks-grpc-server")

    async def stop(self, grace: float = 3.0) -> None:
        if self._task and not self._task.done():
            self._health.set("", health_pb2.HealthCheckResponse.NOT_SERVING)
            await self._server.stop(grace)
            await self._server.wait_for_termination()
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

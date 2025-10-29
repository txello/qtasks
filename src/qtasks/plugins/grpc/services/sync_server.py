"""Async gRPC server."""
import asyncio
from concurrent import futures
from threading import Thread
from typing import TYPE_CHECKING, Any

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from qtasks.plugins.grpc.core import qtasks_pb2, qtasks_pb2_grpc

from .sync_services import SyncQTasksServiceServicer

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks


class SyncQTasksGRPCServer:
    """SyncQTasksGRPCServer."""
    def __init__(
        self,
        app: "QueueTasks",
        host: str = "0.0.0.0",
        port: int = 50051,
        *,
        max_concurrent_rpcs: int | None = None,
        grpc_options: list[tuple[str, Any]] | None = None,
    ) -> None:
        self._app = app
        self._host = host
        self._port = int(port)
        self._addr = f"{host}:{port}"
        self._task: asyncio.Task | None = None
        self._max_concurrent_rpcs = max_concurrent_rpcs
        self._grpc_options = grpc_options


    def _create_server(self) -> None:
        self._server = grpc.server(
            thread_pool=futures.ThreadPoolExecutor(max_workers=10),
            options=self._grpc_options or [
                ("grpc.max_send_message_length", 40 * 1024 * 1024),
                ("grpc.max_receive_message_length", 40 * 1024 * 1024),
            ],
            maximum_concurrent_rpcs=self._max_concurrent_rpcs,
        )

        # Сервис QTasks
        qtasks_pb2_grpc.add_QTasksServiceServicer_to_server(
            SyncQTasksServiceServicer(self._app), self._server
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

    def _serve(self) -> None:
        self._create_server()
        Thread(target=self._server.start, daemon=True).start()
        self._health.set("", health_pb2.HealthCheckResponse.SERVING)
        try:
            self._server.wait_for_termination()
        finally:
            pass

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = Thread(target=self._serve, daemon=True).start()

    def stop(self, grace: float = 3.0) -> None:
        if self._task and not self._task.done():
            self._health.set("", health_pb2.HealthCheckResponse.NOT_SERVING)
            self._server.stop(grace)
            self._server.wait_for_termination()
            self._task.cancel()

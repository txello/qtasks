"""Async gRPC server."""
import asyncio
import json
from typing import Any, Optional, TYPE_CHECKING

import grpc
from qtasks.plugins.grpc.core import qtasks_pb2, qtasks_pb2_grpc

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks


def _loads_or(default: Any, raw: str | bytes | None) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def _dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception as exc:
        # В крайних случаях приводим к строке
        return json.dumps({"__non_json__": str(obj)}, ensure_ascii=False)


class QTasksServiceServicer(qtasks_pb2_grpc.QTasksServiceServicer):
    def __init__(self, app: "QueueTasks"):
        self.app = app

    async def AddTask(
        self,
        request: qtasks_pb2.AddTaskRequest,
        context: grpc.aio.ServicerContext,
    ) -> qtasks_pb2.AddTaskResponse:
        task_uuid = None
        result: Optional[Any] = None

        args = _loads_or([], request.args_json)
        kwargs = _loads_or({}, request.kwargs_json)
        priority = int(request.priority) if request.priority else None
        timeout = float(request.timeout) if request.timeout else None

        try:
            maybe = self.app.add_task(
                request.name,
                *args,
                priority=priority,
                timeout=timeout,
                **kwargs,
            )
            task = await maybe if asyncio.iscoroutine(maybe) else maybe
            if task:
                result = task.returning
                task_uuid = str(task.uuid)

            return qtasks_pb2.AddTaskResponse(
                ok=True,
                uuid=task_uuid or "",
                result_json=_dumps(result) if result is not None else "",
            )
        except Exception as exc:
            return qtasks_pb2.AddTaskResponse(ok=False, error=str(exc))

    async def GetTask(
        self,
        request: qtasks_pb2.GetTaskRequest,
        context: grpc.aio.ServicerContext,
    ) -> qtasks_pb2.GetTaskResponse:
        try:
            task = await self.app.get(request.uuid)
            if not task:
                return qtasks_pb2.GetTaskResponse(ok=False, error="Задача не найдена!")

            status = task.status or ""
            result = None
            traceback_text = ""

            if request.include_result:
                result = task.returning
                traceback_text = task.traceback

            return qtasks_pb2.GetTaskResponse(
                ok=True,
                status=str(status),
                result_json=_dumps(result) if result is not None else "",
                traceback=traceback_text,
            )
        except Exception as exc:
            return qtasks_pb2.GetTaskResponse(ok=False, error=str(exc))

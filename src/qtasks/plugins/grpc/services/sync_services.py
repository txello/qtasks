"""Async gRPC server."""
import json
from typing import TYPE_CHECKING, Any

import grpc

from qtasks.plugins.grpc.core import qtasks_pb2, qtasks_pb2_grpc

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks


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
    except Exception:
        # В крайних случаях приводим к строке
        return json.dumps({"__non_json__": str(obj)}, ensure_ascii=False)


class SyncQTasksServiceServicer(qtasks_pb2_grpc.QTasksServiceServicer):
    def __init__(self, app: "QueueTasks"):
        self.app = app

    def AddTask(
        self,
        request: qtasks_pb2.AddTaskRequest,
        context: grpc.aio.ServicerContext,
    ) -> qtasks_pb2.AddTaskResponse:
        task_uuid = None
        result: Any | None = None

        args = _loads_or([], request.args_json)
        kwargs = _loads_or({}, request.kwargs_json)
        priority = int(request.priority) if request.priority else None
        timeout = float(request.timeout) if request.timeout else None

        try:
            # Вариант 1: позиционные аргументы
            task = self.app.add_task(
                request.name,
                *args,
                priority=priority,
                timeout=timeout,
                **kwargs,
            )
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

    def GetTask(
        self,
        request: qtasks_pb2.GetTaskRequest,
        context: grpc.aio.ServicerContext,
    ) -> qtasks_pb2.GetTaskResponse:
        try:
            task = self.app.get(request.uuid)
            if not task:
                return qtasks_pb2.GetTaskResponse(ok=False, error="Task not found!")

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

"""Async Retry Plugin."""

from dataclasses import field, make_dataclass
import time
from qtasks.brokers.base import BaseBroker
from qtasks.plugins.base import BasePlugin
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusErrorSchema


class AsyncRetryPlugin(BasePlugin):
    """Плагин для асинхронной обработки повторных попыток."""

    def __init__(self,
                 name: str = "AsyncRetryPlugin"
                 ):
        """Инициализация плагина.

        Args:
            name (str, optional): Имя проекта. По умолчанию: "AsyncRetryPlugin".
        """
        super().__init__(name=name)
        self.handlers = {"retry": self._execute}

    async def start(self, *args, **kwargs):
        """Запуск плагина."""
        pass

    async def stop(self, *args, **kwargs):
        """Остановка плагина."""
        pass

    async def trigger(self, name, **kwargs):
        """Триггер для запуска обработчика."""
        handler = self.handlers.get(name)
        return await handler(**kwargs) if handler else None

    async def _execute(
        self,
        broker: BaseBroker,
        task_func: TaskExecSchema,
        task_broker: TaskPrioritySchema,
        trace: str,
    ) -> TaskStatusErrorSchema:
        task = await broker.get(uuid=task_broker.uuid)
        task_retry = int(task.retry) if hasattr(task, "retry") else task_func.retry
        new_task = None

        if task_retry > 0:
            new_task = await broker.add(
                task_name=task_broker.name,
                priority=task_broker.priority,
                extra={"retry": task_retry - 1, "retry_parent_uuid": task_broker.uuid},
                args=task_broker.args,
                kwargs=task_broker.kwargs,
            )

        model = TaskStatusErrorSchema(
            task_name=task_func.name,
            priority=task_func.priority,
            traceback=trace,
            created_at=task_broker.created_at,
            updated_at=time.time(),
        )
        fields = [
            ("retry", int | None, field(default="None")),
        ]
        if new_task is not None:
            fields.append(("retry_child_uuid", str | None, field(default="None")))

        model.__class__ = make_dataclass(
            "TaskStatusErrorSchema", fields=fields, bases=(TaskStatusErrorSchema,)
        )
        model.retry = task_retry
        if new_task is not None:
            model.retry_child_uuid = new_task.uuid if task_retry > 0 else "None"
        return model

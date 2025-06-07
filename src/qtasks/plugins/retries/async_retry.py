from dataclasses import field, make_dataclass
import time
from qtasks.brokers.base import BaseBroker
from qtasks.plugins.base import BasePlugin
from qtasks.schemas.task_exec import TaskExecSchema, TaskPrioritySchema
from qtasks.schemas.task_status import TaskStatusErrorSchema

class AsyncRetryPlugin(BasePlugin):
    def __init__(self, name = "AsyncRetryPlugin"):
        super().__init__(name)
    
    async def start(self, *args, **kwargs):
        pass

    async def stop(self, *args, **kwargs):
        pass


    async def trigger(self, name, *args, **kwargs):
        if name == "retry":
            return await self._execute(
                broker=kwargs.get("broker", None),
                task_func=kwargs.get("task_func", None),
                task_broker=kwargs.get("task_broker", None),
                trace=kwargs.get("trace", None),
            )
        return None


    async def _execute(self, broker: BaseBroker, task_func: TaskExecSchema, task_broker: TaskPrioritySchema, trace: str) -> TaskStatusErrorSchema:
        task = await broker.get(uuid=task_broker.uuid)
        task_retry = int(task.retry) if hasattr(task, "retry") else task_func.retry
        print(123, task_retry)

        if task_retry > 0:
            await broker.add(task_name=task_broker.name, priority=task_broker.priority,
                extra={
                    "retry": task_retry - 1,
                    "retry_uuid": task_broker.uuid
                }, 
                *task_broker.args, **task_broker.kwargs
            )
        
        model = TaskStatusErrorSchema(task_name=task_func.name, priority=task_func.priority, traceback=trace, created_at=task_broker.created_at, updated_at=time.time())
        model.__class__ = make_dataclass('TaskStatusErrorSchema', fields=[('retry', int|None, field(default=None))], bases=(TaskStatusErrorSchema,))
        model.retry = task_retry
        return model

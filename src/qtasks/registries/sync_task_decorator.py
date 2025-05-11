from typing import TYPE_CHECKING, Annotated, Optional
from typing_extensions import Doc

from qtasks.schemas.task import Task


if TYPE_CHECKING:
    from qtasks import QueueTasks

class SyncTask:
    def __init__(self, app: "QueueTasks", task_name: str):
        self.task_name = task_name
        self._app = app
        
    def add_task(self,
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    
                    По умолчанию: `0`.
                    """
                )
            ] = 0,
            args: Annotated[
                Optional[tuple],
                Doc(
                    """
                    args задачи.
                    
                    По умолчанию: `()`.
                    """
                )
            ] = None,
            kwargs: Annotated[
                Optional[dict],
                Doc(
                    """
                    kwargs задачи.
                    
                    По умолчанию: `{}`.
                    """
                )
            ] = None
        ) -> Task:
        return self._app.add_task(task_name=self.task_name, priority=priority, args=args, kwargs=kwargs)
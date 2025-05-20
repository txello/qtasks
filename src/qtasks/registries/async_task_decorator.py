from typing import TYPE_CHECKING, Annotated, Optional
from typing_extensions import Doc

from qtasks.schemas.task import Task


if TYPE_CHECKING:
    from qtasks.asyncio import QueueTasks

class AsyncTask:
    def __init__(self, app: "QueueTasks", task_name: str, priority: int):
        self.task_name = task_name
        self.priority = priority
        self.__app = app
        
    async def add_task(self,
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    
                    По умолчанию: Значение приоритета у задачи.
                    """
                )
            ] = None,
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
            ] = None,

            timeout: Annotated[
                Optional[float],
                Doc(
                    """
                    Таймаут задачи.
                    
                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
                )
            ] = None
        ) -> Task:
        if priority is None:
            priority = self.priority
        
        return await self.__app.add_task(task_name=self.task_name, priority=priority, args=args, kwargs=kwargs, timeout=timeout)
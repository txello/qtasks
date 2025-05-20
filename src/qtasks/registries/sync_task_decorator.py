from typing import TYPE_CHECKING, Annotated, Optional
from typing_extensions import Doc

from qtasks.schemas.task import Task


if TYPE_CHECKING:
    from qtasks import QueueTasks

class SyncTask:
    def __init__(self, task_name: str, priority: int, app: "QueueTasks" = None):
        self.task_name = task_name
        self.priority = priority
        self._app = app
        
    def add_task(self,
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
                    
                    Если указан, задача возвращается через `qtasks.results.SyncTask`.
                    """
                )
            ] = None
        ) -> Task:
        if not self._app:
            self._update_app()
        
        if priority is None:
            priority = self.priority
        
        return self._app.add_task(task_name=self.task_name, priority=priority, args=args, kwargs=kwargs, timeout=timeout)
    
    def _update_app(self) -> "QueueTasks":
        if not self._app:
            import qtasks._state
            if qtasks._state.app_main is None:
                raise ImportError("Невозможно получить app!")
            self._app = qtasks._state.app_main
        return
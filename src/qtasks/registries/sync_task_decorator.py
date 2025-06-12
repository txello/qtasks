from typing import TYPE_CHECKING, Annotated, Callable, Generic, List, Optional, Type
from typing_extensions import Doc

from qtasks.types.annotations import P, R
from qtasks.contexts.sync_context import SyncContext
from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware
from qtasks.schemas.task import Task


if TYPE_CHECKING:
    from qtasks import QueueTasks

class SyncTask(Generic[P, R]):
    """`SyncTask` - класс для замены функции декоратором `@app.task` и `@shared_task`.

    ## Пример

    ```python
    from qtasks import QueueTasks
    
    app = QueueTasks()

    @app.task("test")
    def test():
        print("Это тест!")

    test.add_task()
    ```
    """

    def __init__(self,
            task_name: Annotated[
                str,
                Doc(
                    """
                    Имя задачи.
                    """
                )
            ],
            priority: Annotated[
                int,
                Doc(
                    """
                    Приоритет задачи.
                    """
                )
            ],
            app: Annotated[
                "QueueTasks",
                Doc(
                    """
                    `QueueTasks` экземпляр.

                    По умолчанию: `qtasks._state.app_main`.
                    """
                )
            ] = None,

            echo: bool = False,
            retry: int|None = None,
            retry_on_exc: list[Type[Exception]]|None = None,
            generate_handler: Callable|None = None,


            executor: Annotated[
                Type["BaseTaskExecutor"],
                Doc(
                    """
                    Класс `BaseTaskExecutor`.
                    
                    По умолчанию: `SyncTaskExecutor`.
                    """
                )
            ] = None,
            middlewares: Annotated[
                List[TaskMiddleware],
                Doc(
                    """
                    Мидлвари.

                    По умолчанию: `Пустой массив`.
                    """
                )
            ] = None
        ):
        self.task_name = task_name
        self.priority = priority
        
        self.echo = echo
        self.retry = retry
        self.retry_on_exc = retry_on_exc

        self.executor = executor
        self.middlewares = middlewares
        self._app = app

        self.ctx = SyncContext(generate_handler=generate_handler,
            executor=executor, middlewares=middlewares,
            app=app
        )
        
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
            ] = None,

            task_name: Annotated[
                str,
                Doc(
                    """
                    Имя задачи.
                    """
                )
            ] = None
        ) -> Task|None:
        """Добавить задачу.

        Args:
            priority (int, optional): Приоритет задачи. По умолчанию: Значение приоритета у задачи.
            args (tuple, optional): args задачи. По умолчанию: `()`.
            kwargs (dict, optional): kwargs задачи. По умолчанию: `{}`.
            timeout (float, optional): Таймаут задачи. Если указан, задача возвращается через `qtasks.results.SyncTask`.
            task_name (str, optional): Имя задачи. По умолчанию: Значение имени у задачи.

        Returns:
            Task|None: Результат задачи или `None`.
        """
        if not self._app:
            self._update_app()
        
        if priority is None:
            priority = self.priority
        
        return self._app.add_task(task_name=task_name or self.task_name, priority=priority, args=args, kwargs=kwargs, timeout=timeout)

    def _update_app(self) -> "QueueTasks":
        if not self._app:
            import qtasks._state
            if qtasks._state.app_main is None:
                raise ImportError("Невозможно получить app!")
            self._app = qtasks._state.app_main
        return
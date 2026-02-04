"""Sync Task."""
from __future__ import annotations

from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Optional,
    Union,
)

from typing_extensions import Doc

from qtasks.contexts.sync_context import SyncContext
from qtasks.schemas.task_cls import SyncTaskCls
from qtasks.types.annotations import P, R

if TYPE_CHECKING:
    from qtasks import QueueTasks
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.middlewares.task import TaskMiddleware
    from qtasks.schemas.task import Task


class SyncTask(Generic[P, R]):
    """
    `SyncTask` - a class for replacing a function with a `@app.task` and `@shared_task` decorator.

    ## Example

    ```python
    from qtasks import QueueTasks

    app = QueueTasks()

    @app.task("test")
    def test():
        print("This is a test!")

    test.add_task()
    ```
    """

    def __init__(
        self,
        task_name: Annotated[
            str | None,
            Doc("""
                    Task name.

                    Default: `func.__name__`.
                    """),
        ] = None,
        priority: Annotated[
            int | None,
            Doc("""
                    The task has priority by default.

                    Default: `config.task_default_priority`.
                    """),
        ] = None,
        echo: Annotated[
            bool,
            Doc("""
                    Add SyncTask as the first parameter.

                    Default: `False`.
                    """),
        ] = False,
        max_time: Annotated[
            float | None,
            Doc("""
                    The maximum time it takes to complete a task in seconds.

                    Default: `None`.
                """),
        ] = None,
        retry: Annotated[
            int | None,
            Doc("""
                    The number of attempts to retry the task.

                    Default: `None`.
                    """),
        ] = None,
        retry_on_exc: Annotated[
            list[type[Exception]] | None,
            Doc("""
                    Exceptions under which the task will be re-executed.

                    Default: `None`.
                    """),
        ] = None,
        decode: Annotated[
            Callable | None,
            Doc("""
                    Task result decoder.
                """),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc("""
                    Task tags.

                    Default: `None`.
                """),
        ] = None,
        description: Annotated[
            str | None,
            Doc("""
                    Description of the task.

                    Default: `None`.
                """),
        ] = None,
        generate_handler: Annotated[
            Callable | None,
            Doc("""
                    Handler generator.

                    Default: `None`.
                    """),
        ] = None,
        executor: Annotated[
            type[BaseTaskExecutor] | None,
            Doc("""
                    Class `BaseTaskExecutor`.

                    Default: `SyncTaskExecutor`.
                    """),
        ] = None,
        middlewares_before: Annotated[
            list[type[TaskMiddleware]] | None,
            Doc("""
                    Middleware that will be executed before the task.

                    Default: `Empty array`.
                    """),
        ] = None,
        middlewares_after: Annotated[
            list[type[TaskMiddleware]] | None,
            Doc("""
                    Middleware that will be executed after the task.

                    Default: `Empty array`.
                    """),
        ] = None,
        extra: Annotated[
            dict[str, Any] | None,
            Doc("""
                    Additional options.

                    Default: `Empty dictionary`.
                    """),
        ] = None,
        app: Annotated[
            Optional[QueueTasks],
            Doc("""
                    `QueueTasks` instance.

                    Default: `qtasks._state.app_main`.
                    """),
        ] = None,
    ):
        """
        Initializing a synchronous task.

        Args:
            task_name (str, optional): Task name. Default: `None`.
            priority (int, optional): Task priority. Default: `None`.
            echo (bool, optional): Add SyncTask as the first parameter. Default: `False`.
            max_time (float, optional): The maximum time the task will take to complete in seconds. Default: `None`.
            retry (int, optional): Number of attempts to retry the task. Default: `None`.
            retry_on_exc (List[Type[Exception]], optional): Exceptions under which the task will be re-executed. Default: `None`.
            decode (Callable, optional): Decoder of the task result. Default: `None`.
            tags (List[str], optional): Task tags. Default: `None`.
            description (str, optional): Description of the task. Default: `None`.
            generate_handler (Callable, optional): Handler generator. Default: `None`.
            executor (Type["BaseTaskExecutor"], optional): Class `BaseTaskExecutor`. Default: `None`.
            middlewares_before (List[Type["TaskMiddleware"]], optional): Middleware that will be executed before the task. Default: `Empty array`.
            middlewares_after (List[Type["TaskMiddleware"]], optional): Middleware that will be executed after the task. Default: `Empty array`.
            extra (Dict[str, Any], optional): Additional parameters. Default: `Empty dictionary`.
            app (QueueTasks, optional): `QueueTasks` instance. Default: `None`.
        """
        self.task_name = task_name
        self.priority = priority

        self.echo = echo

        self.max_time = max_time

        self.retry = retry
        self.retry_on_exc = retry_on_exc

        self.decode = decode
        self.tags = tags
        self.description = description

        self.executor = executor
        self.middlewares_before = middlewares_before or []
        self.middlewares_after = middlewares_after or []

        self.extra = extra or {}

        self._app = app

        self.ctx = SyncContext(
            task_name=task_name,
            generate_handler=generate_handler,
            executor=executor,
            app=app,
        )

    def add_task(
        self,
        *args: Annotated[
            Any,
            Doc("""
                    args of the task.

                    Default: `()`.
                    """),
        ],
        priority: Annotated[
            int | None,
            Doc("""
                    The task has priority.

                    Default: Task priority value.
                    """),
        ] = None,
        timeout: Annotated[
            float | None,
            Doc("""
                    Task timeout.

                    If specified, the task is returned via `qtasks.results.AsyncTask`.
                    """),
        ] = None,
        task_name: Annotated[
            str | None,
            Doc("""
                    Task name.

                    Default: The value of the task name.
                    """),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc("""
                    kwargs tasks.

                    Default: `{}`.
                    """),
        ],
    ) -> Union[Task, None]:
        """
        Add a task.

        Args:
            priority (int, optional): Task priority. Default: Task priority value.
            args (tuple, optional): task args. Default: `()`.
            kwargs (dict, optional): kwargs of tasks. Default: `{}`.
            timeout (float, optional): Task timeout. If specified, the task is returned via `qtasks.results.SyncTask`.
            task_name (str, optional): Task name. Default: The value of the task name.

        Returns:
            Task|None: Result of the task or `None`.

        Raises:
            ValueError: Task name is not specified.
        """
        if not task_name and not self.task_name:
            raise ValueError("Task name is not specified.")

        if not self._app:
            self._update_app()

        if priority is None:
            priority = self.priority

        return self._app.add_task(  # type: ignore
            task_name or self.task_name,  # type: ignore
            *args,
            priority=priority,
            timeout=timeout,
            **kwargs,
        )

    def __call__(
            self,
            *args: Annotated[
                Any,
                Doc("""
                        args of the task.

                        Default: `()`.
                        """),
            ],
            priority: Annotated[
                int | None,
                Doc("""
                        Task priority.

                        Default: Task priority value.
                        """),
            ] = None,
            timeout: Annotated[
                float | None,
                Doc("""
                        Task timeout.

                        If specified, the task is returned via `qtasks.results.AsyncTask`.
                        """),
            ] = None,
            task_name: Annotated[
                str | None,
                Doc("""
                        Task name.

                        Default: The value of the task name.
                        """),
            ] = None,
            **kwargs: Annotated[
                Any,
                Doc("""
                        kwargs tasks.

                        Default: `{}`.
                        """),
            ]
    ) -> SyncTaskCls:
        """Create SyncTaskCls instance.

        Args:
            priority (int, optional): Task priority. Default: Task priority value.
            args (tuple, optional): task args. Default: `()`.
            kwargs (dict, optional): kwargs of tasks. Default: `{}`.
            timeout (float, optional): Task timeout. If specified, the task is returned via `qtasks.results.SyncTask`.
            task_name (str, optional): Task name. Default: The value of the task name.
        """
        task_cls = SyncTaskCls(
            task_name=task_name or self.task_name,
            priority=priority or self.priority,
            timeout=timeout,
            args=args,
            kwargs=kwargs
        )
        task_cls.bind(self)
        return task_cls

    def _update_app(self):
        if not self._app:
            import qtasks._state

            if qtasks._state.app_main is None:
                raise ImportError("Unable to get app!")
            self._app = qtasks._state.app_main
        return

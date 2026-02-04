"""Async Task."""
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

from qtasks.contexts.async_context import AsyncContext
from qtasks.schemas.task_cls import AsyncTaskCls
from qtasks.types.annotations import P, R

if TYPE_CHECKING:
    from qtasks.asyncio import QueueTasks
    from qtasks.executors.base import BaseTaskExecutor
    from qtasks.middlewares.task import TaskMiddleware
    from qtasks.schemas.task import Task


class AsyncTask(Generic[P, R]):
    """
    `AsyncTask` - class for replacing a function with a `@app.task` and `@shared_task` decorator.

    ## Example

    ```python
    import asyncio
    from qtasks import QueueTasks

    app = QueueTasks()

    @app.task("test")
    async def test():
        print("This is a test!")

    asyncio.run(await test.add_task())
    ```
    """

    def __init__(
        self,
        task_name: Annotated[
            str | None,
            Doc(
                """
                    Имя задачи.

                    По умолчанию: `func.__name__`.
                    """
            ),
        ] = None,
        priority: Annotated[
            int | None,
            Doc(
                """
                    Приоритет у задачи по умолчанию.

                    По умолчанию: `config.task_default_priority`.
                    """
            ),
        ] = None,
        echo: Annotated[
            bool,
            Doc(
                """
                    Добавить AsyncTask первым параметром.

                    По умолчанию: `False`.
                    """
            ),
        ] = False,
        max_time: Annotated[
            float | None,
            Doc(
                """
                    Максимальное время выполнения задачи в секундах.

                    По умолчанию: `None`.
                """
            ),
        ] = None,
        retry: Annotated[
            int | None,
            Doc(
                """
                    Количество попыток повторного выполнения задачи.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        retry_on_exc: Annotated[
            list[type[Exception]] | None,
            Doc(
                """
                    Исключения, при которых задача будет повторно выполнена.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        decode: Annotated[
            Callable | None,
            Doc(
                """
                    Декодер результата задачи.

                    По умолчанию: `None`.
                """
            ),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Doc(
                """
                    Теги задачи.

                    По умолчанию: `None`.
                """
            ),
        ] = None,
        description: Annotated[
            str | None,
            Doc(
                """
                    Описание задачи.

                    По умолчанию: `None`.
                """
            ),
        ] = None,
        generate_handler: Annotated[
            Callable | None,
            Doc(
                """
                    Генератор обработчика.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        executor: Annotated[
            type[BaseTaskExecutor] | None,
            Doc(
                """
                    Класс `BaseTaskExecutor`.

                    По умолчанию: `SyncTaskExecutor`.
                    """
            ),
        ] = None,
        middlewares_before: Annotated[
            list[type[TaskMiddleware]] | None,
            Doc(
                """
                    Мидлвари, которые будут выполнены перед задачей.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        middlewares_after: Annotated[
            list[type[TaskMiddleware]] | None,
            Doc(
                """
                    Мидлвари, которые будут выполнены после задачи.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        extra: Annotated[
            dict[str, Any] | None,
            Doc(
                """
                    Дополнительные параметры.

                    По умолчанию: `Пустой словарь`.
                    """
            ),
        ] = None,
        app: Annotated[
            Optional[QueueTasks],
            Doc(
                """
                    `QueueTasks` экземпляр.

                    По умолчанию: `qtasks._state.app_main`.
                    """
            ),
        ] = None,
    ):
        """
        Initializing an asynchronous task.

        Args:
            task_name (str, optional): Task name. Default: `None`.
            priority (int, optional): Task priority. Default: `None`.
            echo (bool, optional): Add AsyncTask as the first parameter. Default: `False`.
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

        self._app: QueueTasks | None = app

        self.ctx = AsyncContext(
            task_name=task_name,
            generate_handler=generate_handler,
            executor=executor,
            app=app,
        )

    async def add_task(
        self,
        *args: Annotated[
            Any,
            Doc(
                """
                    args задачи.

                    По умолчанию: `()`.
                    """
            ),
        ],
        priority: Annotated[
            int | None,
            Doc(
                """
                    Приоритет задачи.

                    По умолчанию: Значение приоритета у задачи.
                    """
            ),
        ] = None,
        timeout: Annotated[
            float | None,
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        task_name: Annotated[
            str | None,
            Doc(
                """
                    Имя задачи.

                    По умолчанию: Значение имени у задачи.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Any,
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
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
            ValueError: Task name not specified.
        """
        if not task_name and not self.task_name:
            raise ValueError("Не указано имя задачи.")

        if not self._app:
            self._update_app()

        if priority is None:
            priority = self.priority

        return await self._app.add_task(  # type: ignore
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
                Doc(
                    """
                        args задачи.

                        По умолчанию: `()`.
                        """
                ),
            ],
            priority: Annotated[
                int | None,
                Doc(
                    """
                        Приоритет задачи.

                        По умолчанию: Значение приоритета у задачи.
                        """
                ),
            ] = None,
            timeout: Annotated[
                float | None,
                Doc(
                    """
                        Таймаут задачи.

                        Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                        """
                ),
            ] = None,
            task_name: Annotated[
                str | None,
                Doc(
                    """
                        Имя задачи.

                        По умолчанию: Значение имени у задачи.
                        """
                ),
            ] = None,
            **kwargs: Annotated[
                Any,
                Doc(
                    """
                        kwargs задачи.

                        По умолчанию: `{}`.
                        """
                ),
            ]
    ) -> AsyncTaskCls:
        """Create AsyncTaskCls instance.

        Args:
            priority (int, optional): Task priority. Default: Task priority value.
            args (tuple, optional): task args. Default: `()`.
            kwargs (dict, optional): kwargs of tasks. Default: `{}`.
            timeout (float, optional): Task timeout. If specified, the task is returned via `qtasks.results.AsyncTask`.
            task_name (str, optional): Task name. Default: The value of the task name.
        """
        task_cls = AsyncTaskCls(
            task_name=task_name or self.task_name,
            priority=priority or self.priority,
            timeout=timeout,
            args=args,
            kwargs=kwargs
        )
        task_cls.bind(self)
        return task_cls

    def _update_app(self):
        """Application update."""
        if not self._app:
            import qtasks._state

            if qtasks._state.app_main is None:
                raise ImportError("QTasks app is not initialized.")
            self._app = qtasks._state.app_main  # type: ignore
        return

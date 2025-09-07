"""Sync Task."""

from typing import TYPE_CHECKING, Any, Callable, Dict, Generic, List, Optional, Type, Union
from typing_extensions import Annotated, Doc

from qtasks.types.annotations import P, R
from qtasks.contexts.sync_context import SyncContext
from qtasks.executors.base import BaseTaskExecutor
from qtasks.middlewares.task import TaskMiddleware


if TYPE_CHECKING:
    from qtasks import QueueTasks
    from qtasks.schemas.task import Task


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

    def __init__(
        self,
        task_name: Annotated[
            Optional[str],
            Doc(
                """
                    Имя задачи.

                    По умолчанию: `func.__name__`.
                    """
            ),
        ] = None,
        priority: Annotated[
            Optional[int],
            Doc(
                """
                    Приоритет у задачи по умолчанию.

                    По умолчанию: `config.default_task_priority`.
                    """
            ),
        ] = None,
        echo: Annotated[
            bool,
            Doc(
                """
                    Добавить SyncTask первым параметром.

                    По умолчанию: `False`.
                    """
            ),
        ] = False,
        max_time: Annotated[
            Union[float, None],
            Doc(
                """
                    Максимальное время выполнения задачи в секундах.

                    По умолчанию: `None`.
                """
            ),
        ] = None,
        retry: Annotated[
            int,
            Doc(
                """
                    Количество попыток повторного выполнения задачи.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        retry_on_exc: Annotated[
            List[Type[Exception]],
            Doc(
                """
                    Исключения, при которых задача будет повторно выполнена.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        decode: Annotated[
            Callable,
            Doc(
                """
                    Декодер результата задачи.
                """
            )
        ] = None,
        tags: Annotated[
            List[str],
            Doc(
                """
                    Теги задачи.

                    По умолчанию: `None`.
                """
            )
        ] = None,
        description: Annotated[
            str,
            Doc(
                """
                    Описание задачи.

                    По умолчанию: `None`.
                """
            )
        ] = None,
        generate_handler: Annotated[
            Callable,
            Doc(
                """
                    Генератор обработчика.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        executor: Annotated[
            Type["BaseTaskExecutor"],
            Doc(
                """
                    Класс `BaseTaskExecutor`.

                    По умолчанию: `SyncTaskExecutor`.
                    """
            ),
        ] = None,
        middlewares_before: Annotated[
            List["TaskMiddleware"],
            Doc(
                """
                    Мидлвари, которые будут выполнены перед задачей.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        middlewares_after: Annotated[
            List["TaskMiddleware"],
            Doc(
                """
                    Мидлвари, которые будут выполнены после задачи.

                    По умолчанию: `Пустой массив`.
                    """
            ),
        ] = None,
        extra: Annotated[
            Dict[str, Any],
            Doc(
                """
                    Дополнительные параметры.

                    По умолчанию: `Пустой словарь`.
                    """
            ),
        ] = None,
        app: Annotated[
            "QueueTasks",
            Doc(
                """
                    `QueueTasks` экземпляр.

                    По умолчанию: `qtasks._state.app_main`.
                    """
            ),
        ] = None,
    ):
        """Инициализация синхронной задачи.

        Args:
            task_name (str, optional): Имя задачи. По умолчанию: `None`.
            priority (int, optional): Приоритет задачи. По умолчанию: `None`.
            echo (bool, optional): Добавить SyncTask первым параметром. По умолчанию: `False`.
            max_time (float, optional): Максимальное время выполнения задачи в секундах. По умолчанию: `None`.
            retry (int, optional): Количество попыток повторного выполнения задачи. По умолчанию: `None`.
            retry_on_exc (List[Type[Exception]], optional): Исключения, при которых задача будет повторно выполнена. По умолчанию: `None`.
            decode (Callable, optional): Декодер результата задачи. По умолчанию: `None`.
            tags (List[str], optional): Теги задачи. По умолчанию: `None`.
            description (str, optional): Описание задачи. По умолчанию: `None`.
            generate_handler (Callable, optional): Генератор обработчика. По умолчанию: `None`.
            executor (Type["BaseTaskExecutor"], optional): Класс `BaseTaskExecutor`. По умолчанию: `None`.
            middlewares_before (List["TaskMiddleware"], optional): Мидлвари, которые будут выполнены перед задачей. По умолчанию: `Пустой массив`.
            middlewares_after (List["TaskMiddleware"], optional): Мидлвари, которые будут выполнены после задачи. По умолчанию: `Пустой массив`.
            app (QueueTasks, optional): `QueueTasks` экземпляр. По умолчанию: `None`.
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
            Optional[tuple],
            Doc(
                """
                    args задачи.

                    По умолчанию: `()`.
                    """
            ),
        ],
        priority: Annotated[
            Optional[int],
            Doc(
                """
                    Приоритет у задачи.

                    По умолчанию: Значение приоритета у задачи.
                    """
            ),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
                    """
            ),
        ] = None,
        task_name: Annotated[
            str,
            Doc(
                """
                    Имя задачи.

                    По умолчанию: Значение имени у задачи.
                    """
            ),
        ] = None,
        **kwargs: Annotated[
            Optional[dict],
            Doc(
                """
                    kwargs задачи.

                    По умолчанию: `{}`.
                    """
            ),
        ],
    ) -> Union["Task", None]:
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

        return self._app.add_task(
            *args,
            task_name=task_name or self.task_name,
            priority=priority,
            timeout=timeout,
            **kwargs
        )

    def _update_app(self) -> "QueueTasks":
        if not self._app:
            import qtasks._state

            if qtasks._state.app_main is None:
                raise ImportError("Невозможно получить app!")
            self._app = qtasks._state.app_main
        return

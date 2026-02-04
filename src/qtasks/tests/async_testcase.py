"""Async test classes."""

import asyncio
import threading
from time import time
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional, Union
from uuid import UUID, uuid4

from typing_extensions import Doc

from qtasks.tests.base import BaseTestCase

if TYPE_CHECKING:
    from qtasks.asyncio import QueueTasks
    from qtasks.schemas.task import Task
    from qtasks.starters.base import BaseStarter


class AsyncTestCase(BaseTestCase[Literal[True]]):
    """
    Asynchronous testing case.
    
        ## Example
    
        ```python
        from qtasks import QueueTasks
        from qtasks.tests import AsyncTestCase
    
        app = QueueTasks()
    
        test_case = AsyncTestCase(app=app)
        ```
    """

    def __init__(
        self,
        app: Annotated[
            "QueueTasks",
            Doc(
                """
                    Основной экземпляр.
                    """
            ),
        ],
        name: Annotated[
            str | None,
            Doc(
                """
                    Имя проекта. Это имя может быть использовано для тестовых компонентов.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
    ):
        """
        Asynchronous test case.
        
                Args:
                    app(QueueTasks, Doc): Main instance.
                    name (str, optional): Project name. This name can be used for test components. Default: `None`.
        """
        super().__init__(app=app, name=name)
        self.app: QueueTasks

        self._global_loop: asyncio.AbstractEventLoop | None = None

    def start_in_background(
        self,
        starter: Annotated[
            Optional["BaseStarter"],
            Doc(
                """
                    Стартер. Хранит в себе способы запуска компонентов.

                    По умолчанию: `qtasks.starters.AsyncStarter`.
                    """
            ),
        ] = None,
        num_workers: Annotated[
            int,
            Doc(
                """
                    Количество запущенных воркеров.

                    По умолчанию: `4`.
                    """
            ),
        ] = 4,
        reset_config: Annotated[
            bool,
            Doc(
                """
                    Обновить config у воркера и брокера.

                    По умолчанию: `True`.
                    """
            ),
        ] = True,
    ):  # TODO: fix!
        """
        Run `app.run_forever()` in the background.
        
                Args:
                    starter (BaseStarter, optional): Starter. Default: `qtasks.starters.AsyncStarter`.
                    num_workers (int, optional): Number of workers running. Default: 4.
                    reset_config (bool, optional): Update the config of the worker and broker. Default: True.
        """

        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.start(loop=loop, num_workers=num_workers))
            finally:
                loop.close()

        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()

    async def start(
        self,
        loop: Annotated[
            asyncio.AbstractEventLoop | None,
            Doc(
                """
                    Асинхронный loop.

                    По умолчанию: `None`.
                    """
            ),
        ] = None,
        starter: Annotated[
            Optional["BaseStarter"],
            Doc(
                """
                    Стартер. Хранит в себе способы запуска компонентов.

                    По умолчанию: `qtasks.starters.AsyncStarter`.
                    """
            ),
        ] = None,
        num_workers: Annotated[
            int,
            Doc(
                """
                    Количество запущенных воркеров.

                    По умолчанию: `4`.
                    """
            ),
        ] = 4,
        reset_config: Annotated[
            bool,
            Doc(
                """
                    Обновить config у воркера и брокера.

                    По умолчанию: `True`.
                    """
            ),
        ] = True,
    ) -> None:
        """
        Runs `app.run_forever()`.
        
                Args:
                    loop (asyncio.AbstractEventLoop, optional): async loop. Default: None.
                    starter (BaseStarter, optional): Starter. Default: `qtasks.starters.AsyncStarter`.
                    num_workers (int, optional): Number of workers running. Default: 4.
                    reset_config (bool, optional): Update the config of the worker and broker. Default: True.
        """
        self.app.run_forever(
            loop=loop,
            starter=starter,
            num_workers=num_workers,
            reset_config=reset_config,
        )

    async def stop(self):
        """Stops the test case."""
        if self.test_config.global_config and self.app.broker.storage.global_config:
            await self.app.broker.storage.global_config.stop()

        if self.test_config.storage:
            await self.app.broker.storage.stop()

        if self.test_config.broker:
            await self.app.broker.stop()

        if self.test_config.worker:
            await self.app.worker.stop()
        return

    async def add_task(
        self,
        task_name: Annotated[
            str,
            Doc(
                """
                    Имя задачи.
                    """
            ),
        ],
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
            int,
            Doc(
                """
                    Приоритет у задачи.

                    По умолчанию: `0`.
                    """
            ),
        ] = 0,
        timeout: Annotated[
            float | None,
            Doc(
                """
                    Таймаут задачи.

                    Если указан, задача возвращается через `qtasks.results.AsyncTask`.
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
    ) -> Union["Task", None]:
        """
        Add a task.
        
                Args:
                    task_name (str): The name of the task.
                    priority (int, optional): Task priority. Default: `0`.
                    args (tuple, optional): task args. Default: `()`.
                    kwargs (dict, optional): kwargs of tasks. Default: `{}`
        
                    timeout (float, optional): Task timeout. If specified, the task is called via `qtasks.results.AsyncResult`.
        
                Returns:
                    Task|None: Task data or None.
        """
        if self.test_config.broker:
            return await self.app.add_task(
                task_name, *args, priority=priority, timeout=timeout, **kwargs
            )
        elif self.test_config.worker:
            return await self.app.worker.add(
                name=task_name,
                uuid=uuid4(),
                priority=priority,
                created_at=time(),
                args=args or (),
                kwargs=kwargs or {},
            )
        else:
            print(
                f"[AsyncTestCase: {self.name}] Обязательно включить Воркер или Брокер!"
            )
            return

    async def get(
        self,
        uuid: Annotated[
            UUID | str,
            Doc(
                """
                    UUID задачи.
                    """
            ),
        ],
    ) -> Union["Task", None]:
        """
        Get a task.
        
                Args:
                    uuid (UUID|str): UUID of the Task.
        
                Returns:
                    Task|None: Task data or None.
        """
        if isinstance(uuid, str):
            uuid = UUID(uuid)
        if not self.test_config.broker:
            print(f"[AsyncTestCase: {self.name}] Обязательно включить Брокер!")
            return
        return await self.app.broker.get(uuid=uuid)

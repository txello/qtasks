import asyncio
import threading
from time import time
from typing import TYPE_CHECKING, Optional, Union
from uuid import UUID, uuid4
from typing_extensions import Annotated, Doc
from qtasks.schemas.task import Task
from qtasks.tests.base import BaseTestCase

from qtasks.asyncio import QueueTasks

if TYPE_CHECKING:
    from qtasks.starters.base import BaseStarter


class AsyncTestCase(BaseTestCase):
    """
    Асинхронный кейс тестирования.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.tests import AsyncTestCase
    
    app = QueueTasks()
    
    test_case = AsyncTestCase(app=app)
    ```
    """
    
    def __init__(self,
            app: Annotated[
                "QueueTasks",
                Doc(
                    """
                    Основной экземпляр.
                    """
                )
            ],
            name: Annotated[
                Optional[str],
                Doc(
                    """
                    Имя проекта. Это имя может быть использовано для тестовых компонентов.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
        ):
        super().__init__(app=app, name=name)
        
        self._global_loop: asyncio.AbstractEventLoop|None = None
    
    def start_in_background(self,
            starter: Annotated[
                Optional["BaseStarter"],
                Doc(
                    """
                    Стартер. Хранит в себе способы запуска компонентов.
                    
                    По умолчанию: `qtasks.starters.AsyncStarter`.
                    """
                )
            ] = None,
            num_workers: Annotated[
                int,
                Doc(
                    """
                    Количество запущенных воркеров.
                    
                    По умолчанию: `4`.
                    """
                )
            ] = 4,
            reset_config: Annotated[
                bool,
                Doc(
                    """
                    Обновить config у воркера и брокера.
                    
                    По умолчанию: `True`.
                    """
                )
            ] = True
        ): # TODO: fix!
        """Запустить `app.run_forever()` в фоновом режиме.

        Args:
            starter (BaseStarter, optional): Стартер. По умолчанию: `qtasks.starters.AsyncStarter`.
            num_workers (int, optional): Количество запущенных воркеров. По умолчанию: 4.
            reset_config (bool, optional): Обновить config у воркера и брокера. По умолчанию: True.
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
    
    def start(self,
            loop: Annotated[
                Optional[asyncio.AbstractEventLoop],
                Doc(
                    """
                    Асинхронный loop.
                    
                    По умолчанию: `None`.
                    """
                )
            ] = None,
            starter: Annotated[
                Optional["BaseStarter"],
                Doc(
                    """
                    Стартер. Хранит в себе способы запуска компонентов.
                    
                    По умолчанию: `qtasks.starters.AsyncStarter`.
                    """
                )
            ] = None,
            num_workers: Annotated[
                int,
                Doc(
                    """
                    Количество запущенных воркеров.
                    
                    По умолчанию: `4`.
                    """
                )
            ] = 4,
            reset_config: Annotated[
                bool,
                Doc(
                    """
                    Обновить config у воркера и брокера.
                    
                    По умолчанию: `True`.
                    """
                )
            ] = True
        ) -> None:
        """Запускает `app.run_forever()`.

        Args:
            loop (asyncio.AbstractEventLoop, optional): асинхронный loop. По умолчанию: None.
            starter (BaseStarter, optional): Стартер. По умолчанию: `qtasks.starters.AsyncStarter`.
            num_workers (int, optional): Количество запущенных воркеров. По умолчанию: 4.
            reset_config (bool, optional): Обновить config у воркера и брокера. По умолчанию: True.
        """
        self.app.run_forever(loop=loop, num_workers=num_workers, reset_config=reset_config)
    
    async def stop(self):
        """Останавливает кейс тестирования."""
        if self.test_config.global_config:
            self.app.broker.storage.global_config.stop()
        
        if self.test_config.storage:
            self.app.broker.storage.stop()
        
        if self.test_config.broker:
            self.app.broker.stop()
        
        if self.test_config.worker:
            await self.app.worker.stop()
        return
    
    async def add_task(self,
            task_name: Annotated[
                str, 
                Doc("Имя задачи.")
            ],
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
            ] = None,

        timeout: Annotated[
            Optional[float],
            Doc(
                """
                Таймаут задачи.
                
                Если указан, задача вызывается через `qtasks.results.AsyncTask`.
                """
            )
        ] = None
        ) -> Task | None:
        """Добавить задачу.

        Args:
            task_name (str): Имя задачи.
            priority (int, optional): Приоритет задачи. По умолчанию: `0`.
            args (tuple, optional): args задачи. По умолчанию: `()`.
            kwargs (dict, optional): kwargs задачи. По умолчанию: `{}`

            timeout (float, optional): Таймаут задачи. Если указан, задача вызывается через `qtasks.results.AsyncResult`.

        Returns:
            Task|None: Данные задачи или None.
        """
        if self.test_config.broker:
            args, kwargs = args or (), kwargs or {}
            return await self.app.add_task(task_name=task_name, priority=priority, args=args, kwargs=kwargs, timeout=timeout)
        elif self.test_config.worker:
            return await self.app.worker.add(name=task_name, uuid=uuid4(), priority=priority, created_at=time(), args=args or (), kwargs=kwargs or {})
        else:
            print(f"[AsyncTestCase: {self.name}] Обязательно включить Воркер или Брокер!")
            return

    async def get(self,
            uuid: Annotated[
                Union[UUID, str],
                Doc(
                    """
                    UUID задачи.
                    """
                )
            ]
        ) -> Task|None:
        """Получить задачу.

        Args:
            uuid (UUID|str): UUID Задачи.

        Returns:
            Task|None: Данные задачи или None.
        """
        if isinstance(uuid, str):
            uuid = UUID(uuid)
        if not self.test_config.broker:
            print(f"[AsyncTestCase: {self.name}] Обязательно включить Брокер!")
            return
        return await self.app.broker.get(uuid=uuid)
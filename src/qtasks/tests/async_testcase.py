import asyncio
import threading
from time import time
from typing import Optional, Union
from uuid import UUID, uuid4
from typing_extensions import Annotated, Doc
from qtasks.schemas.task import Task
from qtasks.tests.base import BaseTestCase

from qtasks.asyncio import QueueTasks


class AsyncTestCase(BaseTestCase):
    def __init__(self, app: QueueTasks, name: str|None = None):
        super().__init__(app=app, name=name)
        
        self._global_loop: asyncio.AbstractEventLoop|None = None
    
    def start_in_background(self, num_workers: int = 4): # TODO: FIX!
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
            loop = None,
            num_workers: int = 4
        ):
        self.app.run_forever(loop=loop, num_workers=num_workers)
    
    async def stop(self):
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
        ):
        if self.test_config.broker:
            args, kwargs = args or (), kwargs or {}
            return await self.app.add_task(task_name=task_name, priority=priority, args=args, kwargs=kwargs)
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
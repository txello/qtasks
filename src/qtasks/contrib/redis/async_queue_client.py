"""Async Redis command queue."""

import asyncio
import redis.asyncio as aioredis

from qtasks.logs import Logger


class AsyncRedisCommandQueue:
    """
    `AsyncRedisCommandQueue` - Асинхронный класс для работы с `Redis`.

    ## Пример

    ```python
    import asyncio
    from qtasks import QueueTasks
    from qtasks.contrib.redis import AsyncRedisCommandQueue

    redis_contrib = AsyncRedisCommandQueue(redis)
    asyncio.run(redis_contrib.execute("hset", kwargs["name"], mapping=kwargs["mapping"]))
    ```
    """

    def __init__(self, redis: aioredis.Redis, log: Logger = None):
        """Экземпляр класса.

        Args:
            redis (redis.asyncio.Redis): класс `Redis`.
            log (Logger, optional): класс `qtasks.logs.Logger`. По умолчанию: `qtasks._state.log_main`.
        """
        self.log = self._get_log(log)
        self.redis = redis
        self.queue = asyncio.Queue()
        self.worker_task = None
        self.lock = asyncio.Lock()

    async def _worker(self):
        while not self.queue.empty():
            cmd, args, kwargs = await self.queue.get()
            self.log.debug(f"Задача {cmd} с параметрами {args} и {kwargs} вызвана")
            try:
                await getattr(self.redis, cmd)(*args, **kwargs)
            except Exception as e:
                self.log.error(f"Ошибка Redis команды {cmd}: {e}. Args: {args}, Kwargs: {kwargs}")
            self.queue.task_done()

        async with self.lock:
            self.worker_task = None

    async def execute(self, cmd: str, *args, **kwargs):
        """Запрос в `Redis`.

        Args:
            cmd (str): Команда.
            args(tuple, optional): Параметры к команде через *args.
            kwargs(dict, optional): Параметры к команде через *args.
        """
        await self.queue.put((cmd, args, kwargs))
        async with self.lock:
            if self.worker_task is None or self.worker_task.done():
                self.worker_task = asyncio.create_task(self._worker())

    def _get_log(self, log: Logger | None):
        if log is None:
            import qtasks._state

            log = qtasks._state.log_main
        return log.with_subname("AsyncRedisCommandQueue")

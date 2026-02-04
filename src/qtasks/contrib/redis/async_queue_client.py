"""Async Redis command queue."""

import asyncio

import redis.asyncio as aioredis

from qtasks.logs import Logger


class AsyncRedisCommandQueue:
    """
    `AsyncRedisCommandQueue` - Asynchronous class for working with `Redis`.

    ## Example

    ```python
    import asyncio
    from qtasks import QueueTasks
    from qtasks.contrib.redis import AsyncRedisCommandQueue

    redis_contrib = AsyncRedisCommandQueue(redis)
    asyncio.run(redis_contrib.execute("hset", kwargs["name"], mapping=kwargs["mapping"]))
    ```
    """

    def __init__(self, redis: aioredis.Redis, log: Logger | None = None):
        """
        An instance of a class.

        Args:
            redis (redis.asyncio.Redis): class `Redis`.
            log (Logger, optional): class `qtasks.logs.Logger`. Default: `qtasks._state.log_main`.
        """
        self.log = self._get_log(log)
        self.redis = redis
        self.queue = asyncio.Queue()
        self.worker_task = None
        self.lock = asyncio.Lock()

    async def _worker(self):
        while not self.queue.empty():
            cmd, args, kwargs = await self.queue.get()
            self.log.debug(f"Task {cmd} with parameters {args} and {kwargs} executed")
            try:
                await getattr(self.redis, cmd)(*args, **kwargs)
            except Exception as e:
                self.log.error(
                    f"Error executing Redis command {cmd}: {e}. Args: {args}, Kwargs: {kwargs}"
                )
            self.queue.task_done()

        async with self.lock:
            self.worker_task = None

    async def execute(self, cmd: str, *args, **kwargs):
        """
        Query in `Redis`.

        Args:
            cmd (str): Command.
            args(tuple, optional): Parameters to the command via *args.
            kwargs(dict, optional): Parameters to the command via *args.
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

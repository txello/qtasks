"""Sync Redis command queue."""

import threading
from queue import Queue, Empty
import redis

from qtasks.logs import Logger


class SyncRedisCommandQueue:
    """
    `SyncRedisCommandQueue` - Асинхронный класс для работы с `Redis`.

    ## Пример

    ```python
    from qtasks import QueueTasks
    from qtasks.contrib.redis import SyncRedisCommandQueue

    redis_contrib = SyncRedisCommandQueue(redis)
    redis_contrib.execute("hset", kwargs["name"], mapping=kwargs["mapping"])
    ```
    """

    def __init__(self, redis: redis.Redis, log: Logger = None):
        """Экземпляр класса.

        Args:
            redis (redis.asyncio.Redis): класс `Redis`.
            log (Logger, optional): класс `qtasks.logs.Logger`. По умолчанию: `qtasks._state.log_main`.
        """
        self.log = self._get_log(log)
        self.redis = redis
        self.queue = Queue()
        self.worker_thread = None
        self.lock = threading.Lock()

    def _worker(self):
        while True:
            try:
                cmd, args, kwargs = self.queue.get(timeout=2)  # 2 секунды "жизни"
                self.log.debug(f"Задача {cmd} с параметрами {args} и {kwargs} вызвана")
                getattr(self.redis, cmd)(*args, **kwargs)
                self.queue.task_done()
            except Empty:
                break  # Если очередь пуста 2 секунды — выходим

        with self.lock:
            self.worker_thread = None  # Отмечаем, что воркер завершился

    def execute(self, cmd: str, *args, **kwargs):
        """Запрос в `Redis`.

        Args:
            cmd (str): Команда.
            args(tuple, optional): Параметры к команде через *args.
            kwargs(dict, optional): Параметры к команде через *args.
        """
        self.queue.put((cmd, args, kwargs))
        with self.lock:
            if self.worker_thread is None or not self.worker_thread.is_alive():
                self.worker_thread = threading.Thread(target=self._worker, daemon=True)
                self.worker_thread.start()

    def _get_log(self, log: Logger | None):
        if log is None:
            import qtasks._state

            log = qtasks._state.log_main
        return log.with_subname("SyncRedisCommandQueue")

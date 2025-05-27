import threading
from queue import Queue, Empty
import redis

from qtasks.logs import Logger

class SyncRedisCommandQueue:
    def __init__(self,
            redis: redis.Redis,
            log: Logger = None):
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

    def execute(self, cmd, *args, **kwargs):
        self.queue.put((cmd, args, kwargs))
        with self.lock:
            if self.worker_thread is None or not self.worker_thread.is_alive():
                self.worker_thread = threading.Thread(target=self._worker, daemon=True)
                self.worker_thread.start()

    def _get_log(self, log: Logger|None):
        if log is None:
            import qtasks._state
            log = qtasks._state.log_main
        return log.with_subname("SyncRedisCommandQueue")
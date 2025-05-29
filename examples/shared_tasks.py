from qtasks import shared_task

from libs.task_executor import MySyncTaskExecutor, MyAsyncTaskExecutor
from libs.task_middleware import MyTaskMiddleware
from qtasks.registries.sync_task_decorator import SyncTask


@shared_task(middlewares=[MyTaskMiddleware], echo=True)
def sync_test(self: SyncTask):
    task = self.add_task("test", timeout=50)
    print(task.returning)

@shared_task(middlewares=[MyTaskMiddleware], awaiting=True)
async def async_test():
    print("async_test")

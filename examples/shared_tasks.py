from qtasks import shared_task

from libs.task_executor import MySyncTaskExecutor, MyAsyncTaskExecutor
from libs.task_middleware import MyTaskMiddleware


@shared_task(priority=0, middlewares=[MyTaskMiddleware])
def sync_test():
    print("sync_test")

@shared_task(priority=0, middlewares=[MyTaskMiddleware], awaiting = True)
async def async_test():
    print("async_test")

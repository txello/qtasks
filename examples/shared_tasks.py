from qtasks import shared_task

from libs.task_executor import MySyncTaskExecutor, MyAsyncTaskExecutor
from libs.task_middleware import MyTaskMiddleware
from qtasks.registries.sync_task_decorator import SyncTask


def yield_func(result):
    print(result)
    return result


@shared_task(middlewares=[MyTaskMiddleware], echo=True, generate_handler=yield_func)
def sync_test(self: SyncTask):
    print("sync_test")
    yield 1


@shared_task(middlewares=[MyTaskMiddleware], awaiting=True)
async def async_test():
    print("async_test")

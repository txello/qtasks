from libs.task_middleware import MyTaskMiddleware

from qtasks import shared_task
from qtasks.registries.sync_task_decorator import SyncTask


def yield_func(result):
    print(result)
    return result


@shared_task(
    description="Test synchronous task with decorator",
    middlewares_after=[MyTaskMiddleware],
    echo=True,
    generate_handler=yield_func
)
def sync_test(self: SyncTask):
    print("sync_test")
    yield 1


@shared_task(
    description="Test asynchronous task",
    middlewares_after=[MyTaskMiddleware],
    awaiting=True
)
async def async_test():
    print("async_test")

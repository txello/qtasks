from contextlib import asynccontextmanager, contextmanager
from typing import Annotated

from qtasks.asyncio import QueueTasks
from qtasks.plugins.depends import Depends, ScopeEnum


app = QueueTasks()
app.config.delete_finished_tasks = True
app.config.running_older_tasks = True
app.config.logs_default_level_server = 20


class AwaitableClass:
    def __await__(self):
        print("Awaiting...")
        return self.some_coroutine().__await__()

    async def some_coroutine(self):
        return 123

async def test_dep():
    print("Open")
    try:
        yield 123
    finally:
        print("Close")


@app.task
async def test(dep: Annotated[int, Depends(test_dep, scope=ScopeEnum.TASK)]):
    print(dep)


if __name__ == "__main__":
    app.run_forever()

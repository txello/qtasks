from contextlib import asynccontextmanager
from typing import Annotated

from qtasks.asyncio import QueueTasks
from qtasks.plugins import Depends


app = QueueTasks()
app.config.delete_finished_tasks = True
app.config.running_older_tasks = True
app.config.logs_default_level_server = 20


@asynccontextmanager
async def test_dep():
    print("Open")
    yield 123
    print("Close")


@app.task
async def test(dep: Annotated[int, Depends(test_dep, scope="task")]):
    print(dep)


@app.task
async def close_worker():
    # await app.worker.stop()
    pass


if __name__ == "__main__":
    app.run_forever()

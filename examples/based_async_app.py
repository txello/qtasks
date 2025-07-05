import logging

from qtasks.asyncio import QueueTasks
from qtasks.registries import AsyncTask, SyncTask

import shared_tasks
import router_tasks

app = QueueTasks() 
app.config.logs_default_level = logging.INFO
app.config.running_older_tasks = True

app.include_router(router_tasks.router)


@app.task()
async def load_test_job(num):
    print("Задача {num}")


@app.task(name="test")
async def test():
    print("Это тестовая задача!")


@app.task(name="test_num")
def test_num(number: int):
    print(f"Number: {number}")
    return number


@app.task(name="test_echo", echo=True)
async def test_echo(self: AsyncTask):
    task = await self.add_task(task_name="test_num", args=(5,), timeout=50)
    print(f"Задача {task.task_name}, результат: {task.returning}")
    return str(task)


@app.task(retry=5, retry_on_exc=[ZeroDivisionError])
def error_zero():
    result = 1/0
    print(result)


async def yield_func(result):
    print(result)
    return result + 2


@app.task(generate_handler=yield_func, echo=True)
async def test_yield(self: AsyncTask, n: int):
    self.ctx.get_logger().info(self.ctx.task_uuid)
    for _ in range(n):
        n += 1
        yield n


from pydantic import BaseModel
from libs.plugins.taskexecutor import AsyncTaskExecutorArgsPydanticPlugin


class TestPydanticModel(BaseModel):
    name: str


j = 0


@app.task(echo=True, retry=3)
async def test_pydantic(self: AsyncTask, model: TestPydanticModel):
    global j
    if j != 2:
        j += 1
        raise ValueError("Test error")

    print(model.name)
    return model


if __name__ == "__main__":
    app.run_forever(num_workers=10)

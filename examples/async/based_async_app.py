
import json
import logging
import time

import pydantic
import router_tasks
import shared_tasks

from qtasks.asyncio.qtasks import QueueTasks
from qtasks.registries.async_task_decorator import AsyncTask
from qtasks.stats.async_stats import AsyncStats

app = QueueTasks()
app.config.logs_default_level_server = logging.DEBUG
app.config.running_older_tasks = True
app.config.result_time_interval = 0.1

app.include_router(router_tasks.router)


@app.task(
    description="Task for load testing"
)
async def load_test_job(num: int):
    end_time = time.time()
    print(f"Job {num} finished at {end_time}")
    return


@app.task(
    name="test",
    description="Test Task."
)
async def test():
    print("It's a test task!")


@app.task(
    name="test_num",
    description="Test task with a number"
)
def test_num(number: int):
    print(f"Number: {number}")
    return number


@app.task(
    name="test_echo",
    description="Test task with console output",
    echo=True
)
async def test_echo(self: AsyncTask):
    task = await self.add_task(5, task_name="test_num", timeout=50)
    if task:
        print(f"Task {task.task_name}, result: {task.returning}")
        return str(task)


@app.task(
    description="Test task with exception handling",
    retry=5,
    retry_on_exc=[ZeroDivisionError]
)
def error_zero():
    result = 1/0
    print(result)


async def yield_func(result):
    print(result)
    return result + 2


@app.task(
    description="Test task with generator",
    echo=True,
    generate_handler=yield_func
)
async def test_yield(self: AsyncTask, n: int):
    self.ctx.get_logger().info(self.ctx.task_uuid)
    for _ in range(n):
        n += 1
        yield n


@app.task(
    description="Test task with retry",
    echo=True,
    retry=2
)
async def test_retry(self: AsyncTask):
    self.ctx.get_logger().info("Retry...")
    raise KeyError("Test error")


class Item(pydantic.BaseModel):
    name: str
    value: int


@app.task(
    description="Test task with Pydantic",
    tags=["example"],
    # echo=True,
    decode=json.dumps,
)
async def example_pydantic(item: Item):
    return f"Hello, {item.name}!"


@app.task(
    description="Test task for demonstrating context usage",
    echo=True, tags=["test"], priority=1,
    retry=3, retry_on_exc=[KeyError], decode=json.dumps,
    # generate_handler=yield_func, executor=MyTaskExecutor,
    # middlewares_before=[MyTaskMiddleware], middlewares_after=[MyTaskMiddleware],
    test="test"
)
async def test_echo_ctx(self: AsyncTask):
    # app = self.ctx._app - QueueTasks instance
    # self.ctx.get_logger(name="NewName" or task name)
    self.ctx.get_logger().info("This is a test task!")
    await self.ctx.sleep(5)
    # task = await self.add_task(task_name="test", timeout=50)
    # worker = self.ctx.get_component("worker")
    self.ctx.get_logger().info(self.ctx.get_config())
    # task = self.ctx.get_metadata(cache=True)
    # self.ctx.get_task(uuid="UUID")
    self.ctx.get_logger().info(
        f"""
            UUID: {self.ctx.task_uuid}
            Name: {self.task_name}
            Tags: {self.tags}
            Priority: {self.priority}
            Additional parameters: {self.extra}

            Retry count of the task: {self.retry}
            Exceptions for repetition: {self.retry_on_exc}
            Function for decorator: {self.ctx.generate_handler}

            Is self caused: {self.echo}
            Decoding via parameter: {self.decode}

            TaskExecutor via parameter: {self.executor}
            Middleware before: {self.middlewares_before}
            Middleware after: {self.middlewares_after}
            """
    )
    self.ctx.cancel("Test task cancelled")
    # raise KeyError - will cause the task to be executed again. If retry_on_exc is not specified, it will respond to all.
    # retry=3 - repeat 3 more times.
    return "Hello, world!"


@app.task
async def example_stats():
    inspect = await stats.inspect()
    print(inspect.tasks())


@app.task(echo=True, max_time=2)
async def example_error_timeout(self: AsyncTask):
    await self.ctx.sleep(5)
    return "This task took too long to complete."


stats = AsyncStats(app=app)

if __name__ == "__main__":
    app.run_forever(num_workers=10)

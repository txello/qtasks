import json
import logging
import time

import pydantic

from qtasks.asyncio import QueueTasks
from qtasks.registries import AsyncTask

from qtasks.stats.async_stats import AsyncStats
import shared_tasks
import router_tasks

app = QueueTasks()
app.config.logs_default_level = logging.INFO
app.config.running_older_tasks = True

app.include_router(router_tasks.router)


@app.task(
    description="Задача для тестирования нагрузки."
)
async def load_test_job(num: int):
    end_time = time.time()
    print(f"Job {num} finished at {end_time}")
    return


@app.task(
    name="test",
    description="Тестовая задача."
)
async def test():
    print("Это тестовая задача!")


@app.task(
    name="test_num",
    description="Тестовая задача с числом."
)
def test_num(number: int):
    print(f"Number: {number}")
    return number


@app.task(
    name="test_echo",
    description="Тестовая задача с выводом в консоль.",
    echo=True
)
async def test_echo(self: AsyncTask):
    task = await self.add_task(task_name="test_num", args=(5,), timeout=50)
    print(f"Задача {task.task_name}, результат: {task.returning}")
    return str(task)


@app.task(
    description="Тестовая задача с обработкой исключения ZeroDivisionError.",
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
    description="Тестовая задача с генератором.",
    echo=True,
    generate_handler=yield_func
)
async def test_yield(self: AsyncTask, n: int):
    self.ctx.get_logger().info(self.ctx.task_uuid)
    for _ in range(n):
        n += 1
        yield n


@app.task(
    description="Тестовая задача с повтором.",
    echo=True,
    retry=2
)
async def test_retry(self: AsyncTask):
    self.ctx.get_logger().info("Повтор...")
    raise KeyError("Test error")


class Item(pydantic.BaseModel):
    name: str
    value: int


@app.task(
    description="Тестовая задача с использованием Pydantic.",
    tags=["example"],
    echo=True,
    decode=json.dumps,
)
async def example_pydantic(self: AsyncTask, item: Item):
    return f"Hello, {item.name}!"


@app.task(
    description="Тестовая задача для демонстрации работы с контекстом.",
    echo=True, tags=["test"], priority=1,
    retry=3, retry_on_exc=[KeyError], decode=json.dumps,
    # generate_handler=yield_func, executor=MyTaskExecutor,
    # middlewares_before=[MyTaskMiddleware], middlewares_after=[MyTaskMiddleware],
    test="test"
)
async def test_echo_ctx(self: AsyncTask):
    # app = self.ctx._app - экземпляр QueueTasks
    # self.ctx.get_logger(name="NewName" или имя задачи)
    self.ctx.get_logger().info("Это тестовая задача!")
    await self.ctx.sleep(5)
    # task = await self.add_task(task_name="test", timeout=50)
    # worker = self.ctx.get_component("worker")
    self.ctx.get_logger().info(self.ctx.get_config())
    # task = self.ctx.get_metadata(cache=True)
    # self.ctx.get_task(uuid="UUID")
    self.ctx.get_logger().info(
        f"""
            UUID: {self.ctx.task_uuid}
            Имя: {self.task_name}
            Теги: {self.tags}
            Приоритет: {self.priority}
            Дополнительные параметры: {self.extra}

            Повторений через параметр: {self.retry}
            Исключения для повтора: {self.retry_on_exc}
            Функция для декоратора: {self.ctx.generate_handler}

            Вызван ли self: {self.echo}
            Декордирование через параметр: {self.decode}

            TaskExecutor через параметр: {self.executor}
            Миддлвари: {self.middlewares}
            """
    )
    self.ctx.cancel("Тестовая задача отменена")
    # raise KeyError - вызовет повторное выполнение задачи. Если не указано retry_on_exc - реагирует на все.
    # retry=3 - повторит ещё 3 раза.
    return "Hello, world!"


@app.task()
async def example_stats():
    print(stats.inspect().tasks())

stats = AsyncStats(app=app)

if __name__ == "__main__":
    app.run_forever(num_workers=10)

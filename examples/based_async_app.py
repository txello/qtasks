import logging

from qtasks.asyncio import QueueTasks
from qtasks.registries import AsyncTask

import shared_tasks

app = QueueTasks() 
app.config.logs_default_level = logging.INFO
app.config.running_older_tasks = True

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
    return

@app.task(retry=5)
def error_zero():
    result = 1/0

async def yield_func(result):
    print(result)
    return result

@app.task(generate_handler=yield_func, echo=True)
async def test_yield(self: AsyncTask, n: int):
    for _ in range(n):
        n += 1
        yield n


if __name__ == "__main__":
    app.run_forever(num_workers=10)

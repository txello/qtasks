import logging

import pydantic
from qtasks import QueueTasks
from qtasks.plugins.testing.sync_test import SyncTestPlugin
from qtasks.registries import SyncTask

import shared_tasks
import router_tasks

app = QueueTasks()
app.config.logs_default_level_server = logging.INFO
app.config.running_older_tasks = True

app.include_router(router_tasks.router)
app.add_plugin(SyncTestPlugin(), trigger_names=["worker_execute_before", "worker_remove_finished_task"], component="worker")


@app.task(name="test")
def test():
    print("Это тестовая задача!")


@app.task(name="test_num")
def test_num(number: int):
    print(f"Number: {number}")
    return number


@app.task(name="test_echo", echo=True)
def test_echo(self: SyncTask):
    task = self.add_task(task_name="test_num", args=(5,), timeout=50)
    print(f"Задача {task.task_name}, результат: {task.returning}")
    return


@app.task(retry=5, retry_on_exc=[ZeroDivisionError])
def error_zero():
    result = 1/0
    print(result)


def yield_func(result):
    print(result)
    return result


@app.task(generate_handler=yield_func, echo=True)
def test_yield(self: SyncTask, n: int):
    for _ in range(n):
        n += 1
        yield n


class Item(pydantic.BaseModel):
    name: str
    value: int


@app.task(echo=True, test=True)
def example_pydantic(self: SyncTask, item: Item):
    return f"Hello, {item.name}!"


if __name__ == "__main__":
    app.run_forever()

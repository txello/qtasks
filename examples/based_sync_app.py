import logging
from qtasks import QueueTasks
from qtasks.registries import SyncTask

import shared_tasks

app = QueueTasks()
app.config.logs_default_level = logging.DEBUG
app.config.running_older_tasks = True

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


if __name__ == "__main__":
    app.run_forever()

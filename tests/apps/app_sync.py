"""Sync App."""

from qtasks import QueueTasks
from qtasks.plugins import SyncgRPCPlugin

app = QueueTasks(name="QueueTasks")
app.config.delete_finished_tasks = True

app.add_plugin(SyncgRPCPlugin(app=app, host="localhost"))


@app.task(name="test")
def sample_task(id: int):
    # Логика задачи...
    result = f"Пользователь {id} записан"
    return result


@app.task(name="error_task")
def error_zero():
    result = 1/0
    print(result)


if __name__ == "__main__":
    app.run_forever()

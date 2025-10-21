"""Async App."""

from qtasks.asyncio import QueueTasks


app = QueueTasks(name="QueueTasks")
app.config.delete_finished_tasks = True


@app.task(name="test")
async def sample_task(id: int):
    # Логика задачи...
    result = f"Пользователь {id} записан"
    return result


@app.task(name="error_task")
async def error_zero():
    result = 1/0
    print(result)


if __name__ == "__main__":
    print("[INFO] QTasks Сервер запущен...")
    app.run_forever()

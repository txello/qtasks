from qtasks.asyncio import QueueTasks


app = QueueTasks()
app.config.delete_finished_tasks = True

@app.task
async def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    app.run_forever()

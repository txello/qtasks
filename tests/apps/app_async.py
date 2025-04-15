from qtasks.asyncio import QueueTasks
from qtasks.brokers import AsyncRedisBroker
from qtasks.workers import AsyncWorker

broker = AsyncRedisBroker(name="QueueTasks")
worker = AsyncWorker(name="QueueTasks", broker=broker)

app = QueueTasks(name="QueueTasks", broker=broker, worker=worker)

@app.task(name="test")
async def sample_task(id: int):
    # Логика задачи...
    result = f"Пользователь {id} записан"
    return result

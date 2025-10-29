from qtasks.asyncio import QueueTasks
from qtasks.plugins import AsyncgRPCPlugin

app = QueueTasks()


@app.task
async def test():
    print(123)

@app.task
async def add(x, y):
    return x + y



app.add_plugin(AsyncgRPCPlugin(app=app), trigger_names=["-"])

if __name__ == "__main__":
    app.run_forever()

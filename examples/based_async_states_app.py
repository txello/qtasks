from qtasks.asyncio import QueueTasks
from qtasks.plugins import AsyncState
from qtasks.registries import AsyncTask

app = QueueTasks()


class MyState(AsyncState):
    pass


@app.task
async def step1(state: MyState):
    await state.set("state", "await_phone")
    await state.update(step=1, prompt="Введите телефон")
    return "ok"


@app.task(echo=True)
async def step2(self: AsyncTask, state: MyState):
    print(await state.get_all())

    cur = await state.get("state")
    if cur != "await_phone":
        return "error"
    await state.update(step=2)
    return "ok"


if __name__ == "__main__":
    app.run_forever()

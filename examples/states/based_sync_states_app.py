from qtasks import QueueTasks
from qtasks.plugins import SyncState
from qtasks.registries import AsyncTask

app = QueueTasks()


class MyState(SyncState):
    pass


@app.task
def step1(state: MyState):
    state.set("state", "await_phone")
    state.update(step=1, prompt="Enter your phone number")
    return "ok"


@app.task(echo=True)
def step2(self: AsyncTask, state: MyState):
    print(state.get_all())

    cur = state.get("state")
    if cur != "await_phone":
        return "error"
    state.update(step=2)
    state.delete("state")
    state.clear()
    return "ok"


if __name__ == "__main__":
    app.run_forever()

# Example of variables in task functions

QTasks supports two built-in mechanisms for managing task logic:

* **Depends** — calling external functions, generators, or context managers when
a task is executed.
* **State** — storing and exchanging state between tasks.

---

## 🔧 Example 1: Depends

`Depends` allows you to connect resources that need to be initialized and closed
upon completion.
The function can be simple, generator, or asynchronous context manager.

```python
from qtasks.plugins import Depends
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    db = await connect_to_db()
    yield db
    print("close...")
    await db.disconnect()

@app.task
async def test_depends(depends: Depends(get_db)):
    depends.execute(...)
    print("Call completed")
    return
```

**Console output:**

```bash
<Server starts task>
Call completed
<Server completes task>
close...
```

**Result:** the task uses a database connection that closes automatically.

---

## 🔧 Example 2: State (state between tasks)

`State` is a data store available for sequential steps of a single logic.

```python
from qtasks.plugins import AsyncState

class MyState(AsyncState):
    pass

@app.task
async def step1(state: MyState):
    await state.set("state", "await_phone")
    await state.update(step=1, prompt="Enter phone number")
    return "ok"

@app.task
async def step2(state: MyState):
    print(await state.get_all())

    cur = await state.get("state")
    if cur != "await_phone":
        return "error"
await state.update(step=2)
await state.delete("state")
await state.clear()
return "ok"
```

**Console output:**

```bash
{"state": "await_phone", "step": 1, "prompt": "Enter phone number"}
```

**Result:** the first step wrote the data to the state, the second step read it,
checked it, and cleared it.

---
⚙️ How does this work inside `QTasks`?

## ⚙️ How does it work inside `QTasks`?

* **Depends** is registered when the task is called, and the function inside is
triggered when TaskExecutor is executed. This is useful for connecting to databases,
APIs, or external services.
* **State** is implemented as an asynchronous key-value store. It supports
`set`, `update`, `get`, `delete`, `clear`, as well as reading all data at once (`get_all`).

---

## 🏢 Example of use in a company

Let's say a step-by-step registration form is being implemented:

1. `step1` shows the user a request to enter their phone number.
2. `step2` checks that the phone number has been entered and moves the process forward.

In this case, `Depends` can be used to work with the database connection, and `State`
can be used to store the user's intermediate data.

---

## ✅ Summary

* **Depends** — for connecting dependencies (resources, contexts, services).
* **State** — for step-by-step data storage between tasks.

Together, they allow you to build flexible pipelines: from database integrations
to chatbots
and complex business processes.

# States

The `State` mechanism in QTasks allows you to securely store and transfer data between
tasks.
It is implemented in the built-in worker plugin `(A)StatePlugin` and provides
a convenient interface for working with state.

---

## Example of using State

```python
from qtasks.plugins.states import AsyncState


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

Output of `print(await state.get_all())`:

```python
{'state': 'await_phone', 'step': 1, 'prompt': 'Enter phone number'}
```

Scenario:

* `step1` initializes the state and writes several values.
* `step2` reads the state, checks it, updates it, and clears it.

This way, multiple tasks can work with a shared **thread-safe** state.

---

## How it works "under the hood"

Below is a simplified description of the internal logic of `(A)StatePlugin`.

### 1. Searching for State in task parameters

The plugin analyzes the task signature and checks whether the parameter type is
a subclass of `AsyncState` or `State`:

```python
issubclass(MyState, (AsyncState, State))
```

If such a parameter is found, the task is considered to use state.

### 2. Initializing State and StateRegistry

If `__init__` has not yet been called for `MyState`, the plugin:

* creates an instance of the state class (`MyState()`),
* links it to the internal registry `(A)syncStateRegistry`.

The registry is responsible for storing values "inside" and uses locks:

* `asyncio.Lock()` — for asynchronous tasks,
* `threading.Lock()` — for synchronous tasks.

This ensures that parallel tasks cannot simultaneously modify the same data in an
inconsistent manner.

### 3. Parameter substitution in a task

After initialization, the plugin replaces the task function parameter with the
ready-made `MyState` object.
Inside the task body, the developer already works with a full-fledged state API.

---

## `State` / `AsyncState` API

The main state methods are listed below.

### `get`

```python
value = await state.get("key", default=None)
```

* `key` — state key (if `None`, all values are returned).
* `default` — default value if the key is not found.

### `get_all`

```python
data = await state.get_all()
```

Returns a dictionary of all state values.

### `set`

```python
await state.set("key", value)
```

Sets the state value by key.

### `update`

```python
data = await state.update(step=1, prompt="Enter phone number")
```

Updates multiple values at once and returns the updated dictionary.

### `delete`

```python
await state.delete("key")
```

Deletes the value by key.

### `clear`

```python
await state.clear()
```

Clears all state values.

---

## Purpose of the State mechanism

The `State` mechanism solves the problem of
**thread-safe data transfer between tasks**:

* shared memory for related tasks (script steps, chains, dialogs);
* protection against races during parallel access to the state;
* a unified interface for reading, writing, and clearing data.

This is a convenient tool for building complex step-by-step processes and scenarios
that require context preservation between tasks.

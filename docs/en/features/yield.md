# Tasks with `yield`

In QTasks, a task can return not only a single value via `return`, but also
multiple values via `yield`.
Such a task is considered a **generator**: it sequentially outputs
intermediate results that can be processed and converted.

---

## Example: generator task with `generate_handler`

```python
async def yield_func(result: int) -> int:
    print(result)
    return result + 2


@app.task(
    description="Test task with a generator.",
    generate_handler=yield_func,)

async def test_yield(n: int):
    for _ in range(n):
        n += 1
        yield n
```

Calling the task:

```python
task = await test_yield.add_task(5, timeout=50)
print(task.returning)
# Result: [8, 9, 10, 11, 12]
```

What is happening here:

* The `test_yield` function is an asynchronous generator: it does `yield n` inside
the loop.
* For each value of `n`, `yield_func(result)` is called, and it is the result of
`yield_func` that ends up in the final list.
* When `n = 5`, the loop is executed 5 times, returning
the values `6, 7, 8, 9, 10`,
  and `yield_func` converts them to `8, 9, 10, 11, 12`.

Conclusion: `task.returning` is a list of values returned by `generate_handler`.

---

## How it works "under the hood"

Below is a simplified description of the internal logic without unnecessary details.

1. **Determining that the task is a generator**
   When declaring `@app.task` for a function, an internal task model `TaskExecSchema`
   is created.
   In it, the `generating` flag is set to `True` if the function is a generator:

   ```python
   inspect.isasyncgenfunction(func) or inspect.isgeneratorfunction(func)
   ```

2. **Selecting the execution path in TaskExecutor
   When `(A)syncTaskExecutor` starts executing a task (`execute()`), it checks
   `generating`:

   * if `generating == True` → the internal function `run_task_gen()` is called;
   * otherwise → the usual path `run_task()` is used.

3. **Iteration over generator values**
   Inside `run_task_gen()`, the task is executed as a generator:

   * for `async def`, `async for result in func(...)` is used;
   * for a regular `def`, a `while True` loop with `StopIteration` handling is used.

4. **Processing via `generate_handler`**
   For each `result` received from `yield`, `generate_handler(result)` is called
   (if specified).
   The return values of `generate_handler` are collected in a list.

5. **Final task result**
   By default, `(A)syncTaskExecutor` returns **a list of all results** received
   from the generator:
   either directly from `yield` values,
   or from values converted via `generate_handler`.

   Important: both `TaskExecSchema` and `(A)syncTaskExecutor` can be replaced
   by the user — including at the `@app.task(executor=New)` stage.

Important: both `TaskExecSchema` and `(A)syncTaskExecutor` can be replaced by
the user, including at the `@app.task(executor=NewTaskExecutor)` stage, if a
different way of processing generators is required.

---
When to use tasks with `yield`

## When to use tasks with `yield`

Generator tasks are useful when you need to:

* get a **stream of results** instead of a single value;
* process data in stages (e.g., chunks of files, batches of records);
* log or aggregate intermediate results via `generate_handler`;
* build your own mini-pipelines within a single task.

In other cases, a regular task with `return` is sufficient.

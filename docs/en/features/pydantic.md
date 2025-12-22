# Pydantic

There is a plugin built into Worker called **(A)syncPydanticWrapperPlugin**,
which automatically converts the input parameters of a task into Pydantic models.
It makes working with typed data structures natural and transparent:
the model is assembled right before the task function is called, and the
developer receives a ready-made, validated object.

The plugin works without additional configuration. Any task that accepts a model
parameter will support automatic assembly.

---

## Example of use

```python
import pydantic
from qtasks.asyncio import QueueTasks

app = QueueTasks()

class Item(pydantic.BaseModel):
    name: str
    value: int

@app.task(
    description="Test task using Pydantic.",
    tags=["example"],)

async def example_pydantic(item: Item):
    return f"Hello, {item.name}!"
```

All of the following options will be equivalent — QTasks will correctly assemble
the model:

```python
task = await example_pydantic.add_task("Test", value=42, timeout=50)
task = await example_pydantic.add_task("Test", 42, timeout=50)
task = await example_pydantic.add_task(name="Test", value=42, timeout=50)
```

Each of these will result in the creation of the same model:

```python
Item(name="Test", value=42)
```

---

## Under the hood

The plugin works sequentially.

### 1. Model assembly

The plugin:

1. Analyzes the task signature.
2. Finds parameters that are inheritors of `pydantic.BaseModel`.
3. Extracts suitable `kwargs`.
4. Uses residual positional arguments `args` if necessary.
5. Assembles the model:

```python
model = Item(*args_from_task, **kwargs_from_task)
```

### 2. Cleaning arguments

All parameters used in creating the model are removed from the actual arguments.
The remaining arguments are passed to the task unchanged.

This allows you to flexibly combine the model with other parameters:

```python
@app.task
async def task_with_mix(item: Item, retries: int = 3):
    ...
```

---

## Returning models

If the task returns a `BaseModel` object, QTasks automatically converts
it to a serializable dictionary using:

```python
model.model_dump()
```

Example:

```python
@app.task
async def create_item() -> Item:
    return Item(name="Generated", value=10)
```

Actual result stored in the system:

```json
{"name": "Generated", "value": 10}
```

---

## Features

* Any descendants of `BaseModel` are supported.
* Assembly is performed on the Worker side before calling the user function.
* The plugin does not change the task signature.
* Models can be combined with positional and named arguments.
* Models are automatically serialized as a result of the task.

---

## Summary

(A)syncPydanticWrapperPlugin provides:

* Transparent work with typed structures.
* Automatic validation of incoming data.
* Convenient integration of models into the task signature.
* Standard data return format.

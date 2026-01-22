# Testing

QTasks supports testing tasks and components in both synchronous and
asynchronous modes.
You can use standard Python tools (`unittest`, `pytest`) and asynchronous add-ons
(`pytest-asyncio`), as well as the framework's built-in test cases.

---

## Quick test launch

Minimal example for launching tests directly:

---

## Quick test execution

A minimal example of running tests directly:

```bash
py tests/main.py
```

When using `pytest`:

```bash
pytest -v
```

When using `tox` (for multiple Python versions):

```bash
tox
```

Specific environment:

```bash
tox -e py312
```

---

## Supported frameworks

* ✅ `unittest` — Python's basic standard framework.
* ✅ `pytest` — a flexible and extensible testing system.
* ✅ `pytest-asyncio` — adds support for `async` tests for `pytest`.
* ✅ `SyncTestCase` / `AsyncTestCase` — built-in QTasks cases for fine-tuning
the testing environment.

Asynchronous libraries such as `aiounittest` can be used as desired, but the main
focus of the examples is on `unittest` and `pytest`.

---

## Basic examples

### `unittest` (synchronous)

```python
import unittest
from app import app


class TestTasks(unittest.TestCase):
    def setUp(self):
        # Add a task to the queue
        self._result = app.add_task(“test”, 5)

    def test_task_get_result(self):
        uuid = self._result.uuid
        result = app.get(uuid=uuid)
        self.assertIsNotNone(result)
```

Here, `app.get()` is a public method that proxies the request to the broker and
then to the storage (`app.broker.get()`, `app.broker.storage.get()`).

---

### `unittest` (asynchronously)

```python
import unittest
from app import app


class TestAsyncTasks(unittest.IsolatedAsyncioTestCase):
    async def _add_task(self):
        return await app.add_task(“test”, 5)

    async def test_task_get_result(self):
        task = await self._add_task()
        result = await app.get(uuid=task.uuid)
        self.assertIsNotNone(result)
```

Asynchronous tests use `IsolatedAsyncioTestCase`, available in the standard
Python 3.8+ library.

---

## Built-in QTasks test cases

QTasks provides its own test wrappers `SyncTestCase` and `AsyncTestCase`,
which allow you to:

* replace application components (broker, worker, storage) with test implementations
depending on `TestConfig`;
* run tasks without a separate server;
* test logic with different environment configurations.

For more information about `TestConfig`, see: [API/Schemas/TestConfig](api/schemas/test_config.md).

### `SyncTestCase`

```python
import unittest

from qtasks.tests import SyncTestCase
from qtasks.schemas.test import TestConfig
from app import app


class TestTasks(unittest.TestCase):
    def setUp(self):
        self.case = SyncTestCase(app=app)
        # Enable full test config
        self.case.settings(TestConfig.full())

    def test_task_add(self):
        task = self.case.add_task(“test”, 5)
        self.assertIsNotNone(task)
```

### `AsyncTestCase`

```python
import unittest

from qtasks.tests import AsyncTestCase
from qtasks.schemas.test import TestConfig
from app import app


class TestAsyncQTasks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.case = AsyncTestCase(app=app)
        self.case.settings(TestConfig.full())

    async def _add_task(self):
        return await self.case.add_task(“test”, 5, timeout=10)

    async def test_add_task(self):
        task = await self._add_task()
        self.assertIsNotNone(task)
```

Depending on the `TestConfig` settings, application components can be replaced
with test (empty) classes, which allows you to isolate the logic being tested.

---

## Example with `pytest` and `pytest-asyncio`

### Installation

```bash
pip install pytest pytest-asyncio
```

### Example of the `tests/test_async_task.py` file

```python
import pytest
from uuid import uuid4

from qtasks.tests import AsyncTestCase
from qtasks.schemas.test import TestConfig
from qtasks.enums.task_status import TaskStatusEnum

from tests.apps.app_async import app

@pytest.fixture()
def test_case():
    case = AsyncTestCase(app=app)
    case.settings(TestConfig.full())
    return case

@pytest.mark.asyncio
async def test_task_get_result(test_case):
    task = await test_case.add_task(“test”, 5)
    result = await app.get(uuid=task.uuid)
    assert result is not None

@pytest.mark.asyncio
async def test_task_returns_expected_result(test_case):
    task = await test_case.add_task(“test”, 5, timeout=10)
    # Check that the task returned the expected value
    assert task.returning is not None

@pytest.mark.asyncio
async def test_task_error_handling(test_case):
    task = await test_case.add_task(“error_task”, timeout=10)
    assert task.status == TaskStatusEnum.ERROR.value

@pytest.mark.asyncio
async def test_task_not_found():
    # UUID missing from storage
    result = await app.get(uuid=str(uuid4()))
    assert result is None
```

### Running tests

```bash
pytest tests/test_async_task.py -v
```

---

These examples demonstrate the basic approach to testing tasks, configurations,
and errors in QTasks.
More advanced scenarios (testing plugins, middleware, task chains, etc.)
are described in specialized sections of the documentation.

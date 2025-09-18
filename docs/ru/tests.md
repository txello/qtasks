# Тестирование

`QTasks` поддерживает тестирование задач как в синхронном, так и в асинхронном режиме.
Вы можете использовать стандартные инструменты Python, такие как `unittest`, а
также асинхронные библиотеки — например, `aiounittest` и `pytest-asyncio`.

## Быстрый запуск тестов из консоли

```bash
py tests/main.py
```

## Поддерживаемые фреймворки

* ✅ `unittest` — для синхронных задач и базовой структуры.
* ✅ `aiounittest` — для асинхронных задач и компонентов.
* ✅ `pytest` + `pytest-asyncio` — для гибкого и мощного асинхронного тестирования.
* ✅ `SyncTestCase`/`AsyncTestCase` — внутренние кейсы QTasks для точного управления
задачами.

---

## Примеры

### `unittest` (синхронно)

```python
import unittest
from app import app

class TestTasks(unittest.TestCase):
    def setUp(self):
        self._result = app.add_task(task_name="test", 5)

    def test_task_get_result(self):
        uuid = self._result.uuid
        result = app.get(uuid=uuid)
        self.assertIsNotNone(result)
```

### `unittest` (асинхронно)

```python
import unittest

from qtasks.schemas.task import Task
from app import app

class TestAsyncTasks(unittest.IsolatedAsyncioTestCase):
    async def _add_task(self) -> Task | None:
        return await app.add_task(task_name="test", 5)

    async def test_task_get_result(self):
        uuid = (await self._add_task()).uuid
        result = await app.get(uuid=uuid)
        self.assertIsNotNone(result)
```

### `SyncTestCase` / `AsyncTestCase`

```python
import unittest

from qtasks.tests import SyncTestCase
from qtasks.schemas.test import TestConfig
from app import app

class TestTasks(unittest.TestCase):
    def setUp(self):
        self.test_case = SyncTestCase(app=app)

    def test_task_add(self):
        self.test_case.settings(TestConfig.full())
        result = self.test_case.add_task(task_name="test", 5)
        self.assertIsNotNone(result)
```

```python
import unittest

from qtasks.tests import AsyncTestCase
from qtasks.schemas.test import TestConfig
from qtasks.schemas.task import Task
from app import app

class TestAsyncQTasks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_case = AsyncTestCase(app=app)

    async def _add_task(self) -> Task | None:
        return await self.test_case.add_task("test", args=(5,), timeout=10)

    async def test_add_task(self):
        self.test_case.settings(TestConfig.full())
        result = await self._add_task()
        self.assertIsNotNone(result)
```

### `pytest`

#### Установка

```bash
pip install pytest pytest-asyncio
```

#### `tests/test_async_task.py`

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
    task = await test_case.add_task("test", args=(5,))
    result = await app.get(uuid=task.uuid)
    assert result is not None

@pytest.mark.asyncio
async def test_task_returns_expected_result(test_case):
    task = await test_case.add_task("test", args=(5,), timeout=10)
    assert task.returning == "Пользователь 5 записан"

@pytest.mark.asyncio
async def test_task_error_handling(test_case):
    task = await test_case.add_task("error_task", timeout=10)
    assert task.status == TaskStatusEnum.ERROR.value

@pytest.mark.asyncio
async def test_task_not_found():
    result = await app.get(uuid=str(uuid4()))
    assert result is None
```

#### Запуск

```bash
pytest tests/test_async_task.py -v
```

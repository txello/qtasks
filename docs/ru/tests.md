# Тестирование
QueueTasks поддерживает тестирование задач как в синхронном, так и в асинхронном режиме. Вы можете использовать стандартные инструменты Python, такие как unittest, а также асинхронные библиотеки — например, aiounittest.

## Быстрый запуск тестов из консоли
```bash
py tests/main.py
```

## Поддерживаемые фреймворки
* ✅ unittest — для синхронных задач и базовой структуры тестов.
* ✅ aiounittest — для асинхронных задач и компонентов.
* ✅ `SyncTestCase`/`AsyncTestCase` — внутренний кейс тестирования.

## Пример теста с unittest
```py
import unittest
from app import app

class TestTasks(unittest.TestCase):
    def setUp(self):
        self._result = app.add_task("test", args=(5,))

    def test_task_get_result(self):
        uuid = self._result.uuid
        result = app.get(uuid=uuid)
        self.assertIsNotNone(result)
```
## Пример теста с aiounittest
```py
import aiounittest
from app import app

class TestAsyncTasks(aiounittest.AsyncTestCase):
    async def _add_task(self) -> Task|None:
        return await app.add_task("test", args=(5,))
    
    async def test_task_get_result(self):
        uuid = (await self._add_task()).uuid
        result = await app.get(uuid=uuid)
        self.assertIsNotNone(result)
```

## TestCase

### Пример теста с unittest
```py
import unittest
from app import app


class TestTasks(unittest.TestCase):
    def setUp(self):
        self.test_case = tests.SyncTestCase(app=app)
    
    def test_task_add(self):
        self.test_case.settings(TestConfig.full())
        result = self.test_case.add_task("test", args=(5,))
        self.assertIsNotNone(result)
```

### Пример теста с aiounittest
```py
import aiounittest
from app import app

class TestAsyncQTasks(aiounittest.AsyncTestCase):
    def setUp(self):
        self.test_case = tests.AsyncTestCase(app=app)
    
    async def _add_task(self) -> Task|None:
        return await self.test_case.add_task("test", args=(5,))
    
    async def test_add_task(self):
        self.test_case.settings(TestConfig.full())
        
        result = await self._add_task()
        self.assertIsNotNone(result)
```

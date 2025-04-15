# Тестирование
QueueTasks поддерживает тестирование задач как в синхронном, так и в асинхронном режиме. Вы можете использовать стандартные инструменты Python, такие как unittest, а также асинхронные библиотеки — например, aiounittest.

## Быстрый запуск тестов из консоли
```bash
py tests/main.py
```

## Поддерживаемые фреймворки
* ✅ unittest — для синхронных задач и базовой структуры тестов.
* ✅ aiounittest — для асинхронных задач и компонентов.

## Пример теста с unittest
```py
import unittest
from app import app

class TestTasks(unittest.TestCase):
    def test_task_get_result(self):
        uuid = self._result.uuid
        result = app.get(uuid=uuid)
        self.assertIsNotNone(result)

if __name__ == "__main__":
    unittest.main()
```
## Пример теста с aiounittest
```py
import aiounittest
from app import app

class TestAsyncTasks(aiounittest.AsyncTestCase):
    async def test_task_get_result(self):
        uuid = (await self._add_task()).uuid
        result = await app.get(uuid=uuid)
        self.assertIsNotNone(result)

if __name__ == "__main__":
    aiounittest.main()
```
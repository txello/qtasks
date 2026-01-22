# Тестирование

QTasks поддерживает тестирование задач и компонентов как в синхронном, так и в
асинхронном режиме.
Вы можете использовать стандартные инструменты Python (`unittest`, `pytest`) и
асинхронные надстройки (`pytest-asyncio`), а также встроенные тестовые кейсы фреймворка.

---

## Быстрый запуск тестов

Минимальный пример запуска тестов напрямую:

```bash
py tests/main.py
```

При использовании `pytest`:

```bash
pytest -v
```

При использовании `tox` (для нескольких версий Python):

```bash
tox
```

Конкретное окружение:

```bash
tox -e py312
```

---

## Поддерживаемые фреймворки

* ✅ `unittest` — базовый стандартный фреймворк Python.
* ✅ `pytest` — гибкая и расширяемая система тестирования.
* ✅ `pytest-asyncio` — добавляет поддержку `async`-тестов для `pytest`.
* ✅ `SyncTestCase` / `AsyncTestCase` — встроенные кейсы QTasks для тонкой настройки
среды тестирования.

Асинхронные библиотеки вроде `aiounittest` можно использовать по желанию, но основной
фокус примеров сделан на `unittest` и `pytest`.

---

## Базовые примеры

### `unittest` (синхронно)

```python
import unittest
from app import app


class TestTasks(unittest.TestCase):
    def setUp(self):
        # Добавляем задачу в очередь
        self._result = app.add_task("test", 5)

    def test_task_get_result(self):
        uuid = self._result.uuid
        result = app.get(uuid=uuid)
        self.assertIsNotNone(result)
```

Здесь `app.get()` — публичный метод, который проксирует запрос к брокеру и далее
к хранилищу (`app.broker.get()`, `app.broker.storage.get()`).

---

### `unittest` (асинхронно)

```python
import unittest
from app import app


class TestAsyncTasks(unittest.IsolatedAsyncioTestCase):
    async def _add_task(self):
        return await app.add_task("test", 5)

    async def test_task_get_result(self):
        task = await self._add_task()
        result = await app.get(uuid=task.uuid)
        self.assertIsNotNone(result)
```

В асинхронных тестах используется `IsolatedAsyncioTestCase`, доступный в стандартной
библиотеке Python 3.8+.

---

## Встроенные тестовые кейсы QTasks

QTasks предоставляет собственные тестовые обёртки `SyncTestCase` и `AsyncTestCase`,
которые позволяют:

* подменять компоненты приложения (broker, worker, storage) на тестовые реализации
в зависимости от `TestConfig`;
* запускать задачи без отдельного сервера;
* тестировать логику с разной конфигурацией среды.

Подробнее о `TestConfig` см. в разделе: [API/Схемы/TestConfig](api/schemas/test_config.md).

### `SyncTestCase`

```python
import unittest

from qtasks.tests import SyncTestCase
from qtasks.schemas.test import TestConfig
from app import app


class TestTasks(unittest.TestCase):
    def setUp(self):
        self.case = SyncTestCase(app=app)
        # Включаем полный тестовый конфиг
        self.case.settings(TestConfig.full())

    def test_task_add(self):
        task = self.case.add_task("test", 5)
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
        return await self.case.add_task("test", 5, timeout=10)

    async def test_add_task(self):
        task = await self._add_task()
        self.assertIsNotNone(task)
```

В зависимости от настроек `TestConfig` компоненты приложения могут быть подменены
на тестовые (пустые) классы, что позволяет изолировать тестируемую логику.

---

## Пример с `pytest` и `pytest-asyncio`

### Установка

```bash
pip install pytest pytest-asyncio
```

### Пример файла `tests/test_async_task.py`

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
    task = await test_case.add_task("test", 5)
    result = await app.get(uuid=task.uuid)
    assert result is not None


@pytest.mark.asyncio
async def test_task_returns_expected_result(test_case):
    task = await test_case.add_task("test", 5, timeout=10)
    # Проверяем, что задача вернула ожидаемое значение
    assert task.returning is not None


@pytest.mark.asyncio
async def test_task_error_handling(test_case):
    task = await test_case.add_task("error_task", timeout=10)
    assert task.status == TaskStatusEnum.ERROR.value


@pytest.mark.asyncio
async def test_task_not_found():
    # UUID, отсутствующий в хранилище
    result = await app.get(uuid=str(uuid4()))
    assert result is None
```

### Запуск тестов

```bash
pytest tests/test_async_task.py -v
```

---

Эти примеры демонстрируют базовый подход к тестированию задач, конфигурации и
ошибок в QTasks.
Более продвинутые сценарии (тестирование плагинов, middleware, цепочек задач и т.п.)
описываются в специализированных разделах документации.

"""Async Task Tests."""

import time
import pytest
import sys
import subprocess
from pathlib import Path
from uuid import uuid4

from qtasks import tests
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.schemas.test import TestConfig

from apps.app_async import app


@pytest.fixture(scope="session", autouse=True)
def run_server():
    """Запуск QTasks-сервера через subprocess и лог ошибок."""
    script_path = Path(__file__).parent / "apps" / "app_async.py"
    assert script_path.exists(), f"Script not found: {script_path}"

    process = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    time.sleep(1)

    # Выводим stdout (если вдруг сразу завершилось)
    if process.poll() is not None:
        output = process.stdout.read()
        raise RuntimeError(f"Server exited early with output:\n{output}")

    yield

    time.sleep(2)
    process.terminate()
    process.wait()


@pytest.fixture()
def test_case():
    """Создаёт конфигурацию тестов."""
    case = tests.AsyncTestCase(app=app)
    case.settings(TestConfig.full())
    return case


@pytest.mark.asyncio
async def test_task_get_result(test_case):
    """Получение результата задачи."""
    task = await test_case.add_task("test", args=(5,))
    result = await app.get(uuid=task.uuid)
    assert result is not None


@pytest.mark.asyncio
async def test_task_get_wait(test_case):
    """Ожидание завершения задачи."""
    result = await test_case.add_task("test", args=(5,), timeout=50)
    assert result.status == TaskStatusEnum.SUCCESS.value


@pytest.mark.asyncio
async def test_task_error_get_wait(test_case):
    """Ожидание завершения задачи с ошибкой."""
    result = await test_case.add_task("error_task", timeout=50)
    assert result.status == TaskStatusEnum.ERROR.value


@pytest.mark.asyncio
async def test_task_returns_expected_result(test_case):
    """Проверка ожидаемого результата задачи."""
    result = await test_case.add_task("test", args=(5,), timeout=50)
    assert result.returning == "Пользователь 5 записан"


@pytest.mark.asyncio
async def test_task_not_found():
    """Проверка отсутствия задачи."""
    fake_uuid = str(uuid4())
    result = await app.get(uuid=fake_uuid)
    assert result is None


@pytest.mark.asyncio
async def test_task_timeout(test_case):
    """Проверка истечения времени ожидания задачи."""
    result = await test_case.add_task("test", args=(5,), timeout=0.1)
    assert result is None

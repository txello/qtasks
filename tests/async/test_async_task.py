"""Async Task Tests."""

import os
import sys
from uuid import uuid4

import pytest

from qtasks.enums.task_status import TaskStatusEnum
from qtasks.schemas.test import TestConfig
from qtasks.tests import AsyncTestCase

parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, parent_dir)

from apps.app_async import app


@pytest.fixture(scope="package")
def app_script() -> str:
    return "app_async.py"


@pytest.fixture()
def test_case():
    """Создаёт конфигурацию тестов."""
    case = AsyncTestCase(app=app)
    case.settings(TestConfig.full())
    return case


@pytest.mark.asyncio
async def test_task_get_result(test_case):
    """Получение результата задачи."""
    task = await test_case.add_task("test", 5)
    result = await app.get(uuid=task.uuid)
    assert result is not None


@pytest.mark.asyncio
async def test_task_get_wait(test_case):
    """Ожидание завершения задачи."""
    result = await test_case.add_task("test", 5, timeout=500)
    assert result.status == TaskStatusEnum.SUCCESS.value


@pytest.mark.asyncio
async def test_task_error_get_wait(test_case):
    """Ожидание завершения задачи с ошибкой."""
    result = await test_case.add_task("error_task", timeout=500)
    assert result.status == TaskStatusEnum.ERROR.value


@pytest.mark.asyncio
async def test_task_returns_expected_result(test_case):
    """Проверка ожидаемого результата задачи."""
    result = await test_case.add_task("test", 5, timeout=500)
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
    result = await test_case.add_task("test", 5, timeout=0.1)
    assert result is None

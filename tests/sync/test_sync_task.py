"""Sync Task Tests."""

import os
import sys
import pytest
from uuid import uuid4

from qtasks.tests import SyncTestCase
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.schemas.test import TestConfig

parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, parent_dir)

from apps.app_sync import app

@pytest.fixture(scope="package")
def app_script() -> str:
    return "app_sync.py"


@pytest.fixture()
def test_case():
    """Создаёт конфигурацию тестов."""
    case = SyncTestCase(app=app)
    case.settings(TestConfig.full())
    return case


@pytest.mark.sync
def test_task_get_result(test_case):
    """Получение результата задачи."""
    task = test_case.add_task("test", 5)
    result = app.get(uuid=task.uuid)
    assert result is not None


@pytest.mark.sync
def test_task_get_wait(test_case):
    """Ожидание завершения задачи."""
    result = test_case.add_task("test", 5, timeout=500)
    assert result.status == TaskStatusEnum.SUCCESS.value


@pytest.mark.sync
def test_task_error_get_wait(test_case):
    """Ожидание завершения задачи с ошибкой."""
    result = test_case.add_task("error_task", timeout=500)
    assert result.status == TaskStatusEnum.ERROR.value


@pytest.mark.sync
def test_task_returns_expected_result(test_case):
    """Проверка ожидаемого результата задачи."""
    result = test_case.add_task("test", 5, timeout=500)
    assert result.returning == "Пользователь 5 записан"


@pytest.mark.sync
def test_task_not_found():
    """Проверка отсутствия задачи."""
    fake_uuid = str(uuid4())
    result = app.get(uuid=fake_uuid)
    assert result is None


@pytest.mark.sync
def test_task_timeout(test_case):
    """Проверка истечения времени ожидания задачи."""
    result = test_case.add_task("test", 5, timeout=0.1)
    assert result is None

"""Sync Task Tests."""

import time
import unittest
import multiprocessing
from uuid import uuid4

from qtasks import tests
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.schemas.task import Task
from qtasks.schemas.test import TestConfig

from apps.app_sync import app


def run_server():
    """Запуск сервера."""
    app.run_forever()


class TestSyncQTasks(unittest.TestCase):
    """Тесты для синхронных задач QTasks."""

    @classmethod
    def setUpClass(cls):
        """Запуск сервера."""
        cls.server_process = multiprocessing.Process(target=run_server)
        cls.server_process.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        """Остановка сервера."""
        time.sleep(2)
        cls.server_process.terminate()
        cls.server_process.join()
        pass

    def setUp(self):
        """Настройка теста."""
        self.test_case = tests.SyncTestCase(app=app)
        self.test_case.settings(TestConfig.full())

    def _add_task(self, timeout: float | None = None) -> Task | None:
        """Добавление задачи."""
        return self.test_case.add_task("test", args=(5,), timeout=timeout)

    def _add_error_task(self, timeout: float | None = None) -> Task | None:
        """Добавление задачи с ошибкой."""
        return self.test_case.add_task("error_task", timeout=timeout)

    def test_task_get_result(self):
        """Получение результата задачи."""
        uuid = self._add_task().uuid
        result = app.get(uuid=uuid)
        self.assertIsNotNone(result)

    def test_task_get_wait(self):
        """Ожидание завершения задачи."""
        result = self._add_task(timeout=50)
        self.assertEqual(result.status, TaskStatusEnum.SUCCESS.value)

    def test_task_error_get_wait(self):
        """Ожидание завершения задачи с ошибкой."""
        result = self._add_error_task(timeout=50)
        self.assertEqual(result.status, TaskStatusEnum.ERROR.value)

    def test_task_returns_expected_result(self):
        """Проверка ожидаемого результата задачи."""
        result = self._add_task(timeout=50)
        self.assertEqual(result.returning, "Пользователь 5 записан")

    def test_task_not_found(self):
        """Проверка отсутствия задачи."""
        fake_uuid = str(uuid4())
        result = app.get(uuid=fake_uuid)
        self.assertIsNone(result)

    def test_task_timeout(self):
        """Проверка истечения времени ожидания задачи."""
        task = self._add_task(timeout=0.1)
        self.assertIsNone(task, "Истекло время ожидания задачи (None)")

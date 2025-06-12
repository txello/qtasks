import multiprocessing
import time
import unittest
from uuid import uuid4

from qtasks import tests
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.schemas.task import Task
from qtasks.schemas.test import TestConfig

from apps.app_async import app

def run_server():
    app.run_forever()

class TestAsyncQTasks(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_process = multiprocessing.Process(target=run_server)
        cls.server_process.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        time.sleep(2)
        cls.server_process.terminate()
        cls.server_process.join()
        pass
    
    def setUp(self):
        self.test_case = tests.AsyncTestCase(app=app)
        self.test_case.settings(TestConfig.full())

    async def _add_task(self, timeout: float|None = None) -> Task|None:
        return await self.test_case.add_task("test", args=(5,), timeout=timeout)
    
    async def _add_error_task(self, timeout: float = None) -> Task|None:
        return await self.test_case.add_task("error_task", timeout=timeout)
    
    async def test_task_get_result(self):
        uuid = (await self._add_task()).uuid
        result = app.get(uuid=uuid)
        self.assertIsNotNone(result)
    
    async def test_task_get_wait(self):
        result = await self._add_task(timeout=50)
        self.assertEqual(result.status, TaskStatusEnum.SUCCESS.value)
    
    async def test_task_error_get_wait(self):
        result = await self._add_error_task(timeout=50)
        self.assertEqual(result.status, TaskStatusEnum.ERROR.value)
    
    async def test_task_returns_expected_result(self):
        result = await self._add_task(timeout=50)
        self.assertEqual(result.returning, "Пользователь 5 записан")

    async def test_task_not_found(self):
        fake_uuid = str(uuid4())
        result = await app.get(uuid=fake_uuid)
        self.assertIsNone(result)

    async def test_task_timeout(self):
        task = await self._add_task(timeout=0.1)
        self.assertIsNone(task, "Истекло время ожидания задачи (None)")

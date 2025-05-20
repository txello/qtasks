import unittest

from qtasks import tests
from qtasks.enums.task_status import TaskStatusEnum
from qtasks.schemas.task import Task
from qtasks.schemas.test import TestConfig

from apps.app_async import app

class TestAsyncQTasks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_case = tests.AsyncTestCase(app=app)

    
    async def _add_task(self, timeout: float|None = None) -> Task|None:
        return await self.test_case.add_task("test", args=(5,), timeout=timeout)
    
    async def test_add_task(self):
        self.test_case.settings(TestConfig.full())
        
        result = await self._add_task()
        self.assertIsNotNone(result)
        return result
    
    async def test_add_task_and_get_result(self):
        self.test_case.settings(TestConfig.full())
        
        task = await self._add_task(timeout=50)
        self.assertIsNotNone(task)
        self.assertEqual(task.status, TaskStatusEnum.SUCCESS.value)
    
    async def test_task_get_none(self):
        self.test_case.settings(TestConfig.full_broker())
        
        uuid = "9c467627-3188-4e7a-ba88-1fec628da70e"
        result = await self.test_case.get(uuid=uuid)
        self.assertIsNone(result)
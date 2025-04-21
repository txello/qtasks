import aiounittest

from apps.app_async import app
from qtasks import tests
from qtasks.schemas.task import Task
from qtasks.schemas.test import TestConfig


class TestAsyncQTasks(aiounittest.AsyncTestCase):
    def setUp(self):
        self.test_case = tests.AsyncTestCase(app=app)

    
    async def _add_task(self) -> Task|None:
        return await self.test_case.add_task("test", args=(5,))
    
    async def test_add_task(self):
        self.test_case.settings(TestConfig.full())
        
        result = await self._add_task()
        self.assertIsNotNone(result)
        return result
    
    async def test_add_task_and_get_result(self):
        self.test_case.settings(TestConfig.full())
        
        uuid = (await self._add_task()).uuid
        result = await self.test_case.get(uuid=uuid)
        self.assertIsNotNone(result)
    
    async def test_task_get_none(self):
        self.test_case.settings(TestConfig.full_broker())
        
        uuid = "9c467627-3188-4e7a-ba88-1fec628da70e"
        result = await self.test_case.get(uuid=uuid)
        self.assertIsNone(result)
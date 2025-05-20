import unittest

from qtasks.schemas.task import Task

from app import app

class TestAsyncTasks(unittest.IsolatedAsyncioTestCase):
    async def _add_task(self) -> Task|None:
        return await app.add_task("test", args=(5,))
    
    async def test_task_get_result(self):
        uuid = (await self._add_task()).uuid
        result = await app.get(uuid=uuid)
        self.assertIsNotNone(result)

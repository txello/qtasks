import aiounittest

from apps.app_async import app


class TestAsyncQTasks(aiounittest.AsyncTestCase):
    async def _add_task(self):
        return await app.add_task("test", args=(5,))
    
    async def test_task_add(self):
        result = self._add_task()
        self.assertIsNotNone(result)
        return result
    
    async def test_task_get_result(self):
        uuid = (await self._add_task()).uuid
        result = await app.get(uuid=uuid)
        self.assertIsNotNone(result)
    
    async def test_task_get_none(self):
        uuid = "00e55799-058e-4b6d-bdb1-3d2b31c3b95d"
        result = await app.get(uuid=uuid)
        self.assertIsNone(result)
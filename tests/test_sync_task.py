import unittest

from apps.app_sync import app


class TestSyncQTasks(unittest.TestCase):
    def setUp(self):
        self._result = app.add_task("test", args=(5,))
    
    def test_task_add(self):
        self.assertIsNotNone(self._result)
    
    def test_task_get_result(self):
        uuid = self._result.uuid
        result = app.get(uuid=uuid)
        self.assertIsNotNone(result)
    
    def test_task_get_none(self):
        uuid = "00e55799-058e-4b6d-bdb1-3d2b31c3b95d"
        result = app.get(uuid=uuid)
        self.assertIsNone(result)
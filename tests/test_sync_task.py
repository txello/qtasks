import unittest

from apps.app_sync import app
from qtasks import tests
from qtasks.schemas.test import TestConfig


class TestSyncQTasks(unittest.TestCase):
    def setUp(self):
        self.test_case = tests.SyncTestCase(app=app)
        self.test_case.settings(TestConfig.full())
        
        self._result = self.test_case.add_task("test", args=(5,))
    
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

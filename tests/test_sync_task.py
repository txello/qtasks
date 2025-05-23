import unittest

from qtasks.schemas.task import Task

from apps.app_sync import app

class TestSyncQTasks(unittest.TestCase):
    def _add_task(self) -> Task|None:
        return app.add_task("test", args=(5,))
    
    def test_task_get_result(self):
        uuid = self._add_task().uuid
        result = app.get(uuid=uuid)
        self.assertIsNotNone(result)

import unittest
import aiounittest

from test_async_task import TestAsyncQTasks
from test_sync_task import TestSyncQTasks

if __name__ == "__main__":
    # Запуск синхронных тестов
    print("[INFO] Запуск синхронных тестов...")
    unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestSyncQTasks))

    # Запуск асинхронных тестов
    print("[INFO] Запуск асинхронных тестов...")
    aiounittest.run_sync(unittest.TestLoader().loadTestsFromTestCase(TestAsyncQTasks))
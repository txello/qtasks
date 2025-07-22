"""App for load testing."""

import time

from qtasks.asyncio import QueueTasks


app = QueueTasks()


@app.task(
    description="Задача для тестирования нагрузки."
)
def load_test_job(num: int):
    """Задача для тестирования нагрузки."""
    end_time = time.time()
    print(f"Job {num} finished at {end_time}")
    return num

from http_plugin import AsyncWebAppPlugin
app.add_plugin(AsyncWebAppPlugin(app=app), trigger_names=["-"])

if __name__ == "__main__":
    app.run_forever(num_workers=20)

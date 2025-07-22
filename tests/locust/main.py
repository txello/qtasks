"""Locust load test for QTasks."""

from locust import HttpUser, task, between


class QTasksUser(HttpUser):
    """User for testing QTasks."""

    wait_time = between(0.01, 0.1)

    @task
    def call_qtasks_task(self):
        self.client.post("/run-task", json={
            "name": "load_test_job",
            "args": [5],
            "timeout": 50,
        })

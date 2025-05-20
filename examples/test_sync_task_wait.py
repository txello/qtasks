from based_sync_app import shared_tasks
task = shared_tasks.sync_test.add_task(timeout=50)
print(task)
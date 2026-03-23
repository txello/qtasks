from based_sync_states_app import step1, step2

step1.add_task(timeout=50)
task = step2.add_task(timeout=50)
print(task)

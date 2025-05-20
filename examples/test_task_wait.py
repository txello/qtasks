from qtasks.results import SyncResult
from based_sync_app import test_num

task = test_num.add_task(args=(1, ))
task = SyncResult(uuid=task.uuid).result()
print(task)
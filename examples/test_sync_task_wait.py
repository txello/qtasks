from based_sync_app import test_num, error_zero, test_yield

#task = test_num.add_task(args=(5,),timeout=50)
#task = error_zero.add_task(timeout=50)
task = test_yield.add_task(args=(5,),timeout=50)
print(task)

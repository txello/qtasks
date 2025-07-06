from based_sync_app import example_pydantic, test_num, error_zero, test_yield

# task = test_num.add_task(args=(5,),timeout=50)
# task = error_zero.add_task(timeout=50)
# task = test_yield.add_task(args=(5,),timeout=50)
task = example_pydantic.add_task(args=("Test", 42), timeout=50)
# task = example_pydantic.add_task(kwargs={"item": {"name": "Test", "value": 42}}, timeout=50)
# task = example_pydantic.add_task(kwargs={"name": "Test", "value": 42}, timeout=50)
print(task)

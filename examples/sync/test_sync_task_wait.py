from based_sync_app import (
    app,
    error_zero,
    example_error_timeout,
    example_pydantic,
    test_num,
    test_yield,
)

# task = test_num.add_task(args=(5,),timeout=50)
# task = error_zero.add_task(timeout=50)
# task = test_yield.add_task(args=(5,),timeout=50)
# task = example_pydantic.add_task(args=("Test", 42), timeout=50)
# task = example_pydantic.add_task(kwargs={"item": {"name": "Test", "value": 42}}, timeout=50)
# task = example_pydantic.add_task(kwargs={"name": "Test", "value": 42}, timeout=50)
# task = example_error_timeout.add_task(timeout=50)
task = app.add_task("test_num", 5, timeout=50)

print(task)

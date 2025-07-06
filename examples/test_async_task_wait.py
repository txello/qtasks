import asyncio

from based_async_app import test_num, error_zero, test_yield, router_tasks, test_echo, test_retry


async def main():
    # task = await test_num.add_task(args=(5,),timeout=50)
    # task = await error_zero.add_task(timeout=50)
    # task = await test_yield.add_task(args=(5,), timeout=50)
    # task = router_tasks.router_test.add_task(timeout=50)
    # task = await test_echo.add_task(timeout=50)
    # task = await test_pydantic.add_task(kwargs={"name": "Test"}, timeout=50)
    task = await test_retry.add_task(timeout=50)
    print(task)

asyncio.run(main())

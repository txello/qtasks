import asyncio

from based_async_app import (
    app,
    error_zero,
    example_error_timeout,
    example_pydantic,
    example_stats,
    router_tasks,
    test_echo,
    test_echo_ctx,
    test_num,
    test_retry,
    test_yield,
)


async def main():
    # task = await test_num.add_task(args=(5,),timeout=50)
    # task = await error_zero.add_task(timeout=50)
    # task = await test_yield.add_task(args=(5,), timeout=50)
    # task = router_tasks.router_test.add_task(timeout=50)
    # task = await test_echo.add_task(timeout=50)
    # task = await test_pydantic.add_task(kwargs={"name": "Test"}, timeout=50)
    # task = await test_retry.add_task(timeout=50)
    task = await example_pydantic.add_task("Test", value=42, timeout=50)
    # task = await example_pydantic.add_task("Test", 42, timeout=50)
    # task = await example_pydantic.add_task(name="Test", value=42, timeout=50)
    # task = await test_echo_ctx.add_task(timeout=50)
    # task = await example_stats.add_task(timeout=50)
    # task = await example_error_timeout.add_task(timeout=50)
    # task = await test_num.add_task(5, timeout=50)
    print(task)

asyncio.run(main())

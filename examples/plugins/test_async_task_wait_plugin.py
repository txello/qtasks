import asyncio

from based_async_plugins_app import test_task


async def main():
    task = await test_task.add_task(timeout=50)
    print(task)

asyncio.run(main())

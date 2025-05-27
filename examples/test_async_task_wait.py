import asyncio

import based_async_app
from based_async_app import shared_tasks

async def main():
    task = await shared_tasks.async_test.add_task(timeout=50)
    print(task)

asyncio.run(main())
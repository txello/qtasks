import asyncio
from based_async_depends import test, close_worker


async def main():
    tasks = [test.add_task() for _ in range(500)]
    await asyncio.gather(*tasks)
    await asyncio.sleep(1)

    # await close_worker.add_task()

asyncio.run(main())

import asyncio
from based_async_depends import test


async def main():
    tasks = [test.add_task() for _ in range(500)]
    await asyncio.gather(*tasks)
    await asyncio.sleep(1)


asyncio.run(main())

import asyncio

from based_async_app import test_num

async def main():
    task = await test_num.add_task(args=(1, ), timeout=50)
    print(task)

asyncio.run(main())
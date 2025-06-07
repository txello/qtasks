import asyncio

from based_async_app import error_zero

async def main():
    task = await error_zero.add_task(timeout=50)
    print(task)

asyncio.run(main())
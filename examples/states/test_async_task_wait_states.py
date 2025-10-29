import asyncio

from based_async_states_app import step1, step2


async def main():
    await step1.add_task(timeout=50)
    task = await step2.add_task(timeout=50)
    print(task)

asyncio.run(main())

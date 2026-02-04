import asyncio
from based_async_app_cls import add
from qtasks.utils.tasks.async_task_utils import AsyncTaskUtils


async def main():
    task_cls_list = [
        add(2, 2),
        add(4),
        add(8)
    ]
    print(task_cls_list)

    chain = AsyncTaskUtils.chain(*task_cls_list)
    print(await chain.get(timeout=100)) # Default: 50


asyncio.run(main())

import asyncio
from based_async_app_cls import add


async def main():
    task_cls_list = [
        add(2, 3, timeout=50),
        add(3, 4, timeout=50),
        add(4, 5, timeout=50),
        add(6, 7, timeout=50)
    ]
    print(task_cls_list)
    tasks = await asyncio.gather(*map(lambda cls: cls.add_task(), task_cls_list))
    print(tasks)


asyncio.run(main())

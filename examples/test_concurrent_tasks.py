import asyncio
import time
from based_async_app import test_num

async def main(num):
    async def run_single_task(i):
        try:
            result = await test_num.add_task(args=(i, i+1), timeout=1000)
            return result
        except asyncio.TimeoutError:
            return f"Истекло время ожидания задачи {i}"

    tasks = [run_single_task(i) for i in range(num)]

    start = time.perf_counter()
    await asyncio.gather(*tasks)
    duration = time.perf_counter() - start
    print(f"Выполнено {num} задач за {duration:.2f} секунд")

if __name__ == "__main__":
    asyncio.run(main(10))

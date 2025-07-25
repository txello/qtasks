import asyncio
import time
from based_async_app import load_test_job


async def enqueue_jobs(num):
    start_time = time.time()
    for i in range(num):
        print(f"Enqueuing job {i}")
        await load_test_job.add_task(args=(i,))
    end_time = time.time()
    print("Start time: ", start_time)
    print("All jobs enqueued within: ", end_time - start_time, "seconds")


async def main(num):
    async def run_single_task(i):
        try:
            result = await load_test_job.add_task(args=(i,))
            return result
        except asyncio.TimeoutError:
            return f"Истекло время ожидания задачи {i}"

    tasks = [run_single_task(i) for i in range(num)]

    start = time.perf_counter()
    await asyncio.gather(*tasks)
    duration = time.perf_counter() - start
    print(f"Выполнено {num} задач за {duration:.2f} секунд")


async def main2(num):
    start_time = time.time()
    for i in range(num):
        await load_test_job.add_task(args=(i,))
    end_time = time.time()
    print(f"Выполнено: {num} задач за {(end_time - start_time):.2f} секунд")


async def run():
    await enqueue_jobs(20000)

if __name__ == "__main__":
    asyncio.run(run())

import asyncio
import logging
import time

from qtasks.asyncio import QueueTasks

app = QueueTasks()
app.config.logs_default_level_server = logging.INFO
app.config.running_older_tasks = True
app.config.delete_finished_tasks = True
app.config.result_time_interval = 0.1

@app.task(
    description="Task for load testing"
)
async def load_test_job(num: int):
    end_time = time.time()
    print(f"Job {num} finished at {end_time}")
    return

###


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
            return f"Timeout for task {i}"

    tasks = [run_single_task(i) for i in range(num)]

    start = time.perf_counter()
    await asyncio.gather(*tasks)
    duration = time.perf_counter() - start
    print(f"Completed {num} tasks in {duration:.2f} seconds")


async def main2(num):
    start_time = time.time()
    for i in range(num):
        await load_test_job.add_task(args=(i,))
    end_time = time.time()
    print(f"Completed: {num} tasks in {(end_time - start_time):.2f} seconds")


async def run():
    await main(20000)

if __name__ == "__main__":
    asyncio.run(run())

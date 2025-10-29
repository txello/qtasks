import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from qtasks import QueueTasks

app = QueueTasks()
app.config.logs_default_level_server = logging.INFO
app.config.running_older_tasks = True
app.config.delete_finished_tasks = True
app.config.result_time_interval = 0.1

@app.task(
    description="Задача для тестирования нагрузки."
)
def load_test_job(num: int):
    end_time = time.time()
    print(f"Job {num} finished at {end_time}")
    return

###


def enqueue_jobs(num):
    start_time = time.time()
    for i in range(num):
        print(f"Enqueuing job {i}")
        load_test_job.add_task(i)
    end_time = time.time()
    print("Start time: ", start_time)
    print("All jobs enqueued within: ", end_time - start_time, "seconds")


def main(num):
    async def run_single_task(i):
        try:
            result = load_test_job.add_task(i)
            return result
        except TimeoutError:
            return f"Истекло время ожидания задачи {i}"

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_single_task, i) for i in range(num)]
        [f.result() for f in as_completed(futures)]

    duration = time.perf_counter() - start
    print(f"Выполнено {num} задач за {duration:.2f} секунд")


def main2(num):
    start_time = time.time()
    for i in range(num):
        load_test_job.add_task(i)
    end_time = time.time()
    print(f"Выполнено: {num} задач за {(end_time - start_time):.2f} секунд")


def run():
    main(20000)

if __name__ == "__main__":
    run()

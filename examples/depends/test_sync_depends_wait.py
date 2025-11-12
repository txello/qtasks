from based_sync_depends import test
from concurrent.futures import ThreadPoolExecutor, as_completed

def main():
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(test.add_task) for _ in range(10)]
        [f.result() for f in as_completed(futures)]


main()

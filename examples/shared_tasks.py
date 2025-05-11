from qtasks import shared_task

@shared_task(priority=0)
def sync_test():
    print("sync_test")
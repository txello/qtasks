from qtasks import SyncRouter

router = SyncRouter()


@router.task(
    description="Test router task."
)
def router_test():
    print("router_test")

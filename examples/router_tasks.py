from qtasks import Router

router = Router(method="sync")


@router.task()
def router_test():
    print("router_test")

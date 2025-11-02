from qtasks import Router

router = Router(method="sync")


@router.task(
    description="Тестовая задача маршрутизатора."
)
def router_test():
    print("router_test")

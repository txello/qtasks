from qtasks import AsyncRouter

router = AsyncRouter()


@router.task(
    description="Тестовая задача маршрутизатора."
)
async def router_test():
    print("router_test")

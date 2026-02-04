from qtasks import AsyncRouter

router = AsyncRouter()


@router.task(
    description="Router test task."
)
async def router_test():
    print("router_test")

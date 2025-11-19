from qtasks.schemas.task_cls import AsyncTaskCls
from qtasks.utils.tasks.chains.async_chains import AsyncChain


class AsyncTaskUtils:
    @staticmethod
    async def chain(*tasks: AsyncTaskCls) -> AsyncChain:
        chain = AsyncChain(*tasks)
        return chain

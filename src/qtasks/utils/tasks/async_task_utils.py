from qtasks.schemas.task_cls import AsyncTaskCls
from qtasks.utils.tasks.chains.async_chains import AsyncChain


class AsyncTaskUtils:
    @staticmethod
    def chain(*tasks: AsyncTaskCls) -> AsyncChain:
        return AsyncChain(*tasks)

from qtasks.schemas.task_cls import SyncTaskCls
from qtasks.utils.tasks.chains.sync_chains import SyncChain


class SyncTaskUtils:
    @staticmethod
    def chain(*tasks: SyncTaskCls) -> SyncChain:
        return SyncChain(*tasks)

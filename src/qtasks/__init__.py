"""+--------------------------------------------------+
|   Q T a s k s                                     |
|   Task Queue Framework                            |
+--------------------------------------------------+"""

from qtasks.plugins.depends import Depends
from qtasks.qtasks import QueueTasks
from qtasks.routers import AsyncRouter, SyncRouter
from qtasks.utils import shared_task
from qtasks.version import __version__

__all__ = [
    "QueueTasks",
    "AsyncRouter",
    "SyncRouter",
    "shared_task",
    "Depends",
    "__version__",
]

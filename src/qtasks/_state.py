from __future__ import annotations

from typing import TYPE_CHECKING, Union

from qtasks.logs import Logger

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks as aioQueueTasks
    from qtasks.qtasks import QueueTasks


app_main: Union[QueueTasks, aioQueueTasks, None] = None
"""
`app_main` - Contains the main application [`QueueTasks`](../api/queuetasks.md).

Variable is updated upon initialization of `QueueTasks` and/or before calling [`self.starter.start()`](../api/starters/basestarter.md#qtasks.starters.base.BaseStarter.start)
inside [`app.run_forever()`](../api/queuetasks.md#qtasks.qtasks.QueueTasks.run_forever).
"""

log_main: Logger = Logger(name="QueueTasks", subname="_state")
"""
`log_main` - Contains the main logging component [`Logger`](../api/logs.md).
Variable is updated upon initialization of [`QueueTasks`](../api/queuetasks.md).

Default: Logger(name="QueueTasks", subname="_state")
"""

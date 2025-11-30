from __future__ import annotations

from typing import TYPE_CHECKING, Union

from qtasks.logs import Logger

if TYPE_CHECKING:
    from qtasks.asyncio.qtasks import QueueTasks as aioQueueTasks
    from qtasks.qtasks import QueueTasks


app_main: Union[QueueTasks, aioQueueTasks, None] = None
"""
`app_main` - Хранит в себе основное приложение [`QueueTasks`](../api/queuetasks.md).

Переменная обновляется при инициализации `QueueTasks` и/или перед вызовом [`self.starter.start()`](../api/starters/basestarter.md#qtasks.starters.base.BaseStarter.start)
внутри [`app.run_forever()`](../api/queuetasks.md#qtasks.qtasks.QueueTasks.run_forever).
"""

log_main: Logger = Logger(name="QueueTasks", subname="_state")
"""
`log_main` - Хранит в себе компонент логирования [`Logger`](../api/logs.md).
Переменная обновляется при инициализации [`QueueTasks`](../api/queuetasks.md).

По умолчанию: Logger(name="QueueTasks", subname="_state")
"""

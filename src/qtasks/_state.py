from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks


app_main: "QueueTasks" = None
"""
`app_main` - Хранит в себе основное приложение [`QueueTasks`](/qtasks/ru/api/queuetasks/).

Переменная обновляется при инициализации `QueueTasks` и/или перед вызовом [`self.starter.start()`](/qtasks/ru/api/starters/basestarter#qtasks.starters.base.BaseStarter.start)
внутри [`app.run_forever()`](/qtasks/ru/api/queuetasks/#qtasks.qtasks.QueueTasks.run_forever).
"""
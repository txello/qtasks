from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qtasks.qtasks import QueueTasks


# `app_main` - Хранит в себе основное приложение `QueueTasks`.
# Переменная обновляется при инициализации `QueueTasks`,
# и/или перед вызовом `self.starter.start()` внутри `app.run_forever()`.
app_main: "QueueTasks" = None
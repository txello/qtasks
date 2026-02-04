from contextlib import contextmanager
from typing import Annotated

from qtasks import QueueTasks
from qtasks.plugins.depends import Depends, ScopeEnum


app = QueueTasks()
app.config.delete_finished_tasks = True
app.config.running_older_tasks = True
app.config.logs_default_level_server = 20


@contextmanager
def test_dep():
    print("Open")
    yield 123
    print("Close")


@app.task
def test(dep: Annotated[int, Depends(test_dep, scope=ScopeEnum.TASK)]):
    print(dep)


if __name__ == "__main__":
    app.run_forever()

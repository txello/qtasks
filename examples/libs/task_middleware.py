from qtasks.middlewares import TaskMiddleware

class MyTaskMiddleware(TaskMiddleware):
    def __init__(self, task_executor):
        super().__init__(task_executor)
        print(task_executor.task_broker)

    async def __call__(self, *args, **kwargs):
        return self
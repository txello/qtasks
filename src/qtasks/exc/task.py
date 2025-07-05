"""Task exceptions."""


class TaskCancelError(RuntimeError):
    """Исключение, вызываемое при отмене задачи.

    Может быть перехвачено в Воркере для обработки отмены задач.
    """

    def __init__(self, *args):
        """Инициализация исключения."""
        super().__init__(*args)

"""Plugins exceptions."""


class TaskPluginTriggerError(Exception):
    """Исключение, вызываемое при срабатывании триггера плагина.

    Может быть перехвачено в Воркере для обработки срабатывания триггеров.
    """

    def __init__(self, *args, **kwargs):
        """Инициализация исключения."""
        super().__init__(*args)
        self.kwargs = kwargs

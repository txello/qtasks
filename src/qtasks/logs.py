import logging
from typing_extensions import Annotated, Doc


class Logger:
    """
    `Logger` - Класс логирования, используется всеми компонентами.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.logs import Logger
    
    logger = Logger(name="QueueTasks", subname="Global")
    app = QueueTasks(logs=logger)

    app.log.debug("Тест") # asctime [QueueTasks: DEBUG] (QueueTasks) Тест
    ```
    """

    def __init__(self,
            name: Annotated[
                str,
                Doc(
                    """
                    Имя. Используется в шаблоне `%(name)s`.
                    """
                )
            ],

            subname: Annotated[
                str,
                Doc(
                    """
                    Имя компонента.

                    По умолчанию: None.
                    """
                )
            ] = None,
            default_level: Annotated[
                str,
                Doc(
                    """
                    Level по умолчанию.
                    
                    По умолчанию: `logging.DEBUG`.
                    """
                )
            ] = logging.DEBUG,
            format: Annotated[
                str,
                Doc(
                    """
                    Формат логирования.
                    
                    По умолчанию: `%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s`.
                    """
                )
            ] = None
        ):
        """Экземпляр Logger.

        Args:
            name (str): Имя. Используется в шаблоне `%(name)s`.
            subname (str, optional): Имя компонента. По умолчанию: None.
            default_level (int, optional): Level по умолчанию. По умолчанию: `logging.DEBUG`.
            format (str, optional): Формат логирования. По умолчанию: `%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s`.
        """
        self.name = name
        self.subname = subname
        logging.basicConfig(
            level=default_level,
            format=(format or "%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s")
        )
        self.logger = logging.getLogger(name)
    
    def critical(self, *args, **kwargs):
        """Critical"""
        self._log(logging.CRITICAL, *args, **kwargs)
    def error(self, *args, **kwargs):
        """Error"""
        self._log(logging.ERROR, *args, **kwargs)
    def warning(self, *args, **kwargs):
        """Warning"""
        self._log(logging.WARNING, *args, **kwargs)
    def info(self, *args, **kwargs):
        """Info"""
        self._log(logging.INFO, *args, **kwargs)
    def debug(self, *args, **kwargs):
        """Debug"""
        self._log(logging.DEBUG, *args, **kwargs)
    
    def _log(self, level, msg, *args, **kwargs):
        extra = kwargs.pop("extra", {})
        extra["subname"] = self.subname
        self.logger.log(level, msg, *args, extra=extra, **kwargs)
    
    def with_subname(self, new_subname: str) -> "Logger":
        """Обновляем `subname`.

        Args:
            new_subname (str): Новый `subname`.

        Returns:
            Logger: Новый `Logger`.
        """
        return Logger(self.name, new_subname, default_level=self.logger.level)
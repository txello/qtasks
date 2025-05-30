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
                    
                    По умолчанию: `logging.INFO`.
                    """
                )
            ] = logging.INFO,
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
        self.name = name
        self.subname = subname or "-"
        self.format = format
        self.default_level = default_level
        self.logger = logging.getLogger(name)

        formatter = logging.Formatter(
            self.format or "%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s"
        )

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.setLevel(default_level)
    
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
    
    
    def with_subname(self, new_subname: str) -> "Logger":
        """Обновляем `subname`.

        Args:
            new_subname (str): Новый `subname`.

        Returns:
            Logger: Новый `Logger`.
        """
        return Logger(self.name, new_subname, default_level=self.default_level, format=self.format)
    
    def update_logger(self, **kwargs) -> "Logger":
        """Обновляем `Logger`.

        Args:
            kwargs (dict): Новые данные задачи.
            
        Returns:
            Logger: Новый `Logger`.
        """
        name = kwargs.get("name", None) or self.name
        subname = kwargs.get("subname", None) or self.subname
        default_level = kwargs.get("default_level", None) or self.default_level
        format = kwargs.get("format", None) or self.format
        return Logger(name=name, subname=subname, default_level=default_level, format=format)
    
    def _log(self, level, msg, *args, **kwargs):
        extra = kwargs.pop("extra", {})
        if "subname" not in extra:
            extra["subname"] = self.subname
        self.logger.log(level, msg, *args, extra=extra, **kwargs)

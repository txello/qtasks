import logging


class Logger:
    def __init__(self,
            name: str,
            subname: str = None,
            default_level: int = logging.DEBUG,
            format: str = None
        ):
        self.name = name
        self.subname = subname
        logging.basicConfig(
            level=default_level,
            format=(format or "%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s")
        )
        self.logger = logging.getLogger(name)
    
    def critical(self, *args, **kwargs): self._log(logging.CRITICAL, *args, **kwargs)
    def error(self, *args, **kwargs): self._log(logging.ERROR, *args, **kwargs)
    def warning(self, *args, **kwargs): self._log(logging.WARNING, *args, **kwargs)
    def info(self, *args, **kwargs): self._log(logging.INFO, *args, **kwargs)
    def debug(self, *args, **kwargs): self._log(logging.DEBUG, *args, **kwargs)
    
    def _log(self, level, msg, *args, **kwargs):
        extra = kwargs.pop("extra", {})
        extra["subname"] = self.subname
        self.logger.log(level, msg, *args, extra=extra, **kwargs)
    
    def with_subname(self, new_subname: str) -> "Logger":
        return Logger(self.name, new_subname, default_level=self.logger.level)
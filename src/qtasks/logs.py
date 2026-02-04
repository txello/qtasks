"""Logging."""
from __future__ import annotations

import logging
from typing import Annotated

from typing_extensions import Doc


class Logger:
    """`Logger` - Logging class, used by all components.

    ## Example

    ```python
    from qtasks import QueueTasks
    from qtasks.logs import Logger

    logger = Logger(name="QueueTasks", subname="Global")
    app = QueueTasks(log=logger)

    app.log.debug("Test") # asctime [QueueTasks: DEBUG] (QueueTasks) Test
    ```
    """

    def __init__(
        self,
        name: Annotated[
            str,
            Doc(
                """
                    Name.

                    Used in the `%(name)s` pattern.
                    """
            ),
        ],
        subname: Annotated[
            str | None,
            Doc(
                """
                    Component name.

                    Default: None.
                    """
            ),
        ] = None,
        default_level: Annotated[
            int,
            Doc(
                """
                    Default level.

                    Default: `logging.INFO`.
                    """
            ),
        ] = logging.INFO,
        format: Annotated[
            str | None,
            Doc(
                """
                    Logging format.

                    Default: `%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s`.
                    """
            ),
        ] = None,
    ):
        """
        Logger instance.

        Args:
            name (str): Name. Used in the `%(name)s` pattern.
            subname (str, optional): Component name. Default: `None`.
            default_level (int, optional): Default level. Default: `logging.DEBUG`.
            format (str, optional): Logging format.
        """
        self.name = name
        self.name = name
        self.subname = subname or "-"
        self.format = format
        self.default_level = default_level
        self.logger = logging.getLogger(name)

        formatter = logging.Formatter(
            self.format
            or "%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s"
        )

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.setLevel(default_level)

    def critical(self, *args, **kwargs):
        """Critical."""
        self._log(logging.CRITICAL, *args, **kwargs)

    def error(self, *args, **kwargs):
        """Error."""
        self._log(logging.ERROR, *args, **kwargs)

    def warning(self, *args, **kwargs):
        """Warning."""
        self._log(logging.WARNING, *args, **kwargs)

    def info(self, *args, **kwargs):
        """Info."""
        self._log(logging.INFO, *args, **kwargs)

    def debug(self, *args, **kwargs):
        """Debug."""
        self._log(logging.DEBUG, *args, **kwargs)

    def with_subname(
        self,
        new_subname: str,
        default_level: int | None = None,
        format: str | None = None,
    ) -> Logger:
        """
        Update `subname`.

        Args:
            new_subname (str): New `subname`.
            default_level (int, optional): New logging level. Default: `None`.
            format (str, optional): New logging format. Default: `None`.

        Returns:
            Logger: New `Logger`.
        """
        return Logger(
            self.name,
            new_subname,
            default_level=default_level or self.default_level,
            format=format or self.format,
        )

    def update_logger(self, **kwargs) -> Logger:
        """
        Update `Logger`.

        Args:
            kwargs (dict): New task data.

        Returns:
            Logger: New `Logger`.
        """
        name = kwargs.get("name") or self.name
        subname = kwargs.get("subname") or self.subname
        default_level = kwargs.get("default_level") or self.default_level
        format = kwargs.get("format") or self.format
        return Logger(
            name=name, subname=subname, default_level=default_level, format=format
        )

    def _log(self, level, msg, *args, **kwargs):
        extra = kwargs.pop("extra", {})
        if "subname" not in extra:
            extra["subname"] = self.subname
        self.logger.log(level, msg, *args, extra=extra, **kwargs)

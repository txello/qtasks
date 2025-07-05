"""Global Config Schema."""

from dataclasses import dataclass


@dataclass
class GlobalConfigSchema:
    """`GlobalConfigSchema` схема.

    Args:
        name (str): Название `GlobalConfig.name`.
        status (str): Название `GlobalConfig.status`.
    """

    name: str
    status: str

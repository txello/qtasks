from dataclasses import dataclass


@dataclass
class GlobalConfigSchema:
    """`GlobalConfigSchema` схема.

    Args:
        name (str): Название `GlobalConfig.name`.
    """
    name: str
    status: str
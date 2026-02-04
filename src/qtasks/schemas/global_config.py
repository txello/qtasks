"""Global Config Schema."""

from dataclasses import dataclass


@dataclass
class GlobalConfigSchema:
    """
    `GlobalConfigSchema` schema.
    
        Args:
            name (str): Name `GlobalConfig.name`.
            status (str): Name `GlobalConfig.status`.
    """

    name: str
    status: str

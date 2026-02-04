"""Django Autodiscover."""

import importlib
import logging
from typing import Optional

try:
    from django.conf import settings
    from django.utils.module_loading import module_has_submodule
except ImportError as exc:
    raise ImportError("Install with `pip install Django` to use this contrib.") from exc
from importlib.util import find_spec

logger = logging.getLogger(__name__)


def autodiscover_tasks(app, modules: Optional[list[str]] = None):
    """
    Automatically imports the specified modules from all INSTALLED_APPS to register tasks with QTasks.

    Args:
        app(QueueTasks): application.
        modules (List[str]): Modules for auto-discovery. Default: `["tasks"]`.
    """
    modules = modules or ["tasks"]

    for app_name in settings.INSTALLED_APPS:
        try:
            module = importlib.import_module(app_name)
        except Exception as e:
            logger.warning(f"[QTasks] Failed to import {app_name}: {e}")
            continue

        try:
            for module_name in modules:
                if module_has_submodule(module, module_name) or find_spec(
                    f"{app_name}.{module_name}"
                ):
                    importlib.import_module(f"{app_name}.{module_name}")
                    logger.debug(f"[QTasks] Found {module_name}.py in {app_name}")
        except Exception as e:
            logger.exception(
                f"[QTasks] Error importing {app_name}.{module_name}: {e}"
            )

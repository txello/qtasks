"""Django Autodiscover."""

import importlib
import logging

try:
    from django.conf import settings
    from django.utils.module_loading import module_has_submodule
except ImportError:
    raise ImportError("Install with `pip install Django` to use this contrib.")
from importlib.util import find_spec

logger = logging.getLogger(__name__)


def autodiscover_tasks(app):
    """Автоматически импортирует tasks.py из всех INSTALLED_APPS, чтобы зарегистрировать задачи в QTasks."""
    for app_name in settings.INSTALLED_APPS:
        try:
            module = importlib.import_module(app_name)
        except Exception as e:
            logger.warning(f"[QTasks] Не удалось импортировать {app_name}: {e}")
            continue

        try:
            # Явно проверяем, есть ли модуль tasks
            if module_has_submodule(module, "tasks") or find_spec(f"{app_name}.tasks"):
                importlib.import_module(f"{app_name}.tasks")
                logger.debug(f"[QTasks] Найден tasks.py в {app_name}")
        except Exception as e:
            logger.exception(f"[QTasks] Ошибка при импорте {app_name}.tasks: {e}")

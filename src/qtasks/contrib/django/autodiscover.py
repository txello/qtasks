"""Django Autodiscover."""

import importlib
import logging
from typing import List

try:
    from django.conf import settings
    from django.utils.module_loading import module_has_submodule
except ImportError:
    raise ImportError("Install with `pip install Django` to use this contrib.")
from importlib.util import find_spec

logger = logging.getLogger(__name__)


def autodiscover_tasks(app, modules: List[str] = ["tasks"]):
    """Автоматически импортирует указанные модули из всех INSTALLED_APPS, чтобы зарегистрировать задачи в QTasks.

    Args:
        app (QueueTasks): приложение.
        modules (List[str]): Модули для автодискавери. По умолчанию: `["tasks"]`.
    """
    for app_name in settings.INSTALLED_APPS:
        try:
            module = importlib.import_module(app_name)
        except Exception as e:
            logger.warning(f"[QTasks] Не удалось импортировать {app_name}: {e}")
            continue

        try:
            for module_name in modules:
                if module_has_submodule(module, module_name) or find_spec(f"{app_name}.{module_name}"):
                    importlib.import_module(f"{app_name}.{module_name}")
                    logger.debug(f"[QTasks] Найден {module_name}.py в {app_name}")
        except Exception as e:
            logger.exception(f"[QTasks] Ошибка при импорте {app_name}.{module_name}: {e}")

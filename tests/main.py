"""Init tests."""

import sys
import pytest
from pathlib import Path


if __name__ == "__main__":
    # Корень проекта
    ROOT = Path(__file__).resolve().parent

    # Список тестов
    test_files = [
        str(ROOT / "test_sync_task.py"),
        str(ROOT / "test_async_task.py"),
    ]

    # Аргументы pytest
    args = [
        "-v",
        "--tb=short",
        *test_files,
    ]

    # Запуск
    sys.exit(pytest.main(args))

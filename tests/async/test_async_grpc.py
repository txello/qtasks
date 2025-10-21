import os
import sys
import pytest

from qtasks.tests import AsyncTestCase
from qtasks.schemas.test import TestConfig

parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, parent_dir)

from apps.app_async import app

@pytest.fixture(scope="package")
def app_script() -> str:
    return "app_async.py"

@pytest.fixture()
def test_case():
    """Создаёт конфигурацию тестов."""
    case = AsyncTestCase(app=app)
    case.settings(TestConfig.full())
    return case

import json
import os
import sys
import time
import pytest
import grpc

from qtasks.plugins.grpc.core import qtasks_pb2, qtasks_pb2_grpc
from qtasks.tests import AsyncTestCase
from qtasks.schemas.test import TestConfig

parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, parent_dir)

from apps.app_async import app

@pytest.fixture(scope="package")
def app_script() -> str:
    return "app_sync.py"

@pytest.fixture()
def test_case():
    """Создаёт конфигурацию тестов."""
    case = AsyncTestCase(app=app)
    case.settings(TestConfig.full())
    return case


@pytest.mark.sync
def test_grpc_add_task(test_case):
    """Создание задачи через gRPC."""
    with grpc.insecure_channel("localhost:50051") as channel:
            stub = qtasks_pb2_grpc.QTasksServiceStub(channel)

            req = qtasks_pb2.AddTaskRequest(
                name="test",
                args_json=json.dumps([5]),
                kwargs_json=json.dumps({}),
                timeout=0.0,
                priority=0,
            )
            print(req)

            resp = stub.AddTask(req)
            print("AddTask →", resp.ok, resp.uuid, resp.error)

@pytest.mark.sync
def test_grpc_get_task(test_case):
    """Создание задачи через gRPC."""
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = qtasks_pb2_grpc.QTasksServiceStub(channel)

        # --- 1. Добавляем задачу ---
        req = qtasks_pb2.AddTaskRequest(
            name="add",
            args_json=json.dumps([2, 3]),
            priority=0
        )
        print(req)

        resp = stub.AddTask(req)
        print("AddTask →", resp.ok, resp.uuid, resp.error, resp.result_json)

        # --- 2. Получаем статус задачи ---
        if resp.ok:
            get_req = qtasks_pb2.GetTaskRequest(uuid=resp.uuid, include_result=True)
            while True:
                get_resp = stub.GetTask(get_req)
                print("GetTask →", get_resp.status)

                if get_resp.status in {"success", "error", "cancelled"}:
                    print("Result:", get_resp.result_json)
                    break

                time.sleep(1)

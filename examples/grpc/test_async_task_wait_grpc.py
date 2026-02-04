import asyncio
import json

import grpc

from qtasks.plugins.grpc.core import qtasks_pb2, qtasks_pb2_grpc


async def main():
    # Connect to the gRPC server
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = qtasks_pb2_grpc.QTasksServiceStub(channel)

        # --- 1. Add task ---
        req = qtasks_pb2.AddTaskRequest(
            name="add",
            args_json=json.dumps([2, 3]),
            timeout=50,
            priority=0,
        )
        print(req)

        resp = await stub.AddTask(req)
        print("AddTask →", resp.ok, resp.uuid, resp.error, resp.result_json)

        # --- 2. Get task status ---
        if resp.ok:
            get_req = qtasks_pb2.GetTaskRequest(uuid=resp.uuid, include_result=True)
            while True:
                get_resp = await stub.GetTask(get_req)
                print("GetTask →", get_resp.status)

                if get_resp.status in {"success", "error", "cancelled"}:
                    print("Result:", get_resp.result_json)
                    break

                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

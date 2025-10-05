"""Test Async App Client"""

import asyncio
from app_async import app

async def main():
    await app.add_task("test", 5, timeout=50)

asyncio.run(main())

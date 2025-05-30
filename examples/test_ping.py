import asyncio

from based_async_app import app

print(asyncio.run(app.ping()))

from based_sync_app import app

print(app.ping())

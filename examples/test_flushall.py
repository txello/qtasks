import asyncio

from based_async_app import app

asyncio.run(app.flush_all())

from based_sync_app import app

app.flush_all()

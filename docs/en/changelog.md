# Update History

## v1.7.1 2026-02-05

- The translation of the code from Russian to English has been corrected.

## v1.7.0 2026-02-05

- Added `(A)syncTaskUtils` and `(A)syncChain`.
- Added the ability to get settings for `QueueConfig` from `os.environ`.
- Added `(A)syncTaskCls`.
- Added `(A)syncgRPCPlugin`.
- Added plugin systems for `(A)syncStats`.
- Added `stats_inspect` plugin trigger for `(A)syncStats`.
- Added ExitStack support for `Depends` and the `scope=` parameter for it.
- Added `plugin_cache=` for plugin triggers.
- All code translated into English.
- `Router` changed to `(A)syncRouter`.
- Updated debug output.
- Updated refactoring settings for E, W, F, B, I, and UP.
- Fixed typing in `(A)syncRouter.task`.
- Fixed parameter in the `autodiscover_tasks` function.
- Fixed `Config` and `Task` models.
- Fixed plugin calls.
- Code refactoring.

### Documentation

- Added English as the default language.
- Added the `Architecture` section.
- Translated all pages into English.
- Fixed support for `mermaid` diagrams.
- Updated page texts.

## v1.6.0 2025-09-20

- Added `(A)syncSocketBroker`.
- Added `(A)syncStats`, `InspectStats`, and `UtilsInspectStats`.
- Added `(A)StatePlugin` plugin.
- Added `description` and `max_time` parameters for tasks.
- Added `autodiscover_tasks()` function for integration with Django.
- Added `result_time_interval` setting to specify the execution time for `(A)syncResult`.
- Added `HTTP+QTasks` request analytics via the `Locust+FastAPI plugin` to tests.
- Added testing via `tox` on versions `py310`, `py311`, `py312`, and `py313`
in synchronous and asynchronous modes.
- Changed the way plugins work.
- Changed the `add_task` request method from `args=()` and `kwargs={}` to `*args`
and `**kwargs`.
- Changed the `middlewares` parameter to `middlewares_before` and `middlewares_after`.
- Changed the `logs_default_level` parameter to `logs_default_level_server` and
`logs_default_level_client`.
- Changed the `app.init_*` functions to `app.events.on.*`.
- Changed the task error logging level from `warning` to `error`.
- Changed testing from `unittest` to `pytest`.
- Changed the broker in testing from Redis to Socket.
- Changed testing functions.
- Fixed data transfers for plugins.
- Fixed data transfer errors between components.
- Fixed schema declarations.
- Fixed `(A)syncDependsPlugin`.
- Refactored code.

## v1.5.1 2025-07-17

- Fixed `pydantic` dependency.

## v1.5.0 2025-07-16

- Added `AsyncPluginMixin`.
- Added plugin triggers.
- Added `Retry` status via the built-in `(A)syncRetryPlugin` plugin.
- Added `**kwargs` parameters as `extra` for `@app.task()`.
- Added `tags` and `decode` parameters for `@app.task()`.
- Added support for `pydantic` via the built-in plugin `(A)syncPydanticWrapperPlugin`.
- Added support for `ArgMeta` to work with task function parameters.
- Added `(A)syncTestPlugin` as an optional plugin.
- Added examples to `examples/`.
- Added parameters for calling plugin triggers `_plugin_trigger()`.
- Added `TaskPluginTriggerError` exception.
- Fixed execution methods for `(A)syncRedisCommandQueue`.
- Fixed data transfer errors between components.
- Code refactoring.

## v1.4.0 2025-06-12

- Added support for generators for tasks.
- Added `Cancel` status for tasks and support in the code.
- Added [`SyncContext`](api/contexts/sync_context.md) and [`AsyncContext`](api/contexts/async_context.md).
- Added `SyncRetryPlugin` and `AsyncRetryPlugin`.
- Added `BaseQueueTasks`.
- Added parameters `retry=`, `retry_on_exc=`, `generate_handler=`, `executor=`,
`middlewares=` for task decorators [`task()`](api/classes/baseqtasks.md#qtasks.base.qtasks.BaseQueueTasks.task)
 and `shared_task()`.
- Added `extra=` parameter for `broker.add` and `storage.add`.
- Added `broker.default_sleep`.
- Added dynamic variable processing for dataclass.
- Added functions for working with plugins.
- Added functions for testing.
- Added `subcribe` to [`QueueConfig`](api/schemas/queueconfig.md).
- Added examples to `examples/`.
- Fixed task parameters.
- Fixed [`Router`](api/router.md).
- Removed `ConfigObserver` from `QueueTasks.config`, returned [`QueueConfig`](api/schemas/queueconfig.md).

## v1.3.0 2025-05-30

- Added [`Logger`](api/logs.md) and changed `print()` outputs to
the appropriate method.
- Added [`SyncTaskExecutor`](api/executors/sync_task_executor.md) and
[`AsyncTaskExecutor`](api/executors/async_task_executor.md) and added to
[`Worker`](api/workers/baseworker.md).
- Added [`SyncRedisCommandQueue`](api/classes/sync_redis_commands.md)
 and [`AsyncRedisCommandQueue`](api/classes/async_redis_commands.md).
- Added [`SyncKafkaBroker`](api/brokers/sync_kafkabroker.md).
- Added `ConfigObserver` and replaced it in `QueueTasks.config`.
- Added [`BaseMiddleware`](api/middlewares/basemiddleware.md) and [`TaskMiddleware`](api/middlewares/task_middleware.md).
- Added [`ping()`](api/queuetasks.md#qtasks.qtasks.QueueTasks.ping).
- Added [`flush_all()`](api/queuetasks.md#qtasks.qtasks.QueueTasks.flush_all).
- Added the `echo=` parameter for the [`task()`](api/queuetasks.md#qtasks.qtasks.QueueTasks.task
 and `shared_task()`.
- Added `awaiting=` parameter for `shared_task()` task decorators.
- Added `log=` parameter for [`QueueTasks`](api/queuetasks.md).
- Added the `broker_url=` parameter for [`QueueTasks`](api/queuetasks.md).
- Added an example of concurrent task performance.
- Changed the [`storage.start()`](api/storages/basestorage.md#qtasks.storages.base.BaseStorage.start)
 function to add server startup status with TTL. Added corresponding config.
- Changed test classes.
- Fixed default component calls.

## v1.2.0 2025-05-20

- Added [`SyncResult`](api/results/sync_result.md)/[`AsyncResult`](api/results/async_result.md)
 for receiving real-time tasks.
- Added [`SyncTask`](api/registries/sync_task_decorator.md)/[`AsyncTask`](api/registries/async_task_decorator.md)
 to replace the function with a decorator.
- Added [`qtasks._state.app_main`](api/states.md#qtasks._state.app_main)
 to store a duplicate of the [`QueueTasks`](api/queuetasks.md) application.
- Added [`SyncRedisGlobalConfig`](api/globalconfig/sync_redisglobalconfig.md).
- Added examples to `examples/`.
- Replaced `aiounittest` with `unittest.IsolatedAsyncioTestCase`.
- Fixed component launches.

## v1.1.0 - 2025-04-21

- Added [`TestCase`](api/tests/sync_testcase.md)/[`AsyncTestCase`](api/tests/async_testcase.md).
- Added base classes for testing.
- Added `global_config` parameter for [`BaseStorage`](api/storages/basestorage.md).
- Added [`TaskStatusEnum`](api/schemas/task_status_enum.md).
- Fixed [`QueueConfig`](api/schemas/queueconfig.md) settings.
- Fixed [`BaseWorker`](api/workers/baseworker.md).

## v1.0.1 – 2025-04-15

- Added description.
- Fixed mkdocs error.

## v1.0.0 – 2025-04-15

- Added first version of `QTasks`.

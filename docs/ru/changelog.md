# История обновлений

## v1.5.0 2025-07-16
- Добавлен `AsyncPluginMixin`.
- Добавлены триггеры плагинов.
- Добавлен статус `Retry` через встроенный плагин `(A)syncRetryPlugin`.
- Добавлены параметры `**kwargs` как `extra` для `@app.task()`.
- Добавлены параметры `tags` и `decode` для `@app.task()`.
- Добавлена поддержка `pydantic` через встроенный плагин `(A)syncPydanticWrapperPlugin`.
- Добавлена поддержка `ArgMeta` для работы с параметрами функции задач.
- Добавлен `(A)syncTestPlugin` как необязательный плагин.
- Добавлены примеры в `examples/`.
- Добавлены параметры для вызова триггеров плагинов `_plugin_trigger()`.
- Добавлено исключение `TaskPluginTriggerError`.
- Исправлены способы исполнения для `(A)syncRedisCommandQueue`.
- Исправлены ошибки передачи данных между компонентами.
- Рефакторинг кода.

## v1.4.0 2025-06-12
- Добавлена поддержка генераторов для задач.
- Добавлен статус `Cancel` для задач и поддержка в коде.
- Добавлены [`SyncContext`](/qtasks/ru/api/contexts/sync_context/) и [`AsyncContext`](/qtasks/ru/api/contexts/async_context/).
- Добавлены `SyncRetryPlugin` и `AsyncRetryPlugin`.
- Добавлен `BaseQueueTasks`.
- Добавлены параметры `retry=`, `retry_on_exc=`, `generate_handler=`, `executor=`, `middlewares=` для декораторов задач [`task()`](/qtasks/ru/api/queuetasks/#qtasks.qtasks.QueueTasks.task) и `shared_task()`.
- Добавлены параметр `extra=` для `broker.add` и `storage.add`.
- Добавлен `broker.default_sleep`.
- Добавлена возможность динамической обработки переменных для dataclass.
- Добавлены функции для работы с плагинами.
- Добавлены функции для тестирования.
- Добавлен `subcribe` в [`QueueConfig`](/qtasks/ru/api/schemas/queueconfig/).
- Добавлены примеры в `examples/`.
- Исправлены параметры задач.
- Исправлен [`Router`](/qtasks/ru/api/router/).
- Убран `ConfigObserver` из `QueueTasks.config`, был возвращен [`QueueConfig`](/qtasks/ru/api/schemas/queueconfig/).

## v1.3.0 2025-05-30
- Добавлен [`Logger`](/qtasks/ru/api/logs/) и изменены выводы `print()` на соответствующий способ.
- Добавлен [`SyncTaskExecutor`](/qtasks/ru/api/executors/sync_task_executor/) и [`AsyncTaskExecutor`](/qtasks/ru/api/executors/async_task_executor/) и добавлен в [`Worker`](/qtasks/ru/api/workers/baseworker/).
- Добавлены [`SyncRedisCommandQueue`](/qtasks/ru/api/classes/sync_redis_commands/) и [`AsyncRedisCommandQueue`](/qtasks/ru/api/classes/async_redis_commands/).
- Добавлен [`SyncKafkaBroker`](/qtasks/ru/api/brokers/sync_kafkabroker/).
- Добавлен `ConfigObserver` и был заменен в `QueueTasks.config`.
- Добавлен [`BaseMiddleware`](/qtasks/ru/api/middlewares/basemiddleware/) и [`TaskMiddleware`](/qtasks/ru/api/middlewares/task_middleware/).
- Добавлен [`ping()`](/qtasks/ru/api/queuetasks/#qtasks.qtasks.QueueTasks.ping).
- Добавлен [`flush_all()`](/qtasks/ru/api/queuetasks/#qtasks.qtasks.QueueTasks.flush_all).
- Добавлен параметр `echo=` для декораторов задач [`task()`](/qtasks/ru/api/queuetasks/#qtasks.qtasks.QueueTasks.task) и `shared_task()`.
- Добавлен параметр `awaiting=` для декораторов задач `shared_task()`.
- Добавлен параметр `log=` для [`QueueTasks`](/qtasks/ru/api/queuetasks/).
- Добавлен параметр `broker_url=` для [`QueueTasks`](/qtasks/ru/api/queuetasks/).
- Добавлен пример скорости работы одновременных задач.
- Изменена функция [`storage.start()`](/qtasks/ru/api/storages/basestorage/#qtasks.storages.base.BaseStorage.start) на добавление статуса запуска сервера с TTL. Добавлен соответствующий конфиг.
- Изменены классы тестирования.
- Исправлены вызовы компонентов по умолчанию.

## v1.2.0 2025-05-20
- Добавлены [`SyncResult`](/qtasks/ru/api/results/sync_result)/[`AsyncResult`](/qtasks/ru/api/results/async_result) для получения задачи real-time.
- Добавлены [`SyncTask`](/qtasks/ru/api/registries/sync_task_decorator)/[`AsyncTask`](/qtasks/ru/api/registries/async_task_decorator) для замены функции декоратором.
- Добавлен [`qtasks._state.app_main`](/qtasks/ru/api/states/#qtasks._state.app_main) для хранения дубликата приложения [`QueueTasks`](/qtasks/ru/api/queuetasks).
- Добавлен [`SyncRedisGlobalConfig`](/qtasks/ru/api/globalconfig/sync_redisglobalconfig).
- Добавлены примеры в `examples/`.
- Заменен `aiounittest` на `unittest.IsolatedAsyncioTestCase`.
- Исправлены запуски компонентов.

## v1.1.0 - 2025-04-21
- Добавлен [`TestCase`](/qtasks/ru/api/tests/sync_testcase/)/[`AsyncTestCase`](/qtasks/ru/api/tests/async_testcase/).
- Добавлены базовые классы для тестирования.
- Добавлен параметр `global_config` для [`BaseStorage`](/qtasks/ru/api/storages/basestorage/).
- Добавлен [`TaskStatusEnum`](/qtasks/ru/api/schemas/task_status_enum/).
- Исправлены настройки [`QueueConfig`](/qtasks/ru/api/schemas/queueconfig/).
- Исправлен [`BaseWorker`](/qtasks/ru/api/workers/baseworker/).

## v1.0.1 – 2025-04-15
- Добавлено описание.
- Исправлена ошибка mkdocs.

## v1.0.0 – 2025-04-15
- Добавлена первая версия `QTasks`.

# История обновлений

## v1.2.0 2025-05-20
- Добавлены [`SyncResult`](/qtasks/ru/api/results/sync_result)/[`AsyncResult`](/qtasks/ru/api/results/async_result) для получения задачи real-time.
- Добавлены [`SyncTask`](/qtasks/ru/api/registries/sync_task_decorator)/[`AsyncTask`](/qtasks/ru/api/registries/async_task_decorator) для замены функции декоратором.
- Добавлен [`qtasks._state.app_main`](/qtasks/ru/api/states/#qtasks._state.app_main) для хранения дубликата приложения [`QueueTasks`](/qtasks/ru/api/queuetasks).
- Добавлен [`SyncRedisGlobalConfig`](/qtasks/ru/api/globalconfig/sync_redisglobalconfig).
- Добавлены примеры в examples/
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

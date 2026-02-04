# История обновлений

## v1.7.2 2026-02-05

- Исправлена ссылка на русский язык в файле mkdocs.yml для корректной маршрутизации

## v1.7.1 2026-02-05

- Исправлен перевод кода с русского на английский

## v1.7.0 2026-02-05

- Добавлены `(A)syncTaskUtils` и `(A)syncChain`.
- Добавлена возможность получать настройки для `QueueConfig`из `os.environ`.
- Добавлен `(A)syncTaskCls`.
- Добавлен `(A)syncgRPCPlugin`.
- Добавлены системы плагинов для `(A)syncStats`.
- Добавлен триггер плагинов `stats_inspect` для `(A)syncStats`.
- Добавлена поддержка ExitStack для `Depends` и параметр `scope=` для этого.
- Добавлен `plugin_cache=` для триггеров плагинов.
- Весь код переведён на английский язык.
- `Router` изменен на `(A)syncRouter`.
- Обновлены выводы дебага.
- Обновлены настройки рефакторинга на E, W, F, B, I, и UP.
- Исправлена типизация у `(A)syncRouter.task`.
- Исправлен параметр у функции `autodiscover_tasks`.
- Исправлены модели `Config` и `Task`.
- Исправлены вызовы плагинов.
- Рефакторинг кода.

### Документация

- Добавлен английский язык как язык по умолчанию.
- Добавлен блок `Архитектура`.
- Все страницы переведены на английский язык.
- Исправлена поддержка схем `mermaid`.
- Обновлены тексты страниц.

## v1.6.0 2025-09-20

- Добавлен `(A)syncSocketBroker`.
- Добавлены `(A)syncStats`, `InspectStats` и `UtilsInspectStats`.
- Добавлен плагин `(A)StatePlugin`.
- Добавлены параметры `description` и `max_time` для задач.
- Добавлена функция `autodiscover_tasks()` для интеграции с Django.
- Добавлена настройка `result_time_interval` для задания времени выполнения для
`(A)syncResult`.
- В тестах добавлена аналитика запросов `HTTP+QTasks` через `Locust+FastAPI плагин`.
- Добавлено тестирование через `tox` на версиях `py310`, `py311`, `py312` и `py313`
в синхронном и асинхронном режимах.
- Изменен способ работы с плагинами.
- Изменен способ запроса `add_task` с `args=()` и `kwargs={}` на `*args` и `**kwargs`.
- Изменен параметр `middlewares` на `middlewares_before` и `middlewares_after`.
- Изменен параметр `logs_default_level` на `logs_default_level_server` и `logs_default_level_client`.
- Изменены функции `app.init_*` на `app.events.on.*`.
- Изменен уровень логирования ошибки задачи с `warning` на `error`.
- Изменено тестирование с `unittest` на `pytest`.
- Изменен брокер в тестировании с Redis на Socket.
- Изменены функции тестирования.
- Исправлены передачи данных для плагинов.
- Исправлены ошибки передачи данных между компонентами.
- Исправлены объявления схем.
- Исправлен `(A)syncDependsPlugin`.
- Рефакторинг кода.

## v1.5.1 2025-07-17

- Исправлена зависимость `pydantic`.

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
- Добавлены [`SyncContext`](api/contexts/sync_context.md) и [`AsyncContext`](api/contexts/async_context.md).
- Добавлены `SyncRetryPlugin` и `AsyncRetryPlugin`.
- Добавлен `BaseQueueTasks`.
- Добавлены параметры `retry=`, `retry_on_exc=`, `generate_handler=`, `executor=`,
`middlewares=` для декораторов задач [`task()`](api/classes/baseqtasks.md#qtasks.base.qtasks.BaseQueueTasks.task)
 и `shared_task()`.
- Добавлены параметр `extra=` для `broker.add` и `storage.add`.
- Добавлен `broker.default_sleep`.
- Добавлена возможность динамической обработки переменных для dataclass.
- Добавлены функции для работы с плагинами.
- Добавлены функции для тестирования.
- Добавлен `subcribe` в [`QueueConfig`](api/schemas/queueconfig.md).
- Добавлены примеры в `examples/`.
- Исправлены параметры задач.
- Исправлен [`Router`](api/router.md).
- Убран `ConfigObserver` из `QueueTasks.config`, был возвращен [`QueueConfig`](api/schemas/queueconfig.md).

## v1.3.0 2025-05-30

- Добавлен [`Logger`](api/logs.md) и изменены выводы `print()` на
соответствующий способ.
- Добавлен [`SyncTaskExecutor`](api/executors/sync_task_executor.md) и
[`AsyncTaskExecutor`](api/executors/async_task_executor.md) и добавлен в
[`Worker`](api/workers/baseworker.md).
- Добавлены [`SyncRedisCommandQueue`](api/classes/sync_redis_commands.md)
 и [`AsyncRedisCommandQueue`](api/classes/async_redis_commands.md).
- Добавлен [`SyncKafkaBroker`](api/brokers/sync_kafkabroker.md).
- Добавлен `ConfigObserver` и был заменен в `QueueTasks.config`.
- Добавлен [`BaseMiddleware`](api/middlewares/basemiddleware.md) и [`TaskMiddleware`](api/middlewares/task_middleware.md).
- Добавлен [`ping()`](api/queuetasks.md#qtasks.qtasks.QueueTasks.ping).
- Добавлен [`flush_all()`](api/queuetasks.md#qtasks.qtasks.QueueTasks.flush_all).
- Добавлен параметр `echo=` для декораторов задач [`task()`](api/queuetasks.md#qtasks.qtasks.QueueTasks.task
 и `shared_task()`.
- Добавлен параметр `awaiting=` для декораторов задач `shared_task()`.
- Добавлен параметр `log=` для [`QueueTasks`](api/queuetasks.md).
- Добавлен параметр `broker_url=` для [`QueueTasks`](api/queuetasks.md).
- Добавлен пример скорости работы одновременных задач.
- Изменена функция [`storage.start()`](api/storages/basestorage.md#qtasks.storages.base.BaseStorage.start)
 на добавление статуса запуска сервера с TTL. Добавлен соответствующий конфиг.
- Изменены классы тестирования.
- Исправлены вызовы компонентов по умолчанию.

## v1.2.0 2025-05-20

- Добавлены [`SyncResult`](api/results/sync_result.md)/[`AsyncResult`](api/results/async_result.md)
 для получения задачи real-time.
- Добавлены [`SyncTask`](api/registries/sync_task_decorator.md)/[`AsyncTask`](api/registries/async_task_decorator.md)
 для замены функции декоратором.
- Добавлен [`qtasks._state.app_main`](api/states.md#qtasks._state.app_main)
 для хранения дубликата приложения [`QueueTasks`](api/queuetasks.md).
- Добавлен [`SyncRedisGlobalConfig`](api/globalconfig/sync_redisglobalconfig.md).
- Добавлены примеры в `examples/`.
- Заменен `aiounittest` на `unittest.IsolatedAsyncioTestCase`.
- Исправлены запуски компонентов.

## v1.1.0 - 2025-04-21

- Добавлен [`TestCase`](api/tests/sync_testcase.md)/[`AsyncTestCase`](api/tests/async_testcase.md).
- Добавлены базовые классы для тестирования.
- Добавлен параметр `global_config` для [`BaseStorage`](api/storages/basestorage.md).
- Добавлен [`TaskStatusEnum`](api/schemas/task_status_enum.md).
- Исправлены настройки [`QueueConfig`](api/schemas/queueconfig.md).
- Исправлен [`BaseWorker`](api/workers/baseworker.md).

## v1.0.1 – 2025-04-15

- Добавлено описание.
- Исправлена ошибка mkdocs.

## v1.0.0 – 2025-04-15

- Добавлена первая версия `QTasks`.

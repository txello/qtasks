# Справочник триггеров плагинов

QTasks предоставляет гибкий механизм внедрения плагинов с использованием системы триггеров. Эти триггеры вызываются внутри компонентов и позволяют:

* Изменять входные аргументы задач
* Заменять результат выполнения функций
* Реагировать на события без вмешательства в основную логику

## 📘 Правила именования

* Шаблон: `{компонент}_{функция}_{дополнение}`
* Исключение: компонент `QueueTasks` обозначается как `qtasks`
* Параметры: первым всегда идёт основной компонент (например, `self`), далее — связанные компоненты и параметры контекста

## 📌 Поведение `return`

* `new_args` / `new_model` / `new_data` / `new_result` заменяют соответствующие переменные, если присутствуют
* Если `return` отсутствует или `None`, переменные остаются без изменений
* Последний сработавший плагин имеет приоритет на замену

---

## 🔷 Компоненты

### 🔹 QueueTasks (`qtasks`)

| Триггер                         | Return             | Назначение                                    |
| ------------------------------- | ------------------ | --------------------------------------------- |
| `qtasks_add_task_before_broker` | `new_args: dict`   | Заменяет параметры задачи до передачи брокеру |
| `qtasks_add_task_after_broker`  | —                  | Вызывается после передачи задачи брокеру      |
| `qtasks_get`                    | `new_result: Task` | Заменяет результат получения задачи           |
| `qtasks_stop`                   | —                  | Вызывается при остановке приложения           |
| `qtasks_ping`                   | —                  | Пингует global\_config                        |
| `qtasks_flush_all`              | —                  | Сброс очередей и хранилищ                     |

### 🔹 Broker

| Триггер                       | Return                           | Назначение                                      |
| ----------------------------- | -------------------------------- | ----------------------------------------------- |
| `broker_listen_start`         | —                                | Инициализация прослушивания                     |
| `broker_add_worker`           | `new_args: dict`                 | Заменяет входные параметры задачи для воркера   |
| `broker_add_before`           | `new_model: TaskStatusNewSchema` | Заменяет модель перед записью в хранилище       |
| `broker_add_after`            | —                                | Вызывается после добавления в хранилище         |
| `broker_get`                  | `new_task: Task`                 | Заменяет результат получения задачи             |
| `broker_update`               | `new_kw: dict`                   | Заменяет kwargs при обновлении задачи           |
| `broker_start`                | —                                | Запуск брокера                                  |
| `broker_stop`                 | —                                | Остановка брокера                               |
| `broker_remove_finished_task` | `new_model`                      | Заменяет модель для удаления завершённой задачи |
| `broker_running_older_tasks`  | —                                | Вызывается при восстановлении старых задач      |
| `broker_flush_all`            | —                                | Сброс очередей                                  |

### 🔹 GlobalConfig

| Триггер                    | Return           | Назначение                                   |
| -------------------------- | ---------------- | -------------------------------------------- |
| `global_config_set`        | `new_data: dict` | Заменяет параметры перед установкой значения |
| `global_config_get`        | `new_result`     | Заменяет полученное значение                 |
| `global_config_get_all`    | `new_result`     | Заменяет результат получения всех значений   |
| `global_config_get_match`  | `new_result`     | Заменяет результат поиска по шаблону         |
| `global_config_start`      | —                | Запуск компонента                            |
| `global_config_stop`       | —                | Остановка компонента                         |
| `global_config_set_status` | —                | Сигнал установки статуса                     |

### 🔹 TaskExecutor

| Триггер                                | Return                        | Назначение                                                        |
| -------------------------------------- | ----------------------------- | ----------------------------------------------------------------- |
| `task_executor_args_replace`           | `new_args: Tuple[list, dict]` | Заменяет args и kwargs до выполнения                              |
| `task_executor_middlewares_execute`    | —                             | Вызывается перед выполнением задачи с мидлварами                  |
| `task_executor_run_task`               | `new_result`                  | Заменяет результат выполнения задачи                              |
| `task_executor_run_task_gen`           | `new_results`                 | Заменяет результаты генератора                                    |
| `task_executor_run_task_trigger_error` | `new_result`                  | Заменяет результат при вызове исключения `TaskPluginTriggerError` |
| `task_executor_decode`                 | `new_result`                  | Заменяет результат декодирования результата                       |

### 🔹 Starter

| Триггер         | Return | Назначение                   |
| --------------- | ------ | ---------------------------- |
| `starter_start` | —      | Запуск компонента Starter    |
| `starter_stop`  | —      | Остановка компонента Starter |

### 🔹 Storage

| Триггер                         | Return                    | Назначение                                     |
| ------------------------------- | ------------------------- | ---------------------------------------------- |
| `storage_add`                   | `new_data`                | Заменяет параметры перед добавлением задачи    |
| `storage_get`                   | `new_result: Task`        | Заменяет результат получения задачи            |
| `storage_get_all`               | `new_results: List[Task]` | Заменяет список полученных задач               |
| `storage_update`                | `new_kw: dict`            | Заменяет kwargs при обновлении                 |
| `storage_remove_finished_task`  | —                         | Удаление завершённой задачи                    |
| `storage_start`                 | —                         | Запуск компонента                              |
| `storage_stop`                  | —                         | Остановка компонента                           |
| `storage_add_process`           | `new_data`                | Заменяет параметры при добавлении в процессинг |
| `storage_running_older_tasks`   | `new_data`                | Заменяет данные при восстановлении задач       |
| `storage_delete_finished_tasks` | —                         | Очистка завершённых задач                      |
| `storage_flush_all`             | —                         | Сброс хранилища                                |

### 🔹 Worker

| Триггер                       | Return          | Назначение                                                          |
| ----------------------------- | --------------- | ------------------------------------------------------------------- |
| `worker_execute_before`       | `new_model`     | Заменяет модель перед выполнением                                   |
| `worker_execute_after`        | —               | Вызывается после выполнения задачи                                  |
| `worker_add`                  | `new_data`      | Заменяет параметры создания задачи                                  |
| `worker_start`                | —               | Запуск воркера                                                      |
| `worker_stop`                 | —               | Остановка воркера                                                   |
| `worker_run_task_before`      | `new_data`      | Заменяет данные до выполнения задачи                                |
| `worker_task_error_retry`     | `plugin_result` | Заменяет TaskStatusErrorSchema при повторе                          |
| `worker_remove_finished_task` | `new_data`      | Заменяет TaskPrioritySchema и TaskStatus... для удаления из очереди |

---

Это справочник можно использовать при разработке плагинов, интеграций или системной логики поверх QTasks.

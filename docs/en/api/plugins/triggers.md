# Plugin Trigger Reference Guide

QTasks provides a flexible mechanism for integrating plugins using a system of triggers. These triggers are called within components and allow you to:

* Change task input arguments
* Replace function execution results
* Respond to events without interfering with the main logic

## 📘 Naming rules

* Template: `{component}_{function}_{addition}`
* Exception: the `QueueTasks` component is denoted as `qtasks`
* Parameters: the main component always comes first (e.g., `self`), followed by
related components and context parameters.

## 📌 `return` behavior

* `new_args` / `new_model` / `new_data` / `new_result` replace the corresponding
variables if present.
* If `return` is absent or `None`, the variables remain unchanged.
* The next plugin receives the result from the previous one. If the previous plugin's
result is `None`, the last value or the very first value is used.
* The last plugin that worked has priority for replacement.

Example: if `new_args`, then it stores `{"args": (123,), "kw": {"test": 123}}`.
If one of its parameters is `None`, then the logic above applies.

---

## 🔷 Components

### 🔹 QueueTasks (`qtasks`)

| Trigger                         | Return             | Purpose                                           |
| ------------------------------- | ----------------- - | ------------------------------------------------ |
| `qtasks_add_task_before_broker` | `new_args: dict`   | Replaces task parameters before passing to broker |
| `qtasks_add_task_after_broker`  | —                  | Called after the task is transferred to the broker|
| `qtasks_get`                    | `new_result: Task` | Replaces the result of receiving the task         |
| `qtasks_stop`                   | —                  | Called when the application is stopped            |
| `qtasks_ping`                   | —                  | Pings global\_config                              |
| `qtasks_flush_all`              | —                  | Resets queues and stores                          |

### 🔹 Broker

| Trigger                       | Return                           | Purpose                                          |
| ----------------------------- | -------------------------------- | ------------------------------------------------ |
| `broker_listen_start`         | —                                | Initializes listening                            |
| `broker_add_worker`           | `new_args: dict`                 | Replaces the task input parameters for the worker|
| `broker_add_before`           | `new_model: TaskStatusNewSchema` | Replaces the model before writing to storage     |
| `broker_add_after`            | —                                | Called after adding to storage                   |
| `broker_get`                  | `new_task: Task`                 | Replaces the result of getting the task          |
| `broker_update`               | `new_kw: dict`                   | Replaces kwargs when updating a task             |
| `broker_start`                | —                                | Starts the broker                                |
| `broker_stop`                 | —                                | Stops the broker                                 |
| `broker_remove_finished_task` | `new_model`                      | Replaces the model for deleting a completed task |
| `broker_running_older_tasks`  | —                                | Called when restoring old tasks                  |
| `broker_flush_all`            | —                                | Resets queues                                    |

### 🔹 GlobalConfig

| Trigger                    | Return           | Purpose                                      |
| -------------------------- | ---------------- | -------------------------------------------- |
| `global_config_set`        | `new_data: dict` | Replaces parameters before setting the value |
| `global_config_get`        | `new_result`     | Replaces the retrieved value                 |
| `global_config_get_all`    | `new_result`     | Replaces the result of obtaining all values  |
| `global_config_get_match`  | `new_result`     | Replaces the result of searching by pattern  |
| `global_config_start`      | —                | Component startup                            |
| `global_config_stop`       | —                | Stops the component                          |
| `global_config_set_status` | —                | Status setting signal                        |

### 🔹 TaskExecutor

| Trigger                                | Return                        | Assignment                                                  |
| -------------------------------------- | ----------------------------- | ----------------------------------------------------------- |
| `task_executor_args_replace`           | `new_args: Tuple[list, dict]` | Replaces args and kwargs before execution                   |
| `task_executor_middlewares_execute`    | —                             | Called before task execution with middlewares               |
| `task_executor_run_task`               | `new_result`                  | Replaces the task execution result                          |
| `task_executor_run_task_gen`           | `new_results`                 | Replaces the generator results                              |
| `task_executor_run_task_trigger_error` | `new_result`                  | Replaces the result when `TaskPluginTriggerError` is raised |
| `task_executor_decode`                 | `new_result`                  | Replaces the result of decoding the result                  |


### 🔹 Starter

| Trigger         | Return | Assignment                 |
| --------------- | ------ | -------------------------- |
| `starter_start` | —      | Start the Starter component|
| `starter_stop`  | —      | Stop the Starter component |

### 🔹 Storage

| Trigger                         | Return                    | Purpose                                       |
| ------------------------------- | ------------------------- | --------------------------------------------- |
| `storage_add`                   | `new_data`                | Replaces parameters before adding a task      |
| `storage_get`                   | `new_result: Task`        | Replaces the result of receiving a task       |
| `storage_get_all`               | `new_results: List[Task]` | Replaces the list of received tasks           |
| `storage_update`                | `new_kw: dict`            | Replaces kwargs when updating                 |
| `storage_remove_finished_task`  | —                         | Deletes a completed task                      |
| `storage_start`                 | —                         | Starts the component                          |
| `storage_stop`                  | —                         | Stops the component                           |
| `storage_add_process`           | `new_data`                | Replaces parameters when adding to processing |
| `storage_running_older_tasks`   | `new_data`                | Replaces data when restoring tasks            |
| `storage_delete_finished_tasks` | —                         | Clears completed tasks                        |
| `storage_flush_all`             | —                         | Resets storage                                |

### 🔹 Worker

| Trigger                       | Return          | Assignment                                                               |
| ----------------------------- | --------------- | ------------------------------------------------------------------------ |
| `worker_execute_before`       | `new_model`     | Replaces the model before execution                                      |
| `worker_execute_after`        | —               | Called after task execution                                              |
| `worker_add`                  | `new_data`      | Replaces task creation parameters                                        |
| `worker_start`                | —               | Starts the worker                                                        |
| `worker_stop`                 | —               | Stops the worker                                                         |
| `worker_run_task_before`      | `new_data`      | Replaces data before task execution                                      |
| `worker_task_error_retry`     | `plugin_result` | Replaces TaskStatusErrorSchema on retry                                  |
| `worker_remove_finished_task` | `new_data`      | Replaces TaskPrioritySchema and TaskStatus... for removal from the queue |

### 🔹 Stats

| Триггер         | Return | Назначение                                  |
| --------------- | ------ | ------------------------------------------- |
| `stats_inspect` | —      | Called before `InspectStats` is defined.    |

---

This reference can be used when developing plugins, integrations, or
system logic on top of QTasks.

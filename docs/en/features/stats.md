# Stats

There is a built-in additional component **(A)syncStats** designed for
analytics and inspection of the QTasks application status. The component is
initialized with the `app=app` parameter and provides access to application metadata
and registered tasks without executing them.

Stats is focused on diagnostics, debugging, configuration monitoring, and building
external tools (CLI, WebView, administration panels).

Stats is focused on diagnostics, debugging, configuration monitoring, and building
external tools (CLI, WebView, administration panels).

---

## Capabilities

Currently, the component provides inspection capabilities through the
**InspectStats** object.

### InspectStats.inspect

`(A)syncStats.inspect → InspectStats`

Returns an inspection object through which analytics methods are available.

---

## Application Information

### InspectStats.app(json: bool = False)

Allows you to get complete information about the current instance of QTasks.

Example of text output:

```text
Name: QueueTasks
Method: async
Version: 1.7.0
Configuration              : QueueConfig(max_tasks_process=10, running_older_tasks=True,
delete_finished_tasks=False, task_default_priority=0, task_default_decode=None,
logs_default_level_server=10, logs_default_level_client=20, logs_format='%(asctime)s
[%(name)s: %(levelname)s] (%(subname)s) %(message)s', result_time_interval=0.1,
result_statuses_end=['success', 'error', 'cancel'])
Number of tasks: 14
Number of routers: 1
Number of plugins: 16
Broker: AsyncRedisBroker
Worker: AsyncWorker
Starter: AsyncStarter
Storage: AsyncRedisStorage
GlobalConfig: AsyncRedisGlobalConfig
Log: Logger
Number of initializations: 0
--------------------------------------------------
```

When `json=True`, the method returns a structured dictionary suitable for serialization
and transfer to external systems.

---

## Task information

### InspectStats.tasks(*tasks: tuple[str], json: bool = False)

Returns information about registered tasks.

* Without arguments — for all tasks.
* With task names specified — only for selected tasks.

Example (abbreviated output for two tasks):

```text
Task name: sync_test
Priority: 0
Description: Test synchronous task with decorator.
Tags: —
Asynchronous: False
Generation: sync
Self before task: True
Args: self: SyncTask
Kwargs: —
Middleware after: [<class 'libs.task_middleware.MyTaskMiddleware'>]
--------------------------------------------------
Task name: async_test
Priority: 0
Description: Test asynchronous task.
Tags: —
Asynchronous: True
Generation: False
Self before task: False
Args: —
Kwargs: —
--------------------------------------------- -----
```

When `json=True`, data is returned as a structured dictionary.

---

## Information about a single task

### InspectStats.task(task_name: str, json: bool = False)

Returns information about a single task. Functionally equivalent to `tasks`,
but intended for specific queries.

---

## Using via CLI

The Stats component is integrated into the CLI (currently in a synchronous version).

### Mandatory inspection command

```bash
qtasks -A app:app stats inspect
```

The command displays basic information and available inspection methods.

### Calling InspectStats methods via CLI

```bash
qtasks -A app:app stats inspect <method> <params>
```

The call is made via `getattr`, which allows you to access any `InspectStats` method.

Example:

```bash
qtasks -A app:app stats inspect tasks task1 task2 json=True
```

---

## Features

* Stats does not initiate task execution.
* The component only works with metadata and configuration.
* Text and JSON output formats are supported.
* Designed for CLI, WebView, and external analytics tools.

---

## Summary

(A)syncStats provides:

* centralized application inspection;
* access to task metadata and configuration;
* a basis for monitoring and administration;
* an extensible API for future analytics.

The page is designed as a canvas and can be used as a template for documenting
the analytical and inspection components of QTasks.

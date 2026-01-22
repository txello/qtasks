# Examples → Analytics

The [**(A)syncStats**](../api/stats/basestats.md) component is responsible for
collecting and formatting diagnostic information
about the `QTasks` application and its tasks.
It is initialized by an instance of `QueueTasks` and provides a set of methods for
introspection.
The synchronous version is additionally integrated into the CLI as
the `qtasks stats` command.

---

## 🚀 Where it is used

* **Directly from the code**: an instance of [`(A)syncStats`](../api/stats/basestats.md)
is created
and analysis methods are called.
* **Via CLI**: the synchronous version is available as `qtasks stats`.

Command example (for reference):

```bash
qtasks stats inspect tasks my_task json=true
```

This command will output a structure describing the tasks (in JSON when `json=true`).

---

## 🔎 `inspect()`

The `inspect()` method creates an [**`InspectStats`**] object (../api/stats/inspect/inspect_stats.md),
which contains functions for
detailed inspection:

* `app(json: bool = False)` — information about the application itself
* `task(task_name: str, json: bool = False)` — information about a specific task
* `tasks(*tasks: Tuple[str], json: bool = False)` — summary of several tasks
or all tasks

All these functions support two output formats:

* **Text** (default): aligned columns +
* **JSON** (`json=True`): serialized structure, convenient for parsing and automation

---

## 🧭 `app(json: bool = False)` — summary for the application

**What is output in text mode:**

* Application name
* Launch method
* `QTasks` version
* Current configuration (as a string)
* Number of registered tasks and routers
* Total number of connected plugins (summed by kernel, broker, worker,
starter, storage, and global configuration)
* Number of registered initializations (`on` events)
* Classes of components involved: Broker, Worker, Starter (or `—`), Storage,
GlobalConfig (or `—`), Logger

Format — block, with labels aligned by width and a horizontal separator line.
Example form (data is conditional):

```text
Name: QueueTasks
Method: async
Version: 1.6.0
Configuration: QueueConfig(max_tasks_process=10,
running_older_tasks=True, delete_finished_tasks=True, default_task_priority=0,
logs_default_level_server=20, logs_default_level_client=20,
logs_format='%(asctime)s [%(name)s: %(levelname)s] (%(subname)s) %(message)s',
result_time_interval=0.1, result_statuses_end=['success', 'error', 'cancel'])
Number of tasks: 14
Number of routers: 1
Number of plugins: 3
Number of initializations: 0
Broker: AsyncRedisBroker
Worker: AsyncWorker
Starter: —
Storage: AsyncRedisStorage
GlobalConfig: AsyncRedisGlobalConfig
Log: Logger
--------------------------------------------------
```

**When `json=True`**, a JSON object with the same keys and values is returned.

---

## 🧩 `task(task_name, json: bool = False)` — detailed information about the task

**What is displayed in text mode:** one block per task with the following fields:

* Task name
* Priority
* Description (or `—`)
* Tags (comma-separated list or `—`)
* Asynchronous (flag "awaiting")
* Generation (`yield` mode, flag "generating")
* "Self before task" (`echo`)
* Argument signature: `Args` (positional) and `Kwargs` (keywords with defaults)

**Conditional fields, if specified in the task:**

* `Retries` (retry)
* `Exclude for retries` (`retry_on_exc`, nicely formatted)
* `Decoding` (`decode`)
* `Generator` (`generate_handler`)
* `Executor` (`executor`)
* `Middleware before` / `Middleware after`
* `Additional` — a multi-line section where each key-value pair is output
on a separate line with the marker `*`

**Example form (data is conditional):**

```text
Task name: send_email
Priority: 0
Description: Mailing list
Tags: email, marketing
Asynchronous: True
Generation: False
Self before task: False
Args: recipient: str, subject: str
Kwargs: retries: int=3, timeout: int=30
Retries: 3
Exceptions for retries: [<class 'KeyError'>]
Middleware before: [<class 'AuthMiddleware'>]
Middleware after: [<class 'MetricsMiddleware'>]
Additional:
* concurrency: 5
* queue: high
--------------------------------------------------

**When `json=True`**, an object with the same data is returned (keys correspond
to the labels above).


If the task is not found, a corresponding diagnostic message (text) is displayed,
and when `json=True`, an empty structure or a descriptive error is displayed
(depending on the CLI/wrapper implementation).


---

---

## 📚 `tasks(*tasks, json: bool = False)` — several or all tasks

The behavior is similar to `task(...)`, but for a set of tasks:

* If task names are passed, only they are displayed, in the order listed
* If nothing is passed — **the entire registry** of tasks is displayed
* Task blocks follow each other, separated by the line.

**Example form (conditional data):**

```text
Task name: ping
Priority: 0
Description: —
Tags: —
Asynchronous: True
Generation: False
Self before task: False
Args: host: str
Kwargs: timeout: int=5
--------------------------------------------------
Task name: report_daily
Priority: 1
Description: Daily report
Tags: analytics
Asynchronous: False
Generation: False
Self before task: False
Args: date: datetime.date
Kwargs: format: str=pdf
----------------------- ---------------------------
```

**When `json=True`**, a list of JSON objects is returned — one for each task
in the sample.

---

## 🧱 Formatting and readability

The text output aligns labels to a fixed width (via the internal `label_width`),
so tables look neat in the terminal and logs. `-` separators are used
to visually separate blocks.

---

## ✅ What this means in practice

* Quick audit of application configuration and component environment
* Full visibility for each task: from argument signatures to middleware and additional
options
* Universal JSON format for integration with monitoring, alerting, and dashboards

This analytics is useful in production, CI, and local debugging alike.

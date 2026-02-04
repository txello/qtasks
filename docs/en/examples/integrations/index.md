# Integrations

By default, `QTasks` is very easy to integrate into a system due to its
lightweight memory and threading.
It can be integrated into almost any framework, and there are several ways to
do this:

* Creating tasks via `@app.task`, `@shared_task`, `@router.task`
* Calling a task via `app.add_task(...)` or `this_is_func.add_task(...)`
* Running the framework application as a server via `app.run_forever()`,
or via CLI:

```bash
qtasks -A file:app run
```

---

## 📌 Current integrations

Currently, there is a ready-made integration: **with Django**.
For more details, see the section [Examples → Integrations → Django](./django.md).

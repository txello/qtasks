# Components: The Plugin System

This page describes the architecture of the QTasks plugin system at the component
level:
how plugins are integrated, where exactly they are invoked, and how they affect
the execution flow.

The plugin system is a built-in mechanism for extending components and does not
exist separately from them.
Each component independently determines
**whether it supports plugins and at which points they can be invoked**.

---

## Plugins as part of a component

Each core QTasks component has its own set of plugins,
accessible via:

```python
self.plugins: dict[str, list[BasePluginRegistry]]
```

Where:

* key (str) — the trigger name;
* value (list[BasePluginRegistry]) — a list of registered plugins for
that trigger.
* The list of plugins within each trigger is sorted by priority.
* Sorting is performed in ascending order of priority (from lowest to highest).
* This guarantees a predictable order of plugin execution.

The list of plugins in each trigger is sorted by priority.
Sorting is performed in ascending order of priority (from lowest to highest).

Plugins:

* belong to a specific component;
* are called only at explicitly defined points (triggers);
* do not have direct access to the component’s internal state.

Thus, behavior extension occurs in a controlled and predictable manner.

---

## BasePluginRegistry

Plugins are not stored directly inside components.
Each plugin is wrapped in a plugin registry object.

Base registry type:

```python
BasePluginRegistry
```

This is an abstract class from which the following classes are derived:

* AsyncPluginRegistry
* SyncPluginRegistry

These classes manage the invocation of the corresponding plugin types.

## BasePluginRegistry Fields

Each plugin registry contains the following fields:

| Field      | Type   | Description                          |
| ---------- | ------ | ------------------------------------ |
| `name`     | `str`  | Plugin name (`plugin.name`)          |
| `plugin`   | `Any`  | Plugin instance                      |
| `enabled`  | `bool` | Whether the plugin is allowed to run |
| `priority` | `int`  | Execution priority                   |
| `cache`    | `dict` | Data cache for `_plugin_trigger`     |

---

## PluginMixin and Enabling the Plugin System

For a component to use plugins, it must inherit from
`AsyncPluginMixin` or `SyncPluginMixin`.

The mixin provides:

* the `_plugin_trigger()` method — a callback point for plugins;
* the `add_plugin()` method — a mechanism for registering plugins.

Without connecting the appropriate mixin, the plugin system for the component is
considered disabled.

---

Plugins are enabled using the method:

```python
add_plugin()
```

Method signature:

```python
add_plugin(
    plugin,
    trigger_names=None,
    priority=None,
    class_=None,
)
```

---

## Calling Triggers

Plugin triggers are explicitly called within the component’s logic.

Example of calling an asynchronous trigger:

```python
new_results = await self._plugin_trigger(
    “storage_get_all”,
    storage=self,
    results=results,
    return_last=True,
)
```

A trigger is not a “standard” event, but rather an architectural decision made by
the component author.
If a trigger is not called, plugins are not executed.

---

## Registering Plugins

Plugins are added using `add_plugin()`.

```python
self.add_plugin(
    AsyncRetryPlugin(),
    trigger_names=[“worker_task_error_retry”],
)
```

After registration:

1. an instance of `PluginRegistry` is created;
2. it is added to `self.plugins[trigger_name]`;
3. the list of plugins for the trigger is sorted by `priority`.

If `trigger_names` is `None`, the plugin is considered **global** and
will be called in all triggers of the component.

!!! Note
    In the `QueueTasks()` method, the `add_plugin()` function additionally accepts
    the `component=""` parameter,
    which allows you to add a plugin not to `QueueTasks` itself, but to a specific
    component.

!!! Note
    The workflow passes its plugins to `TaskExecutor` during the task assembly phase.

This allows plugins to influence not only task management but also the process
of their direct execution.

---

## Trigger Types

From an architectural standpoint, triggers are divided into two types.

### Unidirectional Triggers

A unidirectional trigger is used for side effects and does not affect
the subsequent execution of the component’s code.

* The result of the plugin’s execution is ignored;
* The trigger is used for logging, collecting metrics, notifications, and
similar tasks.

### Return Triggers

A return trigger allows plugins to modify data involved in subsequent
execution.

* The plugin’s results can replace the input parameters;
* The set of return values is strictly defined by the trigger contract;
* Most often, the same data that is passed to the trigger is modified.

Which specific parameters can be modified is determined by the description of
the specific trigger.

---

## Trigger Call Parameters

Each call to `_plugin_trigger()` has the following logical parameter structure:

* `<self>` — the component that initiated the trigger call;
* `[additional component]` — optional, if the trigger is logically associated with
another component;
* `**parameters` — a dictionary of parameters passed to plugins.

Additional execution control parameters:

* `return_last: bool | None = None` — return only the last result, if available;
* `safe: bool = True` — if `True`, plugin errors are not ignored;
* `continue_on_fail: bool` — if `True`, execution of other plugins continues
even if an error occurs.

---

## Component Developer Responsibilities

If you are creating your own component and want to support plugins, you must:

* connect the appropriate `PluginMixin`;
* explicitly place `_plugin_trigger()` calls in the appropriate locations within
the logic.

If triggers are not added, the plugin system for the component effectively does
not exist.

Similarly, if you need to completely disable plugins in a component, simply
do not add triggers.

---

## Architectural Invariants

* Plugins belong to components, not to the system as a whole;
* Triggers are called only explicitly;
* Plugins do not violate component contracts;
* The plugin system extends behavior without altering the architectural foundations.

The QTasks plugin system provides controlled architecture extension without hidden
dependencies or implicit side effects.

## Summary

The QTasks plugin system is a
**component-oriented extension mechanism** in which:

* plugins are registered via `add_plugin()`;
* managed via `BasePluginRegistry`;
* stored in `dict[str, list[BasePluginRegistry]]`;
* executed via `_plugin_trigger()`.

This approach allows for safe system extension and the introduction of new
functionality without changing the component architecture.

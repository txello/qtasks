# Components: Plugin System

This page describes the architecture of the QTasks plugin system at the component
level:
how plugins are connected, where exactly they are called, and how they affect the
execution flow.

The plugin system is a built-in mechanism for extending components and does not
exist separately from them.

Each component determines for itself
whether it supports plugins and at which points they can be called.
Each component determines for itself whether it supports plugins and at which
points they can be called.

---

## Plugins as part of a component

Each core QTasks component has its own set of plugins, accessible via `self.plugins`.

Plugins:

* belong to a specific component;
* are called only at explicitly defined points (triggers);
* do not have direct access to the internal state of the component.

Thus, behavior extension is controlled and predictable.

---

## PluginMixin and enabling the plugin system

For a component to use plugins, it must inherit
`AsyncPluginMixin` or `SyncPluginMixin`.

Mixin provides:

* the `_plugin_trigger()` method — the point at which plugins are called;
* the `add_plugin()` method — a mechanism for registering plugins.

Without connecting the appropriate mixin, the plugin system for the component is
considered disabled.

---

## Calling triggers

Plugin triggers are called explicitly within the component logic.

Example of calling an asynchronous trigger:

```python
new_results = await self._plugin_trigger(
    "storage_get_all",
    storage=self,
    results=results,
    return_last=True,
)
```

A trigger is not a "default" event, but an architectural decision made by the
component author.
If the trigger is not called, the plugins are not executed.

---

## Plugin registration

Plugins are added via `add_plugin()`.

```python
self.add_plugin(
    AsyncRetryPlugin(),
    trigger_names=["worker_task_error_retry"],
)
```

`add_plugin()` accepts:

* `plugin` — a plugin instance;
* `trigger_names` — a list of trigger names.

If `trigger_names` is `None`, the plugin is considered **global** and
will be called in all component triggers.

!!! note
    In `QueueTasks()`, the `add_plugin()` method additionally accepts the parameter
    `component=""`,
    which allows you to add a plugin not to `QueueTasks` itself, but to a specific
    component.

!!! note
    Worker passes its plugins to `TaskExecutor` at the task assembly stage.

This allows plugins to influence not only task management, but also the process
of their immediate execution.

---

## Trigger types

From an architectural point of view, triggers are divided into two types.

### Unidirectional triggers

A unidirectional trigger is used for side effects and does not affect
the further execution of the component code.

* The result of plugin execution is ignored.
* The trigger is used for logging, metrics, notifications, and similar tasks.

### Returnable triggers

A returnable trigger allows plugins to change data involved in further
execution.

* plugin results can replace input parameters;
* the set of returnable values is strictly defined by the trigger contract;
* Most often, the same data that is passed to the trigger is changed.

Which parameters can be changed is determined by the description of the specific
trigger.

---

## Trigger call parameters

Each call to `_plugin_trigger()` has the following logical parameter structure:

* `<self>` — the component that initiated the trigger call;
* `[additional component]` — optional, if the trigger is logically related to
another component;
* `**parameters` — a dictionary of parameters passed to plugins.

Additional execution control parameters:

* `return_last: bool | None = None` — return only the last result, if available;
* `safe: bool = True` — if `True`, plugin errors are not ignored;
* `continue_on_fail: bool` — if `True`, other plugins continue to execute
even if an error occurs.

---

## Component developer responsibility

If you are creating your own component and want to support plugins, you must:

* connect the appropriate `PluginMixin`;
* explicitly place `_plugin_trigger()` calls in the necessary places in the logic.

If triggers are not added, the plugin system for the component does not actually
exist.

Similarly, if you want to completely disable plugins in a component, simply
do not add triggers.

---

## Architectural invariants

* Plugins belong to components, not to the system as a whole.
* Triggers are only called explicitly.
* Plugins do not violate component contracts.
* The plugin system extends behavior without changing the architectural foundations.

The QTasks plugin system provides a controlled extension of the architecture
without hidden dependencies or implicit side effects.

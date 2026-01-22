# Configuration

This page describes the architectural model of configuration in QTasks: how it
is structured, how it is distributed among components, and how parameter changes
are automatically reflected throughout the system.

Unlike configurations distributed across components or tied to global variables,
QTasks uses a single, typed configuration source.

---

## Unified configuration scheme

All QTasks configuration is stored in a single dataclass scheme — `QueueConfig`.

A configuration instance:

* is created by default when `QueueTasks` is initialized;
* is available as `app.config`;
* is passed to all components when they are created as a parameter `config=config`;
* is saved by components as `self.config`.

If a component does not receive a configuration explicitly, it must create its own
instance of `QueueConfig`. This allows components to be used in isolation, without
depending on the global state of the application.

---

## Configuration as an architectural contract

`QueueConfig` is not just a set of parameters, but part of the architectural
contract between components.

Through configuration:

* component behavior parameters are set;
* consistency of settings between them is ensured;
* centralized updating of critical parameters is implemented.

Components do not synchronize their settings directly with each other — they rely
exclusively on the configuration.

---

## Change subscription mechanism

One of the key features of `QueueConfig` is support for subscribing to
parameter changes.

Two mechanisms are used for this:

* `subscribe` — registration of change handlers;
* `_notify` — notification of subscribers when a value changes.

Notification occurs automatically when the attribute is changed via `setattr`.

---

## Subscribe function

`subscribe` allows you to subscribe to changes in both existing and dynamically
added configuration parameters.

The subscriber receives the following arguments:

* `config: QueueConfig` — configuration instance;
* `key` — name of the changed parameter;
* `value` — new parameter value.

This allows a component or subsystem to respond to configuration changes
without polling the state.

---

## Automatic propagation of changes

By default, the subscription to configuration changes is registered in `QueueTasks.__init__`.

It is linked to an internal method:

```text
self._update_configs()
```

This method is responsible for synchronizing critical parameters between components.

At the time of writing, it is used, in particular, to update
component loggers:

```text
component.log.update_logger(**kwargs)
```

Thus, a configuration change leads to an immediate update of the state
of components without restarting them.

---

## Dynamic configuration parameters

The `QueueConfig` architecture allows parameters to be added during execution.

Such parameters:

* become part of the overall configuration;
* participate in the subscription mechanism;
* can be used by both components and plugins.

This allows you to extend the configuration without changing the basic schema
and without breaking component compatibility.

---

## Boundaries of responsibility

* `QueueConfig` is responsible for storing and distributing parameters;
* Components are responsible for responding to changes, not coordinating them.
* The configuration does not contain task execution logic.

This separation makes the configuration system predictable, extensible, and
safe for complex scenarios.

---

## Architectural Invariants

* There is a single source of configuration in the system.
* Configuration is typed and serializable.
* Parameter changes are propagated automatically.
* Components are independent of global state.

This configuration model allows QTasks to remain consistent even with
dynamic changes during runtime.

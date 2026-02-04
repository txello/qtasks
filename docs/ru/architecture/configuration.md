# Configuration

This page describes the architectural model of configuration in QTasks: how it is
structured,
how it is distributed among components, and how parameter changes
are automatically reflected throughout the system.

Unlike configurations distributed across components or tied to global
variables, QTasks uses a single, typed configuration source.

---

## Single configuration schema

All QTasks configuration is stored in a single dataclass schema — `QueueConfig`.

A configuration instance:

* is created by default when `QueueTasks` is initialized;
* is accessible as `app.config`;
* is passed to all components when they are created as the `config=config` parameter;
* is saved by components as `self.config`.

If a component does not receive the configuration explicitly, it must create its
own `QueueConfig` instance. This allows components to be used in isolation, without
depending on the global state of the application.

---

## Loading configuration from environment variables

`QueueConfig` supports automatic initialization of parameters from environment variables
(`os.environ`).

Loading is performed **at the `__post_init__` stage** of the `QueueConfig` dataclass
schema, i.e. **immediately after creating a configuration instance**, but
**before passing it to components**.

This allows you to:

* configure QTasks without changing the code;
* use the 12-factor approach;
* safely pass settings through the environment (Docker, CI/CD, systemd);
* override default values at the application launch level.

### How it works

During the execution of `__post_init__`:

1. `QueueConfig` reads values from `os.environ`;
2. matches them with known configuration fields;
3. if a value is found, it overrides the corresponding field;
4. the change goes through the standard `setattr` mechanism.

Since the override is performed through the usual setting of attributes:

* changes participate in the subscription mechanism;
* subscribers receive notifications;
* components automatically receive the current values.

Thus, environment variables are the primary source of values
relative to default values, but do not violate the architectural contract
of the configuration.

### Architectural guarantees

* Loading from `os.environ` occurs once, during configuration initialization.
* Values become part of `QueueConfig`, not external state.
* Further parameter changes work through the standard subscription mechanism.
* Components do not read `os.environ` directly.

This preserves a key invariant of the system:
**components depend only on configuration, not on the execution environment**.

### Practical use cases

* configuring the broker and storage via environment variables;
* managing logging levels;
* enabling and disabling debug modes;
* using different configurations for `dev / stage / prod`;
* running multiple instances of QTasks with different parameters in the same environment.

---

## Configuration as an architectural contract

`QueueConfig` is not just a set of parameters, but part of the architectural
contract between components.

Through configuration:

* component behavior parameters are set;
* consistency of settings between them is ensured;
* centralized updating of critical parameters is implemented.

Components do not synchronize their settings directly with each other — they rely
exclusively on configuration.

---

## Change subscription mechanism

One of the key features of `QueueConfig` is support for subscribing to
parameter changes.

Two mechanisms are used for this:

* `subscribe` — registration of change handlers;
* `_notify` — notification of subscribers when a value changes.

Notification occurs automatically when an attribute is changed via `setattr`.

---

## The subscribe function

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

By default, the subscription to configuration changes is registered in
`QueueTasks.__init__`.

It is bound to an internal method:

```python
self._update_configs()
```

This method is responsible for synchronizing critical parameters between components.

At the time of writing, it is used, in particular, to update component loggers:

```python
component.log.update_logger(**kwargs)
```

Thus, a configuration change leads to an immediate update of the state of
components without restarting them.

---

## Dynamic configuration parameters

The `QueueConfig` architecture allows parameters to be added during runtime.

Such parameters:

* become part of the overall configuration;
* participate in the subscription mechanism;
* can be used by both components and plugins.

This allows you to extend the configuration without changing the basic schema and
without violating component compatibility.

---

## Boundaries of Responsibility

* `QueueConfig` is responsible for storing and distributing parameters;
* components are responsible for responding to changes, not for coordinating them;
* the configuration does not contain task execution logic.

This separation makes the configuration system predictable, extensible, and
safe for complex scenarios.

---

## Architectural Invariants

* There is a single source of configuration in the system;
* Configuration is typed and serializable;
* Parameter changes are propagated automatically;
* Components do not depend on the global state.

This configuration model allows QTasks to remain consistent even with
dynamic changes during operation.
